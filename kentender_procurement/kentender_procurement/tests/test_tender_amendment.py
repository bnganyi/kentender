# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-030: Tender Amendment."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
TENDER_DOCUMENT = "Tender Document"
TAM = "Tender Amendment"
DOCUMENT_TYPE_REGISTRY = "Document Type Registry"
FILE = "File"
BCP = "Budget Control Period"


def _cleanup_tam030():
	for row in frappe.get_all(TAM, filters={"tender": ("like", "_KT_TAM030_%")}, pluck="name") or []:
		frappe.delete_doc(TAM, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TENDER_DOCUMENT, filters={"tender": ("like", "_KT_TAM030_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER_DOCUMENT, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TAM030_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for fn in (
		frappe.get_all(
			FILE,
			filters={"attached_to_doctype": TENDER, "attached_to_name": ("like", "_KT_TAM030_%")},
			pluck="name",
		)
		or []
	):
		frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
	frappe.db.delete(DOCUMENT_TYPE_REGISTRY, {"document_type_code": "_KT_TAM030_DT1"})
	frappe.db.delete(BCP, {"name": ("like", "_KT_TAM030_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TAM030_PE"})


class TestTenderAmendment(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tam030)
		self.entity = _make_entity("_KT_TAM030_PE").insert()
		self.period = _bcp("_KT_TAM030_BCP", self.entity.name).insert()
		self.dt = frappe.get_doc(
			{
				"doctype": DOCUMENT_TYPE_REGISTRY,
				"document_type_code": "_KT_TAM030_DT1",
				"document_type_name": "TAM030 test doc type",
			}
		)
		self.dt.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tam030)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "TAM tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _file_for_tender(self, tender_name: str, content: bytes = b"x"):
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "_kt_tam030.txt",
				"content": content,
				"attached_to_doctype": TENDER,
				"attached_to_name": tender_name,
			}
		)
		fd.insert(ignore_permissions=True)
		return fd

	def _tender_document(self, tender_name: str):
		fd = self._file_for_tender(tender_name)
		return frappe.get_doc(
			{
				"doctype": TENDER_DOCUMENT,
				"tender": tender_name,
				"document_type": self.dt.name,
				"attached_file": fd.name,
				"document_title": "Annex",
				"document_version_no": 1,
				"status": "Draft",
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)

	def _amendment(self, **kwargs):
		base = {
			"doctype": TAM,
			"business_id": "_KT_TAM030_A1",
			"amendment_no": 1,
			"amendment_type": "Administrative",
			"change_summary": "Summary",
			"reason": "Because",
			"effective_datetime": "2026-04-10 12:00:00",
			"status": "Draft",
		}
		base.update(kwargs)
		return frappe.get_doc(base)

	def test_valid_amendment_create(self):
		t = self._tender("_KT_TAM030_T1")
		doc = self._amendment(
			tender=t.name,
			business_id="_KT_TAM030_B1",
		)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertEqual(doc.tender, t.name)
		self.assertIn("_KT_TAM030_B1", doc.display_label or "")
		self.assertIn("Amendment 1", doc.display_label or "")

	def test_deadline_extension_requires_new_submission_deadline(self):
		t = self._tender("_KT_TAM030_T2")
		doc = self._amendment(
			tender=t.name,
			business_id="_KT_TAM030_B2",
			requires_deadline_extension=1,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_deadline_fields_blocked_without_extension_flag(self):
		t = self._tender("_KT_TAM030_T3")
		doc = self._amendment(
			tender=t.name,
			business_id="_KT_TAM030_B3",
			new_submission_deadline="2026-05-01 17:00:00",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_related_document_must_match_tender(self):
		t1 = self._tender("_KT_TAM030_TA")
		t2 = self._tender("_KT_TAM030_TB")
		td_on_b = self._tender_document(t2.name)
		doc = self._amendment(
			tender=t1.name,
			business_id="_KT_TAM030_B4",
			related_document=td_on_b.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_amendment_no_blocked(self):
		t = self._tender("_KT_TAM030_TD")
		self._amendment(tender=t.name, business_id="_KT_TAM030_B5").insert(ignore_permissions=True)
		doc2 = self._amendment(tender=t.name, business_id="_KT_TAM030_B6", amendment_no=1)
		self.assertRaises(frappe.ValidationError, doc2.insert, ignore_permissions=True)
