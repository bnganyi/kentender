# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-032: tender publication readiness."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.tender_publication_readiness import assess_tender_publication_readiness

TENDER = "Tender"
TCR = "Tender Criteria"
TDOC = "Tender Document"
TVR = "Tender Visibility Rule"
BCP = "Budget Control Period"
FILE = "File"
DTR = "Document Type Registry"


def _cleanup_tpro():
	for dt in (TCR, TDOC, TVR):
		for row in frappe.get_all(dt, filters={"tender": ("like", "_KT_TPRO_%")}, pluck="name") or []:
			frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_TPRO_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for fn in (
		frappe.get_all(
			FILE,
			filters={"attached_to_doctype": TENDER, "attached_to_name": ("like", "_KT_TPRO_%")},
			pluck="name",
		)
		or []
	):
		frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
	frappe.db.delete(DTR, {"document_type_code": ("like", "_KT_TPRO_%")})
	frappe.db.delete(BCP, {"name": ("like", "_KT_TPRO_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_TPRO_PE"})


class TestTenderPublicationReadiness(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_tpro)
		self.entity = _make_entity("_KT_TPRO_PE").insert()
		self.period = _bcp("_KT_TPRO_BCP", self.entity.name).insert()
		self.dtr = frappe.get_doc(
			{
				"doctype": DTR,
				"document_type_code": "_KT_TPRO_DT1",
				"document_type_name": "TPRO doc type",
			}
		)
		self.dtr.insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_tpro)
		super().tearDown()

	def _tender(self, name: str, **extra):
		kw = {
			"doctype": TENDER,
			"name": name,
			"business_id": f"{name}-BIZ",
			"title": "TPRO tender",
			"tender_number": f"{name}-TN",
			"workflow_state": "Draft",
			"status": "Draft",
			"approval_status": "Draft",
			"origin_type": "Manual",
			"procuring_entity": self.entity.name,
			"currency": self.currency,
			"supplier_eligibility_rule_mode": "Open",
			"procurement_method": "Open National Tender",
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def test_not_ready_without_schedule_and_criteria(self):
		t = self._tender("_KT_TPRO_T1")
		out = assess_tender_publication_readiness(t.name)
		self.assertFalse(out["ok"])
		self.assertTrue(any("Publication datetime" in x for x in out["reasons"]))
		self.assertTrue(any("criteria" in x.lower() for x in out["reasons"]))
		self.assertTrue(any("document" in x.lower() for x in out["reasons"]))

	def test_not_ready_when_date_chain_invalid(self):
		t = self._tender(
			"_KT_TPRO_T2",
			publication_datetime="2026-06-01 09:00:00",
			clarification_deadline="2026-06-05 17:00:00",
			submission_deadline="2026-06-15 17:00:00",
			opening_datetime="2026-06-16 10:00:00",
		)
		# Bypass Document.validate — readiness service must still flag incoherent DB state.
		frappe.db.set_value(
			TENDER,
			t.name,
			{"clarification_deadline": "2026-05-01 09:00:00"},
			update_modified=False,
		)
		out = assess_tender_publication_readiness(t.name)
		self.assertFalse(out["ok"])
		self.assertTrue(any("Clarification" in x or "Publication" in x for x in out["reasons"]))

	def test_visibility_required_when_not_open_mode(self):
		t = self._tender(
			"_KT_TPRO_T3",
			publication_datetime="2026-05-01 09:00:00",
			clarification_deadline="2026-05-10 17:00:00",
			submission_deadline="2026-06-01 17:00:00",
			opening_datetime="2026-06-02 10:00:00",
			supplier_eligibility_rule_mode="Prequalified",
		)
		frappe.get_doc(
			{
				"doctype": TCR,
				"tender": t.name,
				"criteria_type": "Technical",
				"criteria_code": "M-1",
				"criteria_title": "Must",
				"score_type": "Numeric",
				"max_score": 100,
				"weight_percentage": 25,
				"minimum_pass_mark": 40,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		content = b"x"
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "tpro.txt",
				"content": content,
				"attached_to_doctype": TENDER,
				"attached_to_name": t.name,
			}
		)
		fd.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": TDOC,
				"tender": t.name,
				"document_type": self.dtr.name,
				"document_title": "Spec",
				"document_version_no": 1,
				"attached_file": fd.name,
				"status": "Draft",
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)
		out = assess_tender_publication_readiness(t.name)
		self.assertFalse(out["ok"])
		self.assertTrue(any("Visibility" in x for x in out["reasons"]))

	def test_ready_when_minimal_rows_and_valid_schedule(self):
		t = self._tender(
			"_KT_TPRO_T4",
			publication_datetime="2026-05-01 09:00:00",
			clarification_deadline="2026-05-10 17:00:00",
			submission_deadline="2026-06-01 17:00:00",
			opening_datetime="2026-06-02 10:00:00",
		)
		frappe.get_doc(
			{
				"doctype": TCR,
				"tender": t.name,
				"criteria_type": "Technical",
				"criteria_code": "M-1",
				"criteria_title": "Must",
				"score_type": "Numeric",
				"max_score": 100,
				"weight_percentage": 25,
				"minimum_pass_mark": 40,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		content = b"x"
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "tpro2.txt",
				"content": content,
				"attached_to_doctype": TENDER,
				"attached_to_name": t.name,
			}
		)
		fd.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": TDOC,
				"tender": t.name,
				"document_type": self.dtr.name,
				"document_title": "Spec",
				"document_version_no": 1,
				"attached_file": fd.name,
				"status": "Draft",
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)
		out = assess_tender_publication_readiness(t.name)
		self.assertTrue(out["ok"], out.get("reasons"))
		self.assertFalse(out["reasons"])
