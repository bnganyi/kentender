# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-046: bid document sealed access."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.services.access_audit_service import EVENT_ACCESS_DENIED, EVENT_SENSITIVE_ACCESS
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE

from kentender_procurement.services.bid_document_sealed_access import get_bytes_for_bid_document

TENDER = "Tender"
BS = "Bid Submission"
BES = "Bid Envelope Section"
BD = "Bid Document"
FILE = "File"
BCP = "Budget Control Period"
DTR = "Document Type Registry"


def _cleanup_bdsa046():
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BDSA046_%")}, pluck="name") or []:
		for bs in frappe.get_all(BS, filters={"tender": tn}, pluck="name") or []:
			for row in frappe.get_all(BD, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.delete_doc(BD, row, force=True, ignore_permissions=True)
			for row in frappe.get_all(BES, filters={"bid_submission": bs}, pluck="name") or []:
				frappe.delete_doc(BES, row, force=True, ignore_permissions=True)
			frappe.delete_doc(BS, bs, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BDSA046_%")}, pluck="name") or []:
		for fn in (
			frappe.get_all(FILE, filters={"attached_to_doctype": TENDER, "attached_to_name": tn}, pluck="name")
			or []
		):
			frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(DTR, {"document_type_code": ("like", "_KT_BDSA046_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_BDSA046_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BDSA046_PE"})


class TestBidDocumentSealedAccess(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bdsa046)
		self.entity = _make_entity("_KT_BDSA046_PE").insert()
		self.period = _bcp("_KT_BDSA046_BCP", self.entity.name).insert()
		self.dtr = frappe.get_doc(
			{
				"doctype": DTR,
				"document_type_code": "_KT_BDSA046_DT1",
				"document_type_name": "BDSA046 doc type",
			}
		)
		self.dtr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bdsa046)
		super().tearDown()

	def _minimal_bid_and_doc(self):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_BDSA046_T1",
				"business_id": "_KT_BDSA046_T1-BIZ",
				"title": "BDSA046 tender",
				"tender_number": "TN-046",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		bid = frappe.get_doc(
			{
				"doctype": BS,
				"business_id": "_KT_BDSA046_B1",
				"tender": t.name,
				"supplier": "SUP-S",
				"tender_lot_scope": "Whole Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)
		sec = frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": bid.name,
				"section_type": "Mandatory Documents",
				"section_title": "S",
				"display_order": 1,
				"status": "Draft",
				"completion_status": "Not Started",
			}
		).insert(ignore_permissions=True)
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "sealed.txt",
				"content": b"sealed-bytes-046",
				"attached_to_doctype": TENDER,
				"attached_to_name": t.name,
			}
		)
		fd.insert(ignore_permissions=True)
		doc = frappe.get_doc(
			{
				"doctype": BD,
				"bid_submission": bid.name,
				"bid_envelope_section": sec.name,
				"document_type": self.dtr.name,
				"attached_file": fd.name,
				"document_title": "Annex",
				"status": "Draft",
				"sensitivity_class": "Confidential",
				"validation_status": "Pending",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def test_allowed_with_explicit_permission(self):
		doc = self._minimal_bid_and_doc()
		data = get_bytes_for_bid_document(
			doc.name,
			permission_check=lambda _d: True,
			actor="Administrator",
			procuring_entity=self.entity.name,
		)
		self.assertEqual(data, b"sealed-bytes-046")

	def test_denied_logs_access_denied(self):
		doc = self._minimal_bid_and_doc()
		before = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_ACCESS_DENIED,
				"target_doctype": BD,
				"target_docname": doc.name,
			},
		)
		self.assertRaises(
			frappe.PermissionError,
			lambda: get_bytes_for_bid_document(
				doc.name,
				permission_check=lambda _d: False,
				actor="Administrator",
			),
		)
		after = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_ACCESS_DENIED,
				"target_doctype": BD,
				"target_docname": doc.name,
			},
		)
		self.assertEqual(after, before + 1)

	def test_sensitive_logs_sensitive_access(self):
		doc = self._minimal_bid_and_doc()
		before = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_SENSITIVE_ACCESS,
				"target_doctype": BD,
				"target_docname": doc.name,
			},
		)
		get_bytes_for_bid_document(
			doc.name,
			permission_check=lambda _d: True,
			actor="Administrator",
			procuring_entity=self.entity.name,
		)
		after = frappe.db.count(
			AUDIT_EVENT_DOCTYPE,
			{
				"event_type": EVENT_SENSITIVE_ACCESS,
				"target_doctype": BD,
				"target_docname": doc.name,
			},
		)
		self.assertEqual(after, before + 1)
