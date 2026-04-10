# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-014: Procurement Plan totals and consolidation reconciliation."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender_procurement.services.procurement_plan_totals import (
	compute_procurement_plan_totals,
	list_consolidation_mismatches_for_plan,
	reconcile_plan_item_consolidation_sources,
)

PR = "Purchase Requisition"
PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PCS = "Plan Consolidation Source"
RPL = "Requisition Planning Link"
BCP = "Budget Control Period"


def _minimal_pr(entity: str, currency: str, business_id: str):
	return frappe.get_doc(
		{
			"doctype": PR,
			"name": business_id,
			"title": "PPT14 test",
			"requisition_type": "Goods",
			"status": "Draft",
			"workflow_state": "Draft",
			"approval_status": "Draft",
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
					"quantity": 10,
					"estimated_unit_cost": 10,
				}
			],
		}
	)


def _cleanup_ppt14():
	for pr in frappe.get_all(PR, filters={"name": ("like", "_KT_PPT14_%")}, pluck="name") or []:
		frappe.db.delete(RPL, {"purchase_requisition": pr})
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_PPT14_%")}, pluck="name") or []:
		frappe.db.delete(RPL, {"procurement_plan": pp})
	for pii in frappe.get_all(PPI, filters={"name": ("like", "_KT_PPT14_%")}, pluck="name") or []:
		frappe.db.delete(RPL, {"procurement_plan_item": pii})
		frappe.db.delete(PCS, {"procurement_plan_item": pii})
	for row in frappe.get_all(PR, filters={"name": ("like", "_KT_PPT14_%")}, pluck="name") or []:
		frappe.delete_doc(PR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PPI, filters={"name": ("like", "_KT_PPT14_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PP, filters={"name": ("like", "_KT_PPT14_%")}, pluck="name") or []:
		frappe.delete_doc(PP, row, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PPT14_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PPT14_%")})


class TestProcurementPlanTotals(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_ppt14)
		self.entity = _make_entity("_KT_PPT14_PE").insert()
		self.period = _bcp("_KT_PPT14_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PPT14_PP",
				"plan_title": "Totals test plan",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
				"allow_consolidation": 1,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_ppt14)
		super().tearDown()

	def test_compute_totals_and_counts(self):
		frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPT14_M",
				"procurement_plan": self.plan.name,
				"title": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Manual",
				"manual_entry_justification": "Test",
				"estimated_amount": 1000,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPT14_C",
				"procurement_plan": self.plan.name,
				"title": "Consolidated",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Consolidated",
				"estimated_amount": 2000,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPT14_R",
				"procurement_plan": self.plan.name,
				"title": "Req derived",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Requisition Derived",
				"estimated_amount": 500,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPT14_X",
				"procurement_plan": self.plan.name,
				"title": "Cancelled skip",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Cancelled",
				"origin_type": "Requisition Derived",
				"estimated_amount": 99999,
			}
		).insert(ignore_permissions=True)

		t = compute_procurement_plan_totals(self.plan.name)
		self.assertEqual(t["total_item_count"], 3)
		self.assertAlmostEqual(flt(t["total_estimated_amount"]), 3500.0)
		self.assertEqual(t["manual_item_count"], 1)
		self.assertEqual(t["consolidated_item_count"], 1)
		self.assertEqual(t["planned_requisition_count"], 0)

		self.plan.reload()
		self.assertAlmostEqual(flt(self.plan.total_estimated_amount), 3500.0)
		self.assertEqual(self.plan.total_item_count, 3)

	def test_planned_requisition_distinct_count(self):
		item = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPT14_PI1",
				"procurement_plan": self.plan.name,
				"title": "Item for RPL",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Requisition Derived",
				"estimated_amount": 100,
			}
		).insert(ignore_permissions=True)
		pr_a = _minimal_pr(self.entity.name, self.currency, "_KT_PPT14_PRA").insert(ignore_permissions=True)
		pr_b = _minimal_pr(self.entity.name, self.currency, "_KT_PPT14_PRB").insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": pr_a.name,
				"procurement_plan": self.plan.name,
				"linked_amount": 10,
				"linked_on": "2026-05-01 10:00:00",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": RPL,
				"purchase_requisition": pr_b.name,
				"procurement_plan_item": item.name,
				"linked_amount": 20,
				"linked_on": "2026-05-01 11:00:00",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		self.plan.reload()
		self.assertEqual(self.plan.planned_requisition_count, 2)
		self.assertEqual(compute_procurement_plan_totals(self.plan.name)["planned_requisition_count"], 2)

	def test_reconcile_consolidation_sources_match_and_mismatch(self):
		item = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPT14_CON",
				"procurement_plan": self.plan.name,
				"title": "Con item",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Consolidated",
				"estimated_amount": 3000,
			}
		).insert(ignore_permissions=True)
		pr_a = _minimal_pr(self.entity.name, self.currency, "_KT_PPT14_PRC").insert(ignore_permissions=True)
		pr_b = _minimal_pr(self.entity.name, self.currency, "_KT_PPT14_PRD").insert(ignore_permissions=True)

		r0 = reconcile_plan_item_consolidation_sources(item.name)
		self.assertTrue(r0["match"])
		self.assertEqual(r0["sources_count"], 0)

		frappe.get_doc(
			{
				"doctype": PCS,
				"procurement_plan_item": item.name,
				"purchase_requisition": pr_a.name,
				"source_type": "Requisition",
				"linked_amount": 1000,
				"linked_on": "2026-05-01 10:00:00",
				"status": "Active",
			}
		).insert(ignore_permissions=True)
		pc2 = frappe.get_doc(
			{
				"doctype": PCS,
				"procurement_plan_item": item.name,
				"purchase_requisition": pr_b.name,
				"source_type": "Requisition",
				"linked_amount": 2000,
				"linked_on": "2026-05-01 11:00:00",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		r1 = reconcile_plan_item_consolidation_sources(item.name)
		self.assertTrue(r1["match"])
		self.assertEqual(r1["sources_count"], 2)
		self.assertAlmostEqual(flt(r1["pcs_total"]), 3000.0)

		doc2 = frappe.get_doc(PCS, pc2.name)
		doc2.linked_amount = 1000
		doc2.save(ignore_permissions=True)

		r2 = reconcile_plan_item_consolidation_sources(item.name)
		self.assertFalse(r2["match"])
		mis = list_consolidation_mismatches_for_plan(self.plan.name)
		self.assertEqual(len(mis), 1)
		self.assertEqual(mis[0]["procurement_plan_item"], item.name)
