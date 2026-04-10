# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-013: Plan Consolidation Source traceability."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PR = "Purchase Requisition"
PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PCS = "Plan Consolidation Source"
BCP = "Budget Control Period"


def _minimal_pr(entity: str, currency: str, business_id: str):
	return frappe.get_doc(
		{
			"doctype": PR,
			"name": business_id,
			"title": "PCS test",
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


def _cleanup_pcs13():
	for row in frappe.get_all(PCS, filters={"name": ("like", "_KT_PCS13_%")}, pluck="name") or []:
		frappe.delete_doc(PCS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PR, filters={"name": ("like", "_KT_PCS13_%")}, pluck="name") or []:
		frappe.delete_doc(PR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PPI, filters={"name": ("like", "_KT_PCS13_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PP, filters={"name": ("like", "_KT_PCS13_%")}, pluck="name") or []:
		frappe.delete_doc(PP, row, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PCS13_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": ("like", "_KT_PCS13_%")})


class TestPlanConsolidationSource(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pcs13)
		self.entity = _make_entity("_KT_PCS13_PE").insert()
		self.period = _bcp("_KT_PCS13_BCP", self.entity.name).insert()
		self.plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PCS13_PP",
				"plan_title": "PCS plan",
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
		self.item = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PCS13_PPI",
				"procurement_plan": self.plan.name,
				"title": "Consolidated item",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Consolidated",
				"estimated_amount": 10000,
			}
		).insert(ignore_permissions=True)
		self.pr_a = _minimal_pr(self.entity.name, self.currency, "_KT_PCS13_PRA").insert(
			ignore_permissions=True
		)
		self.pr_b = _minimal_pr(self.entity.name, self.currency, "_KT_PCS13_PRB").insert(
			ignore_permissions=True
		)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pcs13)
		super().tearDown()

	def _row(self, pr_name: str, amount: float, source_type: str = "Requisition"):
		return frappe.get_doc(
			{
				"doctype": PCS,
				"procurement_plan_item": self.item.name,
				"purchase_requisition": pr_name,
				"source_type": source_type,
				"linked_amount": amount,
				"linked_on": "2026-05-01 10:00:00",
				"status": "Active",
			}
		)

	def test_two_sources_same_plan_item(self):
		a = self._row(self.pr_a.name, 3000.0)
		a.insert(ignore_permissions=True)
		b = self._row(self.pr_b.name, 4000.0)
		b.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists(PCS, a.name))
		self.assertTrue(frappe.db.exists(PCS, b.name))
		self.assertEqual(a.currency, self.currency)
		self.assertIn(self.pr_a.name, a.display_label)
		self.assertIn(self.item.name, a.display_label)

	def test_rejects_entity_mismatch(self):
		other = _make_entity("_KT_PCS13_PE2").insert()
		try:
			bad_pr = _minimal_pr(other.name, self.currency, "_KT_PCS13_PRX").insert(
				ignore_permissions=True
			)
			doc = self._row(bad_pr.name, 100.0)
			self.assertRaises(frappe.ValidationError, doc.insert)
		finally:
			if frappe.db.exists(PR, "_KT_PCS13_PRX"):
				frappe.delete_doc(PR, "_KT_PCS13_PRX", force=True, ignore_permissions=True)
			frappe.delete_doc("Procuring Entity", other.name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_rejects_non_positive_amount(self):
		doc = self._row(self.pr_a.name, 0.0)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_manual_source_type_allowed(self):
		doc = self._row(self.pr_a.name, 50.0, source_type="Manual")
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.source_type, "Manual")
