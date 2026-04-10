# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-033: tender workflow actions."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.tender_workflow_actions import (
	approve_tender,
	cancel_tender,
	publish_tender,
	submit_tender_for_review,
	withdraw_tender,
)

TENDER = "Tender"
TAR = "Tender Approval Record"
TCR = "Tender Criteria"
TDOC = "Tender Document"
BCP = "Budget Control Period"
FILE = "File"
DTR = "Document Type Registry"


def _cleanup_twfa():
	for row in frappe.get_all(TAR, filters={"tender": ("like", "_KT_TWFA_%")}, pluck="name") or []:
		frappe.db.delete(TAR, {"name": row})
	for dt in (TCR, TDOC):
		for row in frappe.get_all(dt, filters={"tender": ("like", "_KT_TWFA_%")}, pluck="name") or []:
			frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TWFA_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for fn in (
		frappe.get_all(
			FILE,
			filters={"attached_to_doctype": TENDER, "attached_to_name": ("like", "_KT_TWFA_%")},
			pluck="name",
		)
		or []
	):
		frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
	frappe.db.delete(DTR, {"document_type_code": ("like", "_KT_TWFA_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_TWFA_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TWFA_PE"})


class TestTenderWorkflowActions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_twfa)
		self.entity = _make_entity("_KT_TWFA_PE").insert()
		self.period = _bcp("_KT_TWFA_BCP", self.entity.name).insert()
		self.dtr = frappe.get_doc(
			{
				"doctype": DTR,
				"document_type_code": "_KT_TWFA_DT1",
				"document_type_name": "TWFA doc type",
			}
		)
		self.dtr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_twfa)
		super().tearDown()

	def _base_tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "TWFA tender",
			"tender_number": f"{name}-TN",
			"workflow_state": "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"origin_type": "Manual",
			"procuring_entity": self.entity.name,
			"currency": self.currency,
			"supplier_eligibility_rule_mode": "Open",
			"procurement_method": "Open National Tender",
			"publication_datetime": "2026-05-01 09:00:00",
			"clarification_deadline": "2026-05-10 17:00:00",
			"submission_deadline": "2026-06-01 17:00:00",
			"opening_datetime": "2026-06-02 10:00:00",
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _criteria(self, tender_name: str, code: str):
		return frappe.get_doc(
			{
				"doctype": TCR,
				"tender": tender_name,
				"criteria_type": "Technical",
				"criteria_code": code,
				"criteria_title": "Criterion",
				"score_type": "Numeric",
				"max_score": 100,
				"weight_percentage": 25,
				"minimum_pass_mark": 40,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _document(self, tender_name: str):
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "twfa.txt",
				"content": b"doc",
				"attached_to_doctype": TENDER,
				"attached_to_name": tender_name,
			}
		)
		fd.insert(ignore_permissions=True)
		return frappe.get_doc(
			{
				"doctype": TDOC,
				"tender": tender_name,
				"document_type": self.dtr.name,
				"document_title": "Spec",
				"document_version_no": 1,
				"attached_file": fd.name,
				"status": "Draft",
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)

	def test_submit_approve_publish_happy_path(self):
		t = self._base_tender("_KT_TWFA_T1")
		self._criteria(t.name, "C1")
		self._document(t.name)
		submit_tender_for_review(t.name, user="Administrator", comments="go")
		t.reload()
		self.assertEqual(t.workflow_state, "Submitted")
		approve_tender(t.name, user="Administrator")
		t.reload()
		self.assertEqual(t.workflow_state, "Approved")
		publish_tender(t.name, user="Administrator")
		t.reload()
		self.assertEqual(t.workflow_state, "Published")
		self.assertEqual(t.submission_status, "Open")
		self.assertEqual(t.public_disclosure_stage, "Full Tender")
		n_tar = frappe.db.count(TAR, {"tender": t.name})
		self.assertGreaterEqual(n_tar, 3)

	def test_publish_blocked_when_not_ready(self):
		t = self._base_tender("_KT_TWFA_T2")
		self._criteria(t.name, "C2")
		self._document(t.name)
		submit_tender_for_review(t.name)
		approve_tender(t.name)
		frappe.db.delete(TCR, {"tender": t.name})
		self.assertRaises(frappe.ValidationError, publish_tender, t.name)

	def test_direct_publish_save_blocked(self):
		t = self._base_tender("_KT_TWFA_T3")
		self._criteria(t.name, "C3")
		self._document(t.name)
		submit_tender_for_review(t.name)
		approve_tender(t.name)
		t.reload()
		t.workflow_state = "Published"
		t.status = "Active"
		self.assertRaises(frappe.ValidationError, t.save)

	def test_cancel_draft(self):
		t = self._base_tender("_KT_TWFA_T4")
		cancel_tender(t.name, reason="No longer needed", user="Administrator")
		t.reload()
		self.assertEqual(t.workflow_state, "Cancelled")
		self.assertTrue(t.cancellation_reason)

	def test_withdraw_after_publish(self):
		t = self._base_tender("_KT_TWFA_T5")
		self._criteria(t.name, "C5")
		self._document(t.name)
		submit_tender_for_review(t.name)
		approve_tender(t.name)
		publish_tender(t.name)
		t.reload()
		withdraw_tender(t.name, reason="Market withdrawal", user="Administrator")
		t.reload()
		self.assertEqual(t.workflow_state, "Cancelled")
		self.assertEqual(t.submission_status, "Closed")
		self.assertTrue(t.withdrawal_reason)
