# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-057: Evaluation Session."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
BCP = "Budget Control Period"


def _cleanup_es057():
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES057_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES057_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES057_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES057_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES057_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES057_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES057_PE"})


class TestEvaluationSession057(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es057)
		self.entity = _make_entity("_KT_ES057_PE").insert()
		self.period = _bcp("_KT_ES057_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es057)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES057 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _session(self, tender_name: str, business_id: str):
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

	def _evaluation_session_doc(self, tender_name: str, session_name: str, register_name: str, business_id: str):
		return frappe.get_doc(
			{
				"doctype": ES,
				"business_id": business_id,
				"tender": tender_name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"opening_session": session_name,
				"opening_register": register_name,
				"evaluation_mode": "Two Envelope",
				"conflict_clearance_status": "Pending",
			}
		)

	def test_valid_create_with_opening_context(self):
		t = self._tender("_KT_ES057_T1")
		s = self._session(t.name, "_KT_ES057_S1")
		r = self._register(t.name, s.name, "_KT_ES057_R1")
		doc = self._evaluation_session_doc(t.name, s.name, r.name, "_KT_ES057_E1").insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("_KT_ES057_E1", doc.display_label or "")

	def test_blocks_missing_opening_session(self):
		t = self._tender("_KT_ES057_T2")
		s = self._session(t.name, "_KT_ES057_S2")
		r = self._register(t.name, s.name, "_KT_ES057_R2")
		d = self._evaluation_session_doc(t.name, s.name, r.name, "_KT_ES057_E2")
		d.opening_session = None
		self.assertRaises(frappe.ValidationError, d.insert, ignore_permissions=True)

	def test_blocks_missing_opening_register(self):
		t = self._tender("_KT_ES057_T3")
		s = self._session(t.name, "_KT_ES057_S3")
		r = self._register(t.name, s.name, "_KT_ES057_R3")
		d = self._evaluation_session_doc(t.name, s.name, r.name, "_KT_ES057_E3")
		d.opening_register = None
		self.assertRaises(frappe.ValidationError, d.insert, ignore_permissions=True)

	def test_blocks_register_not_linked_to_session(self):
		t = self._tender("_KT_ES057_T4")
		s_a = self._session(t.name, "_KT_ES057_S4A")
		r = self._register(t.name, s_a.name, "_KT_ES057_R4")
		s_a.workflow_state = "Completed"
		s_a.status = "Completed"
		s_a.save(ignore_permissions=True)
		s_b = self._session(t.name, "_KT_ES057_S4B")
		d = self._evaluation_session_doc(t.name, s_b.name, r.name, "_KT_ES057_E4")
		self.assertRaises(frappe.ValidationError, d.insert, ignore_permissions=True)

	def test_blocks_session_wrong_tender(self):
		t_a = self._tender("_KT_ES057_T5A")
		t_b = self._tender("_KT_ES057_T5B")
		s = self._session(t_a.name, "_KT_ES057_S5")
		r = self._register(t_a.name, s.name, "_KT_ES057_R5")
		d = self._evaluation_session_doc(t_b.name, s.name, r.name, "_KT_ES057_E5")
		self.assertRaises(frappe.ValidationError, d.insert, ignore_permissions=True)

	def test_recommended_bid_wrong_tender_blocked(self):
		t_a = self._tender("_KT_ES057_T6A")
		t_b = self._tender("_KT_ES057_T6B")
		s = self._session(t_a.name, "_KT_ES057_S6")
		r = self._register(t_a.name, s.name, "_KT_ES057_R6")
		b = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": "_KT_ES057_B6",
				"tender": t_b.name,
				"supplier": "ES057-SUP",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)
		d = self._evaluation_session_doc(t_a.name, s.name, r.name, "_KT_ES057_E6")
		d.recommended_bid_submission = b.name
		self.assertRaises(frappe.ValidationError, d.insert, ignore_permissions=True)
