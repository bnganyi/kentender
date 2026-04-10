# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-060: Conflict of Interest Declaration."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
COI = "Conflict of Interest Declaration"
BCP = "Budget Control Period"


def _cleanup_es060():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES060_%")}, pluck="name") or []:
		for row in frappe.get_all(COI, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(COI, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES060_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES060_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES060_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES060_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES060_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES060_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES060_PE"})


class TestConflictOfInterestDeclaration060(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es060)
		self.entity = _make_entity("_KT_ES060_PE").insert()
		self.period = _bcp("_KT_ES060_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es060)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES060 tender",
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
		t = self._tender(f"_KT_ES060_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES060_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES060_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES060_E{suffix}")
		return t, s, r, e

	def _declaration(self, evaluation_session_name: str, **extra):
		kw = {
			"doctype": COI,
			"evaluation_session": evaluation_session_name,
			"evaluator_user": frappe.session.user,
			"declaration_status": "Pending",
		}
		kw.update(extra)
		return frappe.get_doc(kw)

	def test_valid_declaration_create(self):
		_, _, _, e = self._minimal_chain("1")
		doc = self._declaration(e.name).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Pending", doc.display_label or "")

	def test_invalid_evaluation_session_blocked(self):
		doc = self._declaration("nonexistent-es-060-xyz")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_related_bid_wrong_tender_blocked(self):
		t_a = self._tender("_KT_ES060_T2A")
		t_b = self._tender("_KT_ES060_T2B")
		s = self._opening_session(t_a.name, "_KT_ES060_S2")
		r = self._register(t_a.name, s.name, "_KT_ES060_R2")
		e = self._evaluation_session(t_a.name, s.name, r.name, "_KT_ES060_E2")
		b = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": "_KT_ES060_B2",
				"tender": t_b.name,
				"supplier": "ES060-SUP",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)
		doc = self._declaration(e.name, related_bid_submission=b.name)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_review_requires_both_reviewer_and_date(self):
		_, _, _, e = self._minimal_chain("3")
		doc = self._declaration(e.name, reviewed_by=frappe.session.user)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
