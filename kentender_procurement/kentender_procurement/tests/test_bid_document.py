# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-038: Bid Document."""

import hashlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BS = "Bid Submission"
BES = "Bid Envelope Section"
BD = "Bid Document"
DOCUMENT_TYPE_REGISTRY = "Document Type Registry"
FILE = "File"
BCP = "Budget Control Period"


def _cleanup_bd038():
	for bs in frappe.get_all(BS, filters={"business_id": ("like", "_KT_BD038_%")}, pluck="name") or []:
		for row in frappe.get_all(BD, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BD, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(BES, filters={"bid_submission": bs}, pluck="name") or []:
			frappe.delete_doc(BES, row, force=True, ignore_permissions=True)
		frappe.delete_doc(BS, bs, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_BD038_%")}, pluck="name") or []:
		for fn in (
			frappe.get_all(
				FILE,
				filters={"attached_to_doctype": TENDER, "attached_to_name": tn},
				pluck="name",
			)
			or []
		):
			frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(DOCUMENT_TYPE_REGISTRY, {"document_type_code": "_KT_BD038_DT1"})
	frappe.db.delete(BCP, {"name": ("like", "_KT_BD038_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_BD038_PE"})


class TestBidDocument(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_bd038)
		self.entity = _make_entity("_KT_BD038_PE").insert()
		self.period = _bcp("_KT_BD038_BCP", self.entity.name).insert()
		self.dt = frappe.get_doc(
			{
				"doctype": DOCUMENT_TYPE_REGISTRY,
				"document_type_code": "_KT_BD038_DT1",
				"document_type_name": "BD038 test doc type",
			}
		)
		self.dt.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_bd038)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "BD038 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _bid(self, tender_name: str, bid_business_id: str):
		return frappe.get_doc(
			{
				"doctype": BS,
				"business_id": bid_business_id,
				"tender": tender_name,
				"supplier": "SUP-1",
				"tender_lot_scope": "Whole Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def _section(self, bs_name: str, title: str = "Section A"):
		return frappe.get_doc(
			{
				"doctype": BES,
				"bid_submission": bs_name,
				"section_type": "Mandatory Documents",
				"section_title": title,
				"display_order": 1,
				"status": "Draft",
				"completion_status": "Not Started",
			}
		).insert(ignore_permissions=True)

	def _file_for_tender(self, tender_name: str, content: bytes):
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "bd038.txt",
				"content": content,
				"attached_to_doctype": TENDER,
				"attached_to_name": tender_name,
			}
		)
		fd.insert(ignore_permissions=True)
		return fd

	def test_valid_create_and_hash(self):
		t = self._tender("_KT_BD038_T1")
		bs = self._bid(t.name, "_KT_BD038_B1")
		sec = self._section(bs.name)
		content = b"bid document bytes for hash test"
		fd = self._file_for_tender(t.name, content)
		doc = frappe.get_doc(
			{
				"doctype": BD,
				"bid_submission": bs.name,
				"bid_envelope_section": sec.name,
				"document_type": self.dt.name,
				"attached_file": fd.name,
				"document_title": "Financial annex",
				"status": "Draft",
				"sensitivity_class": "Internal",
				"validation_status": "Pending",
			}
		)
		doc.insert(ignore_permissions=True)
		self.assertEqual(doc.hash_value, hashlib.sha256(content).hexdigest())
		self.assertIn("Financial annex", doc.display_label or "")

	def test_section_mismatch_blocked(self):
		t = self._tender("_KT_BD038_T2")
		bs_a = self._bid(t.name, "_KT_BD038_B2")
		bs_b = self._bid(t.name, "_KT_BD038_B3")
		sec = self._section(bs_a.name, title="Only A")
		fd = self._file_for_tender(t.name, b"x")
		doc = frappe.get_doc(
			{
				"doctype": BD,
				"bid_submission": bs_b.name,
				"bid_envelope_section": sec.name,
				"document_type": self.dt.name,
				"attached_file": fd.name,
				"document_title": "Wrong",
				"status": "Draft",
				"sensitivity_class": "Internal",
				"validation_status": "Pending",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_invalid_document_type_blocked(self):
		t = self._tender("_KT_BD038_T3")
		bs = self._bid(t.name, "_KT_BD038_B4")
		sec = self._section(bs.name)
		fd = self._file_for_tender(t.name, b"y")
		doc = frappe.get_doc(
			{
				"doctype": BD,
				"bid_submission": bs.name,
				"bid_envelope_section": sec.name,
				"document_type": "NONEXISTENT-DTR",
				"attached_file": fd.name,
				"document_title": "X",
				"status": "Draft",
				"sensitivity_class": "Internal",
				"validation_status": "Pending",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_invalid_sensitivity_blocked(self):
		t = self._tender("_KT_BD038_T4")
		bs = self._bid(t.name, "_KT_BD038_B5")
		sec = self._section(bs.name)
		fd = self._file_for_tender(t.name, b"z")
		doc = frappe.get_doc(
			{
				"doctype": BD,
				"bid_submission": bs.name,
				"bid_envelope_section": sec.name,
				"document_type": self.dt.name,
				"attached_file": fd.name,
				"document_title": "X",
				"status": "Draft",
				"sensitivity_class": "Top Secret",
				"validation_status": "Pending",
			}
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
