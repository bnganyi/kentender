# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-043: bid draft / upload / validation services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.bid_draft_validate_services import (
	create_bid_draft,
	run_bid_validation,
	upload_bid_document,
)
from kentender_procurement.services.tender_workflow_actions import approve_tender, publish_tender, submit_tender_for_review

TENDER = "Tender"
TCR = "Tender Criteria"
TDOC = "Tender Document"
TVR = "Tender Visibility Rule"
BS = "Bid Submission"
BES = "Bid Envelope Section"
BD = "Bid Document"
BVI = "Bid Validation Issue"
FILE = "File"
BCP = "Budget Control Period"
DTR = "Document Type Registry"


def _cleanup_bvi043():
	"""Remove fixtures by tender prefix; bid business_ids are service-generated (BID-…), not _KT_ prefixed."""
	for bs in frappe.get_all(BS, filters={"tender": ("like", "_KT_BVI043_%")}, pluck="name") or []:
		for row in frappe.get_all(BVI, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BVI, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(BD, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BD, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(BES, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BES, row, force=True, ignore_permissions=True)
		frappe.delete_doc(BS, bs, force=True, ignore_permissions=True)
	for dt in (TCR, TDOC, TVR):
		for row in frappe.get_all(dt, filters={"tender": ("like", "_KT_BVI043_%")}, pluck="name") or []:
			frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BVI043_%")}, pluck="name") or []:
		for fn in (
			frappe.get_all(FILE, filters={"attached_to_doctype": TENDER, "attached_to_name": tn}, pluck="name")
			or []
		):
			frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(DTR, {"document_type_code": ("like", "_KT_BVI043_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_BVI043_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BVI043_PE"})


class TestBidDraftValidateServices(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bvi043)
		self.entity = _make_entity("_KT_BVI043_PE").insert()
		self.period = _bcp("_KT_BVI043_BCP", self.entity.name).insert()
		self.dtr = frappe.get_doc(
			{
				"doctype": DTR,
				"document_type_code": "_KT_BVI043_DT1",
				"document_type_name": "BVI043 doc type",
			}
		)
		self.dtr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bvi043)
		super().tearDown()

	def _base_tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "BVI043 tender",
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

	def _tender_document(self, tender_name: str, *, mandatory: bool = False):
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "bvi043.txt",
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
		t = frappe.get_doc(TENDER, tender_name)
		self._criteria(t.name, "C1")
		self._tender_document(t.name, mandatory=False)
		submit_tender_for_review(t.name, user="Administrator")
		approve_tender(t.name, user="Administrator")
		publish_tender(t.name, user="Administrator")

	def test_create_draft_and_validation_pass(self):
		t = self._base_tender("_KT_BVI043_T1")
		self._criteria(t.name, "CX")
		self._tender_document(t.name, mandatory=False)
		td_mand = self._tender_document(t.name, mandatory=True)
		self.assertTrue(td_mand.is_mandatory_for_supplier_response)
		submit_tender_for_review(t.name, user="Administrator")
		approve_tender(t.name, user="Administrator")
		publish_tender(t.name, user="Administrator")

		bid = create_bid_draft(t.name, "SUP-BVI043-1")
		self.assertTrue(bid.name)
		self.assertEqual(bid.document_count, 0)

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
				"file_name": "bid.txt",
				"content": b"bid bytes",
				"attached_to_doctype": TENDER,
				"attached_to_name": t.name,
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
		bid.reload()
		self.assertEqual(bid.document_count, 1)

		res = run_bid_validation(bid.name)
		self.assertEqual(res["validation_status"], "Pass")
		self.assertEqual(res["eligibility_check_status"], "Pass")
		self.assertEqual(res["mandatory_document_check_status"], "Pass")
		self.assertEqual(res["structure_check_status"], "Pass")

	def test_create_blocked_when_tender_not_published(self):
		t = self._base_tender("_KT_BVI043_T2")
		self.assertRaises(frappe.ValidationError, create_bid_draft, t.name, "SUP-X")

	def test_duplicate_draft_blocked(self):
		t = self._base_tender("_KT_BVI043_T3")
		self._publish(t.name)
		create_bid_draft(t.name, "SUP-DUP")
		self.assertRaises(frappe.ValidationError, create_bid_draft, t.name, "SUP-DUP")

	def test_validation_blocking_mandatory_and_structure(self):
		t = self._base_tender("_KT_BVI043_T4")
		self._criteria(t.name, "C4")
		self._tender_document(t.name, mandatory=False)
		self._tender_document(t.name, mandatory=True)
		submit_tender_for_review(t.name, user="Administrator")
		approve_tender(t.name, user="Administrator")
		publish_tender(t.name, user="Administrator")

		bid = create_bid_draft(t.name, "SUP-VAL")
		frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": bid.name,
				"section_type": "Mandatory Documents",
				"section_title": "ReqSec",
				"display_order": 1,
				"status": "Draft",
				"completion_status": "Not Started",
				"is_required": 1,
			}
		).insert(ignore_permissions=True)

		res = run_bid_validation(bid.name)
		self.assertEqual(res["validation_status"], "Fail")
		self.assertEqual(res["mandatory_document_check_status"], "Fail")
		self.assertEqual(res["structure_check_status"], "Fail")
		n_issues = frappe.db.count(BVI, {"bid_submission": bid.name})
		self.assertGreaterEqual(n_issues, 2)

	def test_prequalified_mode_blocks_draft(self):
		t = self._base_tender("_KT_BVI043_T5", supplier_eligibility_rule_mode="Prequalified")
		self._criteria(t.name, "C5")
		self._tender_document(t.name, mandatory=False)
		frappe.get_doc(
			{
				"doctype": TVR,
				"tender": t.name,
				"rule_type": "Invitation List",
				"rule_value": "list-1",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		submit_tender_for_review(t.name, user="Administrator")
		approve_tender(t.name, user="Administrator")
		publish_tender(t.name, user="Administrator")

		self.assertRaises(frappe.ValidationError, create_bid_draft, t.name, "SUP-PQ")
