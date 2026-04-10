# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-034: clarification and amendment action services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.tender_clarification_amendment_actions import (
	create_tender_amendment,
	publish_clarification_response,
	publish_tender_amendment,
	submit_clarification,
)
from kentender_procurement.services.tender_workflow_actions import (
	approve_tender,
	publish_tender,
	submit_tender_for_review,
)

TENDER = "Tender"
TCL = "Tender Clarification"
TAM = "Tender Amendment"
TAR = "Tender Approval Record"
TCR = "Tender Criteria"
TDOC = "Tender Document"
BCP = "Budget Control Period"
FILE = "File"
DTR = "Document Type Registry"


def _cleanup_tcam034():
	for row in frappe.get_all(TAM, filters={"tender": ("like", "_KT_TCAM034_%")}, pluck="name") or []:
		frappe.delete_doc(TAM, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TCL, filters={"tender": ("like", "_KT_TCAM034_%")}, pluck="name") or []:
		frappe.delete_doc(TCL, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TAR, filters={"tender": ("like", "_KT_TCAM034_%")}, pluck="name") or []:
		frappe.db.delete(TAR, {"name": row})
	for dt in (TCR, TDOC):
		for row in frappe.get_all(dt, filters={"tender": ("like", "_KT_TCAM034_%")}, pluck="name") or []:
			frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TCAM034_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for fn in (
		frappe.get_all(
			FILE,
			filters={"attached_to_doctype": TENDER, "attached_to_name": ("like", "_KT_TCAM034_%")},
			pluck="name",
		)
		or []
	):
		frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
	frappe.db.delete(DTR, {"document_type_code": ("like", "_KT_TCAM034_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_TCAM034_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TCAM034_PE"})


class TestTenderClarificationAmendmentActions(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tcam034)
		self.entity = _make_entity("_KT_TCAM034_PE").insert()
		self.period = _bcp("_KT_TCAM034_BCP", self.entity.name).insert()
		self.dtr = frappe.get_doc(
			{
				"doctype": DTR,
				"document_type_code": "_KT_TCAM034_DT1",
				"document_type_name": "TCAM034 doc type",
			}
		)
		self.dtr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tcam034)
		super().tearDown()

	def _base_tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "TCAM034 tender",
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
				"file_name": "tcam034.txt",
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

	def _published_tender(self, name: str):
		t = self._base_tender(name)
		self._criteria(t.name, "C1")
		self._document(t.name)
		submit_tender_for_review(t.name, user="Administrator")
		approve_tender(t.name, user="Administrator")
		publish_tender(t.name, user="Administrator")
		t.reload()
		return t

	def test_submit_clarification_increments_count(self):
		t = self._published_tender("_KT_TCAM034_T1")
		frappe.db.set_value(TENDER, t.name, "clarification_count", 0, update_modified=False)
		cl = frappe.get_doc(
			{
				"doctype": TCL,
				"business_id": "_KT_TCAM034_CL1",
				"tender": t.name,
				"supplier": "SUP-1",
				"question_submitted_by": frappe.session.user,
				"question_datetime": "2026-05-02 10:00:00",
				"question_text": "What is the warranty?",
				"status": "Draft",
				"visibility_mode": "Internal",
			}
		)
		cl.insert(ignore_permissions=True)
		submit_clarification(cl.name, user="Administrator")
		cl.reload()
		t.reload()
		self.assertEqual(cl.status, "Pending Response")
		self.assertEqual(int(t.clarification_count or 0), 1)

	def test_submit_blocked_when_tender_not_published(self):
		t = self._base_tender("_KT_TCAM034_T2")
		self._criteria(t.name, "C2")
		self._document(t.name)
		cl = frappe.get_doc(
			{
				"doctype": TCL,
				"business_id": "_KT_TCAM034_CL2",
				"tender": t.name,
				"supplier": "SUP-1",
				"question_submitted_by": frappe.session.user,
				"question_datetime": "2026-05-02 10:00:00",
				"question_text": "Question?",
				"status": "Draft",
				"visibility_mode": "Internal",
			}
		)
		cl.insert(ignore_permissions=True)
		self.assertRaises(frappe.ValidationError, submit_clarification, cl.name)

	def test_publish_response_answered_count_unchanged(self):
		t = self._published_tender("_KT_TCAM034_T3")
		frappe.db.set_value(TENDER, t.name, "clarification_count", 0, update_modified=False)
		cl = frappe.get_doc(
			{
				"doctype": TCL,
				"business_id": "_KT_TCAM034_CL3",
				"tender": t.name,
				"supplier": "SUP-1",
				"question_submitted_by": frappe.session.user,
				"question_datetime": "2026-05-02 10:00:00",
				"question_text": "Delivery date?",
				"status": "Draft",
				"visibility_mode": "Internal",
			}
		)
		cl.insert(ignore_permissions=True)
		submit_clarification(cl.name, user="Administrator")
		t.reload()
		self.assertEqual(int(t.clarification_count or 0), 1)
		publish_clarification_response(cl.name, response_text="See section 4.", user="Administrator")
		cl.reload()
		t.reload()
		self.assertEqual(cl.status, "Answered")
		self.assertTrue(cl.response_text)
		self.assertEqual(int(t.clarification_count or 0), 1)

	def test_submit_clarification_insert_path(self):
		t = self._published_tender("_KT_TCAM034_T4")
		frappe.db.set_value(TENDER, t.name, "clarification_count", 0, update_modified=False)
		doc = submit_clarification(
			None,
			tender=t.name,
			business_id="_KT_TCAM034_CL4",
			supplier="SUP-X",
			question_text="Price basis?",
			user="Administrator",
		)
		self.assertEqual(doc.status, "Pending Response")
		t.reload()
		self.assertEqual(int(t.clarification_count or 0), 1)

	def test_create_amendment_then_publish_updates_tender(self):
		t = self._published_tender("_KT_TCAM034_T5")
		frappe.db.set_value(
			TENDER,
			t.name,
			{"amendment_count": 0, "latest_amendment_ref": None},
			update_modified=False,
		)
		am = create_tender_amendment(
			t.name,
			change_summary="Clarify scope",
			reason="Buyer request",
			effective_datetime="2026-05-15 12:00:00",
			user="Administrator",
		)
		self.assertEqual(am.status, "Draft")
		self.assertEqual(am.amendment_no, 1)
		t.reload()
		self.assertEqual(int(t.amendment_count or 0), 0)
		publish_tender_amendment(am.name, user="Administrator")
		am.reload()
		t.reload()
		self.assertEqual(am.status, "Published")
		self.assertTrue(am.published_at)
		self.assertEqual(int(t.amendment_count or 0), 1)
		self.assertEqual((t.latest_amendment_ref or "").strip(), (am.business_id or "").strip())

	def test_publish_amendment_twice_blocked(self):
		t = self._published_tender("_KT_TCAM034_T6")
		am = create_tender_amendment(
			t.name,
			change_summary="X",
			reason="Y",
			effective_datetime="2026-05-15 12:00:00",
			user="Administrator",
		)
		publish_tender_amendment(am.name, user="Administrator")
		self.assertRaises(frappe.ValidationError, publish_tender_amendment, am.name)
