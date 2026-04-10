# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.uat.mvp.commands import seed_uat_mvp
from kentender.uat.mvp.dataset import load_mvp_dataset, mvp_password
from kentender.uat.mvp.reset import reset_mvp_seed_data
from kentender.uat.mvp.users import seed_mvp_users
from kentender.uat.mvp.verify import verify_uat_mvp
from kentender_procurement.services.requisition_workflow_actions import (
	RAR_DOCTYPE,
	approve_requisition_finance,
	approve_requisition_hod,
	approve_requisition_step,
	submit_requisition,
)


PR = "Purchase Requisition"
BLE = "Budget Ledger Entry"


class TestUatMvpSeed(FrappeTestCase):
	def tearDown(self):
		try:
			reset_mvp_seed_data(load_mvp_dataset())
		except Exception:
			pass
		frappe.db.commit()
		super().tearDown()

	def test_mvp_seed_idempotent_chain(self):
		ds = load_mvp_dataset()
		reset_mvp_seed_data(ds)
		out1 = seed_uat_mvp()
		out2 = seed_uat_mvp()
		self.assertEqual(
			out1["sp1"]["approved_business_id"],
			out2["sp1"]["approved_business_id"],
		)
		v = verify_uat_mvp(ds)
		self.assertTrue(v.get("ok"), msg=v)

	def test_mvp_users_and_roles(self):
		ds = load_mvp_dataset()
		pwd = mvp_password(ds)
		seed_mvp_users(ds, pwd)
		for row in (ds.get("users") or {}).get("internal") or []:
			self.assertTrue(frappe.db.exists("User", row["email"]))
			roles = frappe.get_roles(row["email"])
			self.assertIn(row["role"], roles)

	def test_sp1_states_and_budget_reservation(self):
		ds = load_mvp_dataset()
		reset_mvp_seed_data(ds)
		seed_uat_mvp()

		draft_id = (ds.get("purchase_requisitions") or {}).get("draft", {}).get("name")
		d = frappe.get_doc(PR, draft_id)
		self.assertEqual(d.workflow_state, "Draft")

		ret_id = (ds.get("purchase_requisitions") or {}).get("returned", {}).get("name")
		r = frappe.get_doc(PR, ret_id)
		self.assertEqual(r.workflow_state, "Returned for Amendment")
		rars = frappe.get_all(RAR_DOCTYPE, filters={"purchase_requisition": ret_id, "action_type": "Return for Revision"})
		self.assertEqual(len(rars), 1)

		app_id = (ds.get("purchase_requisitions") or {}).get("approved", {}).get("name")
		a = frappe.get_doc(PR, app_id)
		self.assertEqual(a.workflow_state, "Approved")
		self.assertEqual(a.budget_reservation_status, "Reserved")
		bles = frappe.get_all(BLE, filters={"related_requisition": app_id}, pluck="name")
		self.assertTrue(len(bles) >= 1)

	def test_self_approval_blocked_mvp_users(self):
		ds = load_mvp_dataset()
		reset_mvp_seed_data(ds)
		out = seed_uat_mvp()
		ref = out["base_ref"]
		strat = out["base_strat"]
		bud = out["base_bud"]
		req = next(r["email"] for r in ds["users"]["internal"] if r["key"] == "requisitioner")
		dept = ref["departments"][0]
		doc = frappe.get_doc(
			{
				"doctype": PR,
				"name": "UAT-MVP-PR-SELFTEST",
				"title": "Self approval test",
				"requisition_type": "Goods",
				"status": "Draft",
				"workflow_state": "Draft",
				"approval_status": "Draft",
				"procuring_entity": ref["procuring_entity"],
				"requesting_department": dept,
				"fiscal_year": ds["fiscal_year"],
				"currency": ds["currency_code"],
				"request_date": "2026-04-01",
				"priority_level": "Medium",
				"budget_reservation_status": "None",
				"planning_status": "Unplanned",
				"entity_strategic_plan": strat["entity_strategic_plan"],
				"program": strat["strategic_program"],
				"sub_program": strat["strategic_sub_program"],
				"output_indicator": strat["output_indicator"],
				"performance_target": strat["performance_target"],
				"national_objective": strat["national_objective"],
				"budget_control_period": bud["budget_control_period"],
				"budget": bud["budget"],
				"budget_line": bud["budget_line_healthy"],
				"funding_source": ref["funding_source"],
				"items": [
					{
						"doctype": "Purchase Requisition Item",
						"item_description": "x",
						"quantity": 1,
						"estimated_unit_cost": 100,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		doc.requested_by_user = req
		doc.save(ignore_permissions=True)
		submit_requisition(doc.name, user=req)
		self.assertRaises(
			frappe.ValidationError,
			lambda: approve_requisition_step(
				doc.name,
				workflow_step="Final",
				decision_level="L1",
				user=req,
			),
		)
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": doc.name})
		frappe.delete_doc(PR, doc.name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_insufficient_funds_blocks_approve(self):
		ds = load_mvp_dataset()
		reset_mvp_seed_data(ds)
		out = seed_uat_mvp()
		ref = out["base_ref"]
		strat = out["base_strat"]
		bud = out["base_bud"]
		ent = ref["procuring_entity"]
		tight_line = bud["budget_line_constrained"]
		req = next(r["email"] for r in ds["users"]["internal"] if r["key"] == "requisitioner")
		hod = next(r["email"] for r in ds["users"]["internal"] if r["key"] == "hod")
		fin = next(r["email"] for r in ds["users"]["internal"] if r["key"] == "finance")
		dept = ref["departments"][0]
		doc = frappe.get_doc(
			{
				"doctype": PR,
				"name": "UAT-MVP-PR-BAD-BUD",
				"title": "Over line",
				"requisition_type": "Goods",
				"status": "Draft",
				"workflow_state": "Draft",
				"approval_status": "Draft",
				"procuring_entity": ent,
				"requesting_department": dept,
				"fiscal_year": ds["fiscal_year"],
				"currency": ds["currency_code"],
				"request_date": "2026-04-01",
				"priority_level": "Medium",
				"budget_reservation_status": "None",
				"planning_status": "Unplanned",
				"entity_strategic_plan": strat["entity_strategic_plan"],
				"program": strat["strategic_program"],
				"sub_program": strat["strategic_sub_program"],
				"output_indicator": strat["output_indicator"],
				"performance_target": strat["performance_target"],
				"national_objective": strat["national_objective"],
				"budget_control_period": bud["budget_control_period"],
				"budget": bud["budget"],
				"budget_line": tight_line,
				"funding_source": ref["funding_source"],
				"items": [
					{
						"doctype": "Purchase Requisition Item",
						"item_description": "x",
						"quantity": 10,
						"estimated_unit_cost": 500,
					}
				],
			}
		)
		doc.insert(ignore_permissions=True)
		doc.requested_by_user = req
		doc.save(ignore_permissions=True)
		submit_requisition(doc.name, user=req)
		approve_requisition_hod(doc.name, user=hod)
		self.assertRaises(
			frappe.ValidationError,
			lambda: approve_requisition_finance(doc.name, user=fin),
		)
		frappe.db.delete(RAR_DOCTYPE, {"purchase_requisition": doc.name})
		frappe.delete_doc(PR, doc.name, force=True, ignore_permissions=True)
		frappe.db.commit()
