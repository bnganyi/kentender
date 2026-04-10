# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-023: Tender DocType."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
TENDER = "Tender"
BCP = "Budget Control Period"


def _cleanup_tdr023():
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TDR023_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for pin in frappe.get_all(PPI, filters={"name": ("like", "_KT_TDR023_%")}, pluck="name") or []:
		frappe.delete_doc(PPI, pin, force=True, ignore_permissions=True)
	for pp in frappe.get_all(PP, filters={"name": ("like", "_KT_TDR023_%")}, pluck="name") or []:
		frappe.delete_doc(PP, pp, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TDR023_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TDR023_PE"})


class TestTender(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tdr023)
		self.entity = _make_entity("_KT_TDR023_PE").insert()
		self.period = _bcp("_KT_TDR023_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tdr023)
		super().tearDown()

	def _minimal_tender_kwargs(self, business_id: str = "_KT_TDR023_B1", **extra):
		kw = {
			"doctype": TENDER,
			"name": "_KT_TDR023_T1",
			"business_id": business_id,
			"title": "Road maintenance tender",
			"tender_number": "TDR-2026-001",
			"workflow_state": "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"origin_type": "Manual",
			"procuring_entity": self.entity.name,
			"currency": self.currency,
		}
		kw.update(extra)
		return kw

	def test_valid_create(self):
		doc = frappe.get_doc(self._minimal_tender_kwargs())
		doc.insert()
		self.assertEqual(doc.name, "_KT_TDR023_T1")
		self.assertIn("Road maintenance", doc.display_label or "")
		self.assertIn("_KT_TDR023_B1", doc.display_label or "")

	def test_invalid_deadline_sequencing(self):
		doc = frappe.get_doc(
			self._minimal_tender_kwargs(
				business_id="_KT_TDR023_B2",
				name="_KT_TDR023_T2",
				clarification_deadline="2026-06-15 12:00:00",
				submission_deadline="2026-06-10 12:00:00",
			)
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_missing_plan_item_blocked_when_origin_from_plan(self):
		doc = frappe.get_doc(
			self._minimal_tender_kwargs(
				business_id="_KT_TDR023_B3",
				name="_KT_TDR023_T3",
				origin_type="From Plan Item",
			)
		)
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_from_plan_item_with_plan_links_ok(self):
		plan = frappe.get_doc(
			{
				"doctype": PP,
				"name": "_KT_TDR023_PP",
				"plan_title": "TDR023 plan",
				"workflow_state": "Approved",
				"status": "Approved",
				"approval_status": "Approved",
				"procuring_entity": self.entity.name,
				"fiscal_year": "2026-2027",
				"budget_control_period": self.period.name,
				"currency": self.currency,
				"version_no": 1,
				"allow_manual_items": 1,
			}
		).insert(ignore_permissions=True)
		item = frappe.get_doc(
			{
				"doctype": PPI,
				"name": "_KT_TDR023_PPI",
				"procurement_plan": plan.name,
				"title": "Line",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"status": "Approved",
				"origin_type": "Manual",
				"manual_entry_justification": "Test",
				"estimated_amount": 5000,
				"priority_level": "Medium",
			}
		).insert(ignore_permissions=True)
		doc = frappe.get_doc(
			self._minimal_tender_kwargs(
				business_id="_KT_TDR023_B4",
				name="_KT_TDR023_T4",
				origin_type="From Plan Item",
				procurement_plan_item=item.name,
			)
		)
		doc.insert()
		self.assertEqual((doc.procurement_plan or "").strip(), plan.name)
