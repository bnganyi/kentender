# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-026: Tender Document."""

import hashlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_LOT = "Tender Lot"
TENDER_DOCUMENT = "Tender Document"
DOCUMENT_TYPE_REGISTRY = "Document Type Registry"
FILE = "File"
BCP = "Budget Control Period"


def _cleanup_tdc026():
	for row in frappe.get_all(TENDER_DOCUMENT, filters={"tender": ("like", "_KT_TDC026_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_DOCUMENT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_LOT, filters={"tender": ("like", "_KT_TDC026_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_LOT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TDC026_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for fn in (
		frappe.get_all(
			FILE,
			filters={"attached_to_doctype": TENDER, "attached_to_name": ("like", "_KT_TDC026_%")},
			pluck="name",
		)
		or []
	):
		frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
	frappe.db.delete(DOCUMENT_TYPE_REGISTRY, {"document_type_code": "_KT_TDC026_DT1"})
	frappe.db.delete(BCP, {"name": ("like", "_KT_TDC026_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TDC026_PE"})


class TestTenderDocument(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tdc026)
		self.entity = _make_entity("_KT_TDC026_PE").insert()
		self.period = _bcp("_KT_TDC026_BCP", self.entity.name).insert()
		self.dt = frappe.get_doc(
			{
				"doctype": DOCUMENT_TYPE_REGISTRY,
				"document_type_code": "_KT_TDC026_DT1",
				"document_type_name": "TDC026 test doc type",
			}
		)
		self.dt.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tdc026)
		super().tearDown()

	def _tender(self, name: str, *, is_multi_lot: int = 0):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "TDC tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
				"is_multi_lot": is_multi_lot,
			}
		).insert(ignore_permissions=True)

	def _lot(self, tender_name: str, lot_no: int = 1):
		return frappe.get_doc(
			{
				"doctype": TENDER_LOT,
				"tender": tender_name,
				"lot_no": lot_no,
				"lot_title": "Lot",
				"estimated_amount": 5000,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"award_status": "Not Awarded",
			}
		).insert(ignore_permissions=True)

	def _file_for_tender(self, tender_name: str, content: bytes):
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "_kt_tdc026.txt",
				"content": content,
				"attached_to_doctype": TENDER,
				"attached_to_name": tender_name,
			}
		)
		fd.insert(ignore_permissions=True)
		return fd

	def _tender_document(self, **kwargs):
		base = {
			"doctype": TENDER_DOCUMENT,
			"document_type": self.dt.name,
			"document_title": "Spec",
			"document_version_no": 1,
			"status": "Draft",
			"sensitivity_class": "Internal",
		}
		base.update(kwargs)
		return frappe.get_doc(base)

	def test_valid_tender_document(self):
		t = self._tender("_KT_TDC026_T1")
		content = b"tender document test bytes for hash"
		fd = self._file_for_tender(t.name, content)
		doc = self._tender_document(tender=t.name, attached_file=fd.name)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Spec", doc.display_label or "")
		expected = hashlib.sha256(content).hexdigest()
		self.assertEqual(doc.hash_value, expected)

	def test_lot_tender_mismatch_blocked(self):
		t1 = self._tender("_KT_TDC026_TA", is_multi_lot=1)
		t2 = self._tender("_KT_TDC026_TB", is_multi_lot=1)
		lot_a = self._lot(t1.name, 1)
		fd = self._file_for_tender(t2.name, b"x")
		doc = self._tender_document(
			tender=t2.name,
			lot=lot_a.name,
			attached_file=fd.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supersedes_wrong_tender_blocked(self):
		t1 = self._tender("_KT_TDC026_TS1")
		t2 = self._tender("_KT_TDC026_TS2")
		f1 = self._file_for_tender(t1.name, b"v1")
		f2 = self._file_for_tender(t2.name, b"v2")
		first = self._tender_document(tender=t1.name, attached_file=f1.name, document_title="V1")
		first.insert(ignore_permissions=True)
		second = self._tender_document(
			tender=t2.name,
			attached_file=f2.name,
			document_title="V2",
			supersedes_document=first.name,
		)
		self.assertRaises(frappe.ValidationError, second.insert, ignore_permissions=True)

	def test_missing_file_or_document_type_blocked(self):
		t = self._tender("_KT_TDC026_TM1")
		fd = self._file_for_tender(t.name, b"ok")
		bad_dt = self._tender_document(
			tender=t.name,
			attached_file=fd.name,
			document_type="NONEXISTENT-DT-CODE-99999",
		)
		self.assertRaises(frappe.ValidationError, bad_dt.insert, ignore_permissions=True)
		bad_file = self._tender_document(
			tender=t.name,
			attached_file="nonexistent-file-id-xyz",
			document_type=self.dt.name,
		)
		self.assertRaises(frappe.ValidationError, bad_file.insert, ignore_permissions=True)
