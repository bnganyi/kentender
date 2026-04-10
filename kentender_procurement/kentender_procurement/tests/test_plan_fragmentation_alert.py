# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-016: Plan Fragmentation Alert."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PFRA = "Plan Fragmentation Alert"
BCP = "Budget Control Period"


def _cleanup_pfra():
	for name in frappe.get_all(
		PFRA, filters={"procurement_plan": ("like", "_KT_PFRA_%")}, pluck="name"
	) or []:
		frappe.delete_doc(PFRA, name, force=True, ignore_permissions=True)
	for row in frappe.get_all(PPI, filters={"name": ("like", "_KT_PFRA_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PP, filters={"name": ("like", "_KT_PFRA_%")}, pluck="name") or []:
		frappe.delete_doc(PP, row, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PFRA_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PFRA_PE"})


class TestPlanFragmentationAlert(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pfra)
		self.entity = _make_entity("_KT_PFRA_PE").insert()
		self.period = _bcp("_KT_PFRA_BCP", self.entity.name).insert()
		self.plan_a = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PFRA_PPA",
				"plan_title": "Fragmentation plan A",
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
		self.plan_b = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PFRA_PPB",
				"plan_title": "Fragmentation plan B",
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
		self.item_a = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PFRA_PIA",
				"procurement_plan": self.plan_a.name,
				"title": "Item on plan A",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Requisition Derived",
				"estimated_amount": 1000,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pfra)
		super().tearDown()

	def _minimal_alert_kwargs(self, **extra):
		row = {
			"doctype": PFRA,
			"business_id": "FRA-UNIT-001",
			"procurement_plan": self.plan_a.name,
			"alert_type": "Similar Demand Split",
			"severity": "Medium",
			"risk_score": 0.42,
			"rule_trigger_summary": "Two items overlap category and schedule (placeholder).",
			"status": "Open",
			"raised_on": "2026-05-01 09:00:00",
			"raised_by_system": 1,
		}
		row.update(extra)
		return row

	def test_valid_create_with_related_item(self):
		doc = frappe.get_doc(
			self._minimal_alert_kwargs(related_plan_item=self.item_a.name)
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertEqual(doc.procurement_plan, self.plan_a.name)
		self.assertEqual(doc.related_plan_item, self.item_a.name)
		self.assertIn("FRA-UNIT-001", doc.display_label or "")
		self.assertIn("Similar Demand Split", doc.display_label or "")

	def test_rejects_plan_item_from_other_plan(self):
		doc = frappe.get_doc(
			self._minimal_alert_kwargs(
				procurement_plan=self.plan_b.name,
				business_id="FRA-UNIT-BAD",
				related_plan_item=self.item_a.name,
			)
		)
		self.assertRaises(frappe.ValidationError, doc.insert)
