# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-029: Tender Clarification."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TCL = "Tender Clarification"
BCP = "Budget Control Period"


def _cleanup_tcl029():
	for row in frappe.get_all(TCL, filters={"tender": ("like", "_KT_TCL029_%")}, pluck="name") or []:
		frappe.delete_doc(TCL, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TCL029_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_TCL029_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TCL029_PE"})


class TestTenderClarification(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tcl029)
		self.entity = _make_entity("_KT_TCL029_PE").insert()
		self.period = _bcp("_KT_TCL029_BCP", self.entity.name).insert()
		self.tender = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_TCL029_T1",
				"business_id": "_KT_TCL029_B1",
				"title": "TCL tender",
				"tender_number": "TCL-029-001",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tcl029)
		super().tearDown()

	def test_valid_create(self):
		doc = frappe.get_doc(
			{
				"doctype": TCL,
				"business_id": "_KT_TCL029_CL1",
				"tender": self.tender.name,
				"supplier": "SUP-001",
				"question_submitted_by": frappe.session.user,
				"question_datetime": "2026-04-10 09:00:00",
				"question_text": "What is the delivery period?",
				"status": "Pending Response",
				"visibility_mode": "Internal",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertEqual(doc.tender, self.tender.name)
		self.assertEqual(doc.business_id, "_KT_TCL029_CL1")
		self.assertIn("_KT_TCL029_CL1", doc.display_label or "")
		self.assertIn("delivery", (doc.display_label or "").lower())

	def test_answered_requires_response_fields(self):
		doc = frappe.get_doc(
			{
				"doctype": TCL,
				"business_id": "_KT_TCL029_CL2",
				"tender": self.tender.name,
				"supplier": "SUP-002",
				"question_submitted_by": frappe.session.user,
				"question_datetime": "2026-04-10 10:00:00",
				"question_text": "Clarification on specs?",
				"status": "Answered",
				"visibility_mode": "Bidders Only",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
