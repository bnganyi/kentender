# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-018: requisition-to-plan consolidation service."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.procurement_plan_totals import reconcile_plan_item_consolidation_sources
from kentender_procurement.services.requisition_plan_consolidation import consolidate_requisitions_into_plan
from kentender_procurement.services.requisition_planning_derivation import STATUS_LINKED

PR = "Purchase Requisition"
RPL = "Requisition Planning Link"
PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PCS = "Plan Consolidation Source"
BCP = "Budget Control Period"


def _approved_pr(entity: str, currency: str, business_id: str, qty: float = 10.0, unit: float = 10.0):
	return frappe.get_doc(
		{
			"doctype": PR,
			"name": business_id,
			"title": "RPC18 test",
			"requisition_type": "Goods",
			"status": "Draft",
			"workflow_state": "Approved",
			"approval_status": "Approved",
			"procuring_entity": entity,
			"fiscal_year": "2026-2027",
			"currency": currency,
			"request_date": "2026-04-01",
			"priority_level": "Medium",
			"budget_reservation_status": "None",
			"planning_status": "Unplanned",
			"items": [
				{
					"doctype": "Purchase Requisition Item",
					"item_description": "Line",
					"quantity": qty,
					"estimated_unit_cost": unit,
				}
			],
		}
	).insert(ignore_permissions=True)


def _cleanup_rpc18():
	for pn in frappe.get_all(PP, filters={"name": ("like", "_KT_RPC18_%")}, pluck="name") or []:
		for lnk in frappe.get_all(RPL, filters={"procurement_plan": pn}, pluck="name") or []:
			frappe.delete_doc(RPL, lnk, force=True, ignore_permissions=True)
		for pin in frappe.get_all(PPI, filters={"procurement_plan": pn}, pluck="name") or []:
			for src in frappe.get_all(PCS, filters={"procurement_plan_item": pin}, pluck="name") or []:
				frappe.delete_doc(PCS, src, force=True, ignore_permissions=True)
			frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
		frappe.delete_doc(PP, pn, force=True, ignore_permissions=True)
	for prn in frappe.get_all(PR, filters={"name": ("like", "_KT_RPC18_%")}, pluck="name") or []:
		frappe.db.delete(RPL, {"purchase_requisition": prn})
		frappe.delete_doc(PR, prn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_RPC18_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_RPC18_PE"})


class TestRequisitionPlanConsolidation(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_rpc18)
		self.entity = _make_entity("_KT_RPC18_PE").insert()
		self.period = _bcp("_KT_RPC18_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_RPC18_PP",
				"plan_title": "RPC18 plan",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_rpc18)
		super().tearDown()

	def test_separate_mode_one_pr_creates_linked_planning(self):
		pr = _approved_pr(self.entity.name, self.currency, "_KT_RPC18_PR1")
		self.assertEqual(flt(pr.requested_amount), 100.0)

		out = consolidate_requisitions_into_plan(
			self.plan.name,
			[{"purchase_requisition": pr.name}],
			mode="separate",
		)
		self.assertFalse(out.get("dry_run"))
		self.assertEqual(len(out["plan_items_created"]), 1)
		self.assertEqual(len(out["consolidation_source_names"]), 1)
		self.assertEqual(len(out["planning_link_names"]), 1)

		ppi_name = out["plan_items_created"][0]
		ppi = frappe.get_doc(PPI, ppi_name)
		self.assertEqual(ppi.origin_type, "Requisition Derived")
		self.assertEqual(flt(ppi.estimated_amount), 100.0)

		rec = reconcile_plan_item_consolidation_sources(ppi_name)
		self.assertTrue(rec["match"])

		pr.reload()
		self.assertEqual(pr.planning_status, STATUS_LINKED)

	def test_consolidated_mode_two_prs_single_item(self):
		pr_a = _approved_pr(self.entity.name, self.currency, "_KT_RPC18_PRA")
		pr_b = _approved_pr(self.entity.name, self.currency, "_KT_RPC18_PRB")

		out = consolidate_requisitions_into_plan(
			self.plan.name,
			[
				{"purchase_requisition": pr_a.name},
				{"purchase_requisition": pr_b.name},
			],
			mode="consolidated",
		)
		self.assertEqual(len(out["plan_items_created"]), 1)
		self.assertEqual(len(out["consolidation_source_names"]), 2)
		self.assertEqual(len(out["planning_link_names"]), 2)

		ppi_name = out["plan_items_created"][0]
		ppi = frappe.get_doc(PPI, ppi_name)
		self.assertEqual(ppi.origin_type, "Consolidated")
		self.assertEqual(flt(ppi.estimated_amount), 200.0)
		self.assertTrue(reconcile_plan_item_consolidation_sources(ppi_name)["match"])

	def test_over_planning_blocked_batch_same_pr(self):
		pr = _approved_pr(self.entity.name, self.currency, "_KT_RPC18_PRO")

		with self.assertRaises(frappe.ValidationError):
			consolidate_requisitions_into_plan(
				self.plan.name,
				[
					{"purchase_requisition": pr.name, "linked_amount": 60.0},
					{"purchase_requisition": pr.name, "linked_amount": 50.0},
				],
				mode="separate",
			)

	def test_over_planning_blocked_second_call(self):
		pr = _approved_pr(self.entity.name, self.currency, "_KT_RPC18_PR2")

		consolidate_requisitions_into_plan(
			self.plan.name,
			[{"purchase_requisition": pr.name, "linked_amount": 80.0}],
			mode="separate",
		)
		with self.assertRaises(frappe.ValidationError):
			consolidate_requisitions_into_plan(
				self.plan.name,
				[{"purchase_requisition": pr.name, "linked_amount": 30.0}],
				mode="separate",
			)

	def test_dry_run_does_not_insert(self):
		pr = _approved_pr(self.entity.name, self.currency, "_KT_RPC18_PRD")
		out = consolidate_requisitions_into_plan(
			self.plan.name,
			[{"purchase_requisition": pr.name}],
			mode="separate",
			dry_run=True,
		)
		self.assertTrue(out.get("dry_run"))
		self.assertFalse(frappe.get_all(RPL, filters={"purchase_requisition": pr.name}))
