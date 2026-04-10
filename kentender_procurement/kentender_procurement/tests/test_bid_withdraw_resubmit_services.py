# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-045: withdraw and resubmit services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE

from kentender_procurement.services.bid_draft_validate_services import create_bid_draft, run_bid_validation, upload_bid_document
from kentender_procurement.services.bid_final_submit_services import submit_bid
from kentender_procurement.services.bid_withdraw_resubmit_services import (
	create_resubmission_from_withdrawn_bid,
	withdraw_bid,
)
from kentender_procurement.services.tender_workflow_actions import approve_tender, publish_tender, submit_tender_for_review

TENDER = "Tender"
TCR = "Tender Criteria"
TDOC = "Tender Document"
BS = "Bid Submission"
BES = "Bid Envelope Section"
BD = "Bid Document"
BWR = "Bid Withdrawal Record"
BSE = "Bid Submission Event"
BVI = "Bid Validation Issue"
FILE = "File"
BCP = "Budget Control Period"
DTR = "Document Type Registry"


def _cleanup_bwr045():
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BWR045_%")}, pluck="name") or []:
		for bs in frappe.get_all(BS, filters={"tender": tn}, pluck="name") or []:
			frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": BS, "target_docname": bs})
			for row in frappe.get_all(BSE, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.db.delete(BSE, {"name": row})
			for row in frappe.get_all(BWR, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.db.delete(BWR, {"name": row})
			for row in frappe.get_all(BVI, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.db.delete(BVI, {"name": row})
			for row in frappe.get_all(BD, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.delete_doc(BD, row, force=True, ignore_permissions=True)
			for row in frappe.get_all(BES, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.delete_doc(BES, row, force=True, ignore_permissions=True)
			for row in frappe.get_all("Bid Receipt", filters={"bid_submission": bs}, pluck="name") or []:
				frappe.delete_doc("Bid Receipt", row, force=True, ignore_permissions=True)
			frappe.delete_doc(BS, bs, force=True, ignore_permissions=True)
	for dt in (TCR, TDOC):
		for row in frappe.get_all(dt, filters={"tender": ("like", "_KT_BWR045_%")}, pluck="name") or []:
			frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BWR045_%")}, pluck="name") or []:
		for fn in (
			frappe.get_all(FILE, filters={"attached_to_doctype": TENDER, "attached_to_name": tn}, pluck="name")
			or []
		):
			frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(DTR, {"document_type_code": ("like", "_KT_BWR045_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_BWR045_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BWR045_PE"})


class TestBidWithdrawResubmitServices(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bwr045)
		self.entity = _make_entity("_KT_BWR045_PE").insert()
		self.period = _bcp("_KT_BWR045_BCP", self.entity.name).insert()
		self.dtr = frappe.get_doc(
			{
				"doctype": DTR,
				"document_type_code": "_KT_BWR045_DT1",
				"document_type_name": "BWR045 doc type",
			}
		)
		self.dtr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bwr045)
		super().tearDown()

	def _base_tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BWR045 tender",
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
			"submission_deadline": "2030-06-01 17:00:00",
			"opening_datetime": "2030-06-02 10:00:00",
			"allows_withdrawal_before_deadline": 1,
			"allows_resubmission_before_deadline": 1,
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

	def _tender_document(self, tender_name: str, *, mandatory: bool):
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "bwr045.txt",
				"content": b"spec",
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
				"status": "Active",
				"sensitivity_class": "Internal",
				"is_mandatory_for_supplier_response": 1 if mandatory else 0,
			}
		).insert(ignore_permissions=True)

	def _publish(self, tender_name: str):
		self._criteria(tender_name, "C1")
		self._tender_document(tender_name, mandatory=False)
		self._tender_document(tender_name, mandatory=True)
		submit_tender_for_review(tender_name, user="Administrator")
		approve_tender(tender_name, user="Administrator")
		publish_tender(tender_name, user="Administrator")

	def _submit_ready_bid(self, tender_name: str, supplier: str):
		self._publish(tender_name)
		bid = create_bid_draft(tender_name, supplier)
		sec = frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": bid.name,
				"section_type": "Mandatory Documents",
				"section_title": "Main",
				"display_order": 1,
				"status": "Draft",
				"completion_status": "Not Started",
				"is_required": 1,
			}
		).insert(ignore_permissions=True)
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "resp.txt",
				"content": b"response",
				"attached_to_doctype": TENDER,
				"attached_to_name": tender_name,
			}
		)
		fd.insert(ignore_permissions=True)
		upload_bid_document(
			bid.name,
			sec.name,
			document_type=self.dtr.name,
			attached_file=fd.name,
			document_title="Response",
		)
		run_bid_validation(bid.name)
		submit_bid(bid.name, user="Administrator")
		return frappe.get_doc(BS, bid.name)

	def test_withdraw_after_submit_ok(self):
		t = self._base_tender("_KT_BWR045_T1")
		bid = self._submit_ready_bid(t.name, "SUP-W1")
		out = withdraw_bid(bid.name, reason="Change in consortium", user="Administrator")
		self.assertTrue(out.get("withdrawn_on"))
		bid.reload()
		self.assertEqual(bid.workflow_state, "Withdrawn")
		self.assertEqual(bid.status, "Withdrawn")
		self.assertEqual(bid.active_submission_flag, 0)
		self.assertTrue(frappe.db.exists(BWR, {"bid_submission": bid.name}))

	def test_withdraw_blocked_after_opening_time(self):
		t = self._base_tender("_KT_BWR045_T2")
		bid = self._submit_ready_bid(t.name, "SUP-W2")
		frappe.db.set_value(TENDER, t.name, "opening_datetime", "2020-01-01 10:00:00")
		frappe.db.set_value(BS, bid.name, "opening_datetime", "2020-01-01 10:00:00")
		self.assertRaises(frappe.ValidationError, withdraw_bid, bid.name, reason="Too late")

	def test_withdraw_blocked_when_tender_disallows(self):
		t = self._base_tender("_KT_BWR045_T3", allows_withdrawal_before_deadline=0)
		bid = self._submit_ready_bid(t.name, "SUP-W3")
		self.assertRaises(frappe.ValidationError, withdraw_bid, bid.name, reason="Not allowed")

	def test_resubmit_from_withdrawn(self):
		t = self._base_tender("_KT_BWR045_T4")
		bid = self._submit_ready_bid(t.name, "SUP-W4")
		withdraw_bid(bid.name, reason="Pricing error", user="Administrator")
		new_bid = create_resubmission_from_withdrawn_bid(bid.name)
		self.assertTrue(new_bid.name)
		self.assertEqual(new_bid.prior_bid_submission, bid.name)
		self.assertEqual(new_bid.submission_version_no, 2)
		self.assertEqual(new_bid.workflow_state, "Draft")

	def test_direct_withdraw_save_blocked(self):
		t = self._base_tender("_KT_BWR045_T5")
		bid = self._submit_ready_bid(t.name, "SUP-W5")
		bid.workflow_state = "Withdrawn"
		bid.status = "Withdrawn"
		self.assertRaises(frappe.ValidationError, bid.save, ignore_permissions=True)
