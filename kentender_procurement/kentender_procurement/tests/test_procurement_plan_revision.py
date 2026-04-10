# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-019: Procurement Plan Revision + revision lines."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PPR = "Procurement Plan Revision"
PPRL = "Procurement Plan Revision Line"
BCP = "Budget Control Period"


def _cleanup_pprev():
	for row in frappe.get_all(PPR, filters={"revision_business_id": ("like", "_KT_PPREV_%")}, pluck="name") or []:
		frappe.delete_doc(PPR, row, force=True, ignore_permissions=True)
	for pin in frappe.get_all(PPI, filters={"name": ("like", "_KT_PPREV_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_PPREV_%")}, pluck="name") or []:
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_PPREV_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_PPREV_PE"})


class TestProcurementPlanRevision(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pprev)
		self.entity = _make_entity("_KT_PPREV_PE").insert()
		self.period = _bcp("_KT_PPREV_BCP", self.entity.name).insert()
		self.plan_a = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PPREV_PP",
				"plan_title": "Revision plan A",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
			}
		).insert(ignore_permissions=True)
		self.plan_b = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_PPREV_PP2",
				"plan_title": "Revision plan B",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
			}
		).insert(ignore_permissions=True)
		self.item_a = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPREV_IA",
				"procurement_plan": self.plan_a.name,
				"title": "Item A",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Manual",
				"manual_entry_justification": "Test item",
				"estimated_amount": 5000,
				"priority_level": "Medium",
			}
		).insert(ignore_permissions=True)
		self.item_b = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_PPREV_IB",
				"procurement_plan": self.plan_b.name,
				"title": "Item B",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Draft",
				"origin_type": "Manual",
				"manual_entry_justification": "Test item",
				"estimated_amount": 3000,
				"priority_level": "Medium",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pprev)
		super().tearDown()

	def _minimal_revision(self, plan_name, line_item: str, **extra):
		row = {
			"doctype": PPR,
			"revision_business_id": "_KT_PPREV_REV01",
			"source_procurement_plan": plan_name,
			"revision_type": "Budget",
			"revision_reason": "Budget alignment",
			"requested_by": frappe.session.user,
			"requested_on": "2026-04-10 09:00:00",
			"status": "Draft",
			"revision_lines": [
				{
					"doctype": PPRL,
					"affected_plan_item": line_item,
					"action_type": "Update",
					"change_notes": "Test line",
					"change_amount": 250,
				}
			],
		}
		row.update(extra)
		return frappe.get_doc(row)

	def test_valid_create_with_line_and_display_label(self):
		doc = self._minimal_revision(self.plan_a.name, self.item_a.name)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertEqual(doc.source_procurement_plan, self.plan_a.name)
		self.assertEqual(len(doc.revision_lines), 1)
		self.assertIn("_KT_PPREV_REV01", doc.display_label or "")
		self.assertIn("Budget", doc.display_label or "")

	def test_rejects_line_from_different_plan(self):
		doc = self._minimal_revision(self.plan_a.name, self.item_b.name)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_approved_requires_approver_fields(self):
		doc = self._minimal_revision(
			self.plan_a.name,
			self.item_a.name,
			status="Approved",
			revision_business_id="_KT_PPREV_REV02",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_approved_ok_with_approver(self):
		doc = self._minimal_revision(
			self.plan_a.name,
			self.item_a.name,
			revision_business_id="_KT_PPREV_REV03",
			status="Approved",
			approved_by=frappe.session.user,
			approved_on="2026-04-10 10:00:00",
		)
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.status, "Approved")
