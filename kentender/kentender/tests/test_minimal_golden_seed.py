# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.uat.minimal_golden.base_ref import load_base_ref
from kentender.uat.minimal_golden.commands import (
	seed_minimal_golden,
	seed_minimal_golden_budget,
	seed_minimal_golden_requisition,
	seed_minimal_golden_strategy,
	seed_minimal_golden_users,
)
from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset
from kentender.uat.minimal_golden.reset import reset_minimal_golden_data
from kentender.uat.minimal_golden.strategy import load_strategy
from kentender.uat.minimal_golden.verify import verify_minimal_golden


class TestMinimalGoldenSeed(FrappeTestCase):
	def tearDown(self):
		try:
			reset_minimal_golden_data(load_minimal_golden_dataset())
		except Exception:
			pass
		frappe.db.commit()
		super().tearDown()

	def test_base_ref_idempotent(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		r1 = load_base_ref(ds)
		r2 = load_base_ref(ds)
		self.assertEqual(r1["procuring_entity"], r2["procuring_entity"])
		self.assertEqual(r1["procuring_entity"], "MOH")
		hod_email = "hod.test@ken-tender.test"
		self.assertTrue(frappe.db.exists("User", hod_email))
		self.assertIn("Head of Department", frappe.get_roles(hod_email))
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": hod_email, "allow": "Procuring Entity", "for_value": "MOH"},
			)
		)

	def test_seed_minimal_golden_strategy_step(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		load_base_ref(ds)
		out = seed_minimal_golden_strategy()
		self.assertEqual(out.get("step"), "strategy")
		self.assertTrue(frappe.db.exists("National Framework", "VF2030"))
		self.assertTrue(frappe.db.exists("Performance Target", "PT-IMG-2026"))

	def test_seed_minimal_golden_budget_step(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		load_base_ref(ds)
		seed_minimal_golden_strategy()
		out = seed_minimal_golden_budget()
		self.assertEqual(out.get("step"), "budget")
		b = out.get("budget") or {}
		self.assertEqual(b.get("budget"), "BUD-MOH-2026-V1")
		self.assertTrue(frappe.db.exists("Budget Control Period", "BCP-2026"))
		bud_doc = frappe.get_doc("Budget", "BUD-MOH-2026-V1")
		self.assertEqual(float(bud_doc.total_allocated_amount), 12000000.0)
		bl = frappe.get_doc("Budget Line", "BL-MOH-IMG-001")
		self.assertEqual(bl.budget, "BUD-MOH-2026-V1")
		self.assertEqual(float(bl.allocated_amount), 12000000.0)
		self.assertEqual(bl.performance_target, "PT-IMG-2026")

	def test_seed_minimal_golden_users_step(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		load_base_ref(ds)
		seed_minimal_golden_strategy()
		seed_minimal_golden_budget()
		out = seed_minimal_golden_users()
		self.assertEqual(out.get("step"), "users")
		self.assertEqual(out.get("procuring_entity"), "MOH")
		self.assertIn("base_ref", out)
		req_email = "requisitioner.test@ken-tender.test"
		self.assertTrue(frappe.db.exists("User", req_email))
		self.assertIn("Requisitioner", frappe.get_roles(req_email))
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": req_email, "allow": "Procuring Entity", "for_value": "MOH"},
			)
		)

	def test_seed_minimal_golden_requisition_step(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		load_base_ref(ds)
		seed_minimal_golden_strategy()
		seed_minimal_golden_budget()
		seed_minimal_golden_users()
		out = seed_minimal_golden_requisition()
		self.assertEqual(out.get("step"), "requisition")
		self.assertEqual(out.get("procuring_entity"), "MOH")
		self.assertIn("base_ref", out)
		v = verify_minimal_golden(ds)
		self.assertTrue(v.get("ok"), msg=v)
		fut = ds.get("future_business_ids") or {}
		for label in ("bid_1", "bid_2"):
			biz = fut.get(label)
			self.assertTrue(
				frappe.db.exists("Bid Submission", {"business_id": biz}),
				msg=f"expected Bid Submission business_id={biz!r}",
			)
		pr_bid = (ds.get("purchase_requisition") or {}).get("name")
		self.assertEqual(out.get("purchase_requisition", {}).get("name"), pr_bid)
		doc = frappe.get_doc("Purchase Requisition", pr_bid)
		self.assertEqual(doc.workflow_state, "Approved")
		self.assertEqual(doc.budget_reservation_status, "Reserved")
		self.assertEqual(doc.requested_amount, 9000000)
		ble = frappe.db.exists("Budget Ledger Entry", {"related_requisition": pr_bid})
		self.assertTrue(bool(ble))

	def test_strategy_chain_links(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		ref = load_base_ref(ds)
		strat = load_strategy(ds, procuring_entity=ref["procuring_entity"])
		nf = frappe.get_doc("National Framework", strat["national_framework"])
		self.assertEqual(nf.framework_code, "VF2030")
		pl = frappe.get_doc("National Pillar", strat["national_pillar"])
		self.assertEqual(pl.national_framework, "VF2030")
		obj = frappe.get_doc("National Objective", strat["national_objective"])
		self.assertEqual(obj.national_pillar, strat["national_pillar"])
		esp = frappe.get_doc("Entity Strategic Plan", strat["entity_strategic_plan"])
		self.assertEqual(esp.procuring_entity, "MOH")
		self.assertEqual(esp.primary_national_framework, "VF2030")
		pg = frappe.get_doc("Strategic Program", strat["strategic_program"])
		self.assertEqual(pg.program_code, "HD")
		self.assertEqual(pg.national_objective, strat["national_objective"])
		sg = frappe.get_doc("Strategic Sub Program", strat["strategic_sub_program"])
		self.assertEqual(sg.sub_program_code, "CRS")
		ind = frappe.get_doc("Output Indicator", strat["output_indicator"])
		self.assertEqual(ind.sub_program, strat["strategic_sub_program"])
		pt = frappe.get_doc("Performance Target", strat["performance_target"])
		self.assertEqual(pt.output_indicator, strat["output_indicator"])
		self.assertEqual(pt.target_value_numeric, 2)

	def test_full_seed_verify_and_idempotent_pr(self):
		ds = load_minimal_golden_dataset()
		reset_minimal_golden_data(ds)
		out1 = seed_minimal_golden(cleanup_mvp=False)
		out2 = seed_minimal_golden(cleanup_mvp=False)
		self.assertEqual(
			out1["purchase_requisition"]["name"],
			out2["purchase_requisition"]["name"],
		)
		pt = out1.get("post_tender") or {}
		if not pt.get("skipped"):
			self.assertEqual(pt.get("contract_status"), "Active")
			self.assertTrue(pt.get("evaluation_session"))
			self.assertTrue(pt.get("procurement_contract"))
		v = verify_minimal_golden(ds)
		self.assertTrue(v.get("ok"), msg=v)
		fut = ds.get("future_business_ids") or {}
		for label in ("bid_1", "bid_2"):
			biz = fut.get(label)
			self.assertTrue(frappe.db.exists("Bid Submission", {"business_id": biz}))
		pr_bid = (ds.get("purchase_requisition") or {}).get("name")
		doc = frappe.get_doc("Purchase Requisition", pr_bid)
		self.assertEqual(doc.workflow_state, "Approved")
		self.assertEqual(doc.budget_reservation_status, "Reserved")
		self.assertEqual(doc.requested_amount, 9000000)
		ble = frappe.db.exists("Budget Ledger Entry", {"related_requisition": pr_bid})
		self.assertTrue(bool(ble))
