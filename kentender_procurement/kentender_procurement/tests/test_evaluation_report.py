# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-065: Evaluation Report."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
ERPT = "Evaluation Report"
BCP = "Budget Control Period"


def _cleanup_es065():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES065_%")}, pluck="name") or []:
		for row in frappe.get_all(ERPT, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES065_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES065_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES065_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES065_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES065_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES065_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES065_PE"})


class TestEvaluationReport065(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es065)
		self.entity = _make_entity("_KT_ES065_PE").insert()
		self.period = _bcp("_KT_ES065_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es065)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES065 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _opening_session(self, tender_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)

	def _register(self, tender_name: str, session_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": business_id,
				"tender": tender_name,
				"bid_opening_session": session_name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _evaluation_session(self, tender_name: str, bos_name: str, bor_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": ES,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"opening_session": bos_name,
				"opening_register": bor_name,
				"evaluation_mode": "Two Envelope",
				"conflict_clearance_status": "Pending",
			}
		).insert(ignore_permissions=True)

	def _minimal_chain(self, suffix: str):
		t = self._tender(f"_KT_ES065_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES065_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES065_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES065_E{suffix}")
		return t, s, r, e

	def _bid(self, tender_name: str, business_id: str, supplier: str):
		return frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": business_id,
				"tender": tender_name,
				"supplier": supplier,
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)

	def _report(self, **kw):
		base = {
			"doctype": ERPT,
			"business_id": kw.pop("business_id"),
			"evaluation_session": kw.pop("evaluation_session"),
			"tender": kw.pop("tender"),
			"status": kw.pop("status", "Draft"),
			"responsive_bid_count": kw.pop("responsive_bid_count", 0),
			"non_responsive_bid_count": kw.pop("non_responsive_bid_count", 0),
			"disqualified_bid_count": kw.pop("disqualified_bid_count", 0),
		}
		base.update(kw)
		return frappe.get_doc(base)

	def test_valid_report_create(self):
		t, _, _, e = self._minimal_chain("1")
		b = self._bid(t.name, "_KT_ES065_B1", "ES065-SUP-1")
		doc = self._report(
			business_id="_KT_ES065_RPT1",
			evaluation_session=e.name,
			tender=t.name,
			recommended_bid_submission=b.name,
			recommended_supplier="ES065-SUP-1",
			recommendation_justification="Award recommended per evaluation criteria.",
			currency=self.currency,
			recommended_amount=1000.0,
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertTrue(doc.display_label)
		self.assertIn("Draft", doc.display_label)

	def test_recommendation_requires_justification(self):
		t, _, _, e = self._minimal_chain("2")
		b = self._bid(t.name, "_KT_ES065_B2", "ES065-SUP-2")
		doc = self._report(
			business_id="_KT_ES065_RPT2",
			evaluation_session=e.name,
			tender=t.name,
			recommended_bid_submission=b.name,
			recommended_supplier="ES065-SUP-2",
			recommendation_justification="",
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_tender_session_mismatch_blocked(self):
		t_a, _, _, e = self._minimal_chain("3A")
		t_b = self._tender("_KT_ES065_T3B")
		doc = self._report(
			business_id="_KT_ES065_RPT3",
			evaluation_session=e.name,
			tender=t_b.name,
		)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_duplicate_session_report_blocked(self):
		t, _, _, e = self._minimal_chain("4")
		self._report(
			business_id="_KT_ES065_RPT4A",
			evaluation_session=e.name,
			tender=t.name,
		).insert(ignore_permissions=True)
		dup = self._report(
			business_id="_KT_ES065_RPT4B",
			evaluation_session=e.name,
			tender=t.name,
		)
		self.assertRaises(frappe.ValidationError, dup.insert, ignore_permissions=True)
