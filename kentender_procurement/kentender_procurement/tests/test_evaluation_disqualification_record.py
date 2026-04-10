# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-063: Evaluation Disqualification Record."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
EDR = "Evaluation Disqualification Record"
EX = "Exception Record"
BCP = "Budget Control Period"


def _cleanup_es063():
	es_names = frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES063_%")}, pluck="name") or []
	for es_name in es_names:
		for row in frappe.get_all(EDR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EDR, row, force=True, ignore_permissions=True)
	for es_name in es_names:
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES063_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES063_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES063_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES063_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES063_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	if frappe.db.exists(EX, "_KT_ES063_EX"):
		frappe.delete_doc(EX, "_KT_ES063_EX", force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES063_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES063_PE"})


class TestEvaluationDisqualificationRecord063(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es063)
		self.entity = _make_entity("_KT_ES063_PE").insert()
		self.period = _bcp("_KT_ES063_BCP", self.entity.name).insert()
		self.exception = frappe.get_doc(
			{
				"doctype": EX,
				"name": "_KT_ES063_EX",
				"exception_type": "Other",
				"severity": "Medium",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"triggered_by": frappe.session.user,
				"justification": "ES063 test exception for disqualification record.",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es063)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES063 tender",
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
		t = self._tender(f"_KT_ES063_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES063_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES063_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES063_E{suffix}")
		return t, s, r, e

	def _stage(self, evaluation_session_name: str, stage_order: int = 1, **extra):
		kw = {
			"doctype": EST,
			"evaluation_session": evaluation_session_name,
			"stage_type": "Technical Evaluation",
			"stage_order": stage_order,
			"status": "Draft",
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

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

	def _disqualification(self, evaluation_session, evaluation_stage, bid_submission, supplier: str, **kw):
		base = {
			"doctype": EDR,
			"evaluation_session": evaluation_session,
			"evaluation_stage": evaluation_stage,
			"bid_submission": bid_submission,
			"supplier": supplier,
			"disqualification_reason_type": "Technical Non-Compliance",
			"reason_details": "ES063 test disqualification details.",
			"status": "Draft",
			"exception_record": self.exception.name,
		}
		base.update(kw)
		return frappe.get_doc(base)

	def test_valid_disqualification_create(self):
		_, _, _, e = self._minimal_chain("1")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES063_B1", "ES063-SUP-1")
		doc = self._disqualification(
			e.name,
			st.name,
			b.name,
			"ES063-SUP-1",
			decided_by_user=frappe.session.user,
			decided_on=now_datetime(),
		).insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		self.assertIn("Draft", doc.display_label or "")

	def test_stage_wrong_session_blocked(self):
		_, _, _, e1 = self._minimal_chain("2A")
		_, _, _, e2 = self._minimal_chain("2B")
		st2 = self._stage(e2.name, 1)
		b = self._bid(e1.tender, "_KT_ES063_B2", "ES063-SUP-2")
		doc = self._disqualification(e1.name, st2.name, b.name, "ES063-SUP-2")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_bid_wrong_tender_blocked(self):
		t_a = self._tender("_KT_ES063_T3A")
		t_b = self._tender("_KT_ES063_T3B")
		s = self._opening_session(t_a.name, "_KT_ES063_S3")
		r = self._register(t_a.name, s.name, "_KT_ES063_R3")
		e = self._evaluation_session(t_a.name, s.name, r.name, "_KT_ES063_E3")
		st = self._stage(e.name, 1)
		b = self._bid(t_b.name, "_KT_ES063_B3", "ES063-SUP-3")
		doc = self._disqualification(e.name, st.name, b.name, "ES063-SUP-3")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_supplier_mismatch_blocked(self):
		_, _, _, e = self._minimal_chain("4")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES063_B4", "ES063-SUP-4A")
		doc = self._disqualification(e.name, st.name, b.name, "ES063-SUP-4B")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_decision_requires_user_and_date(self):
		_, _, _, e = self._minimal_chain("5")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES063_B5", "ES063-SUP-5")
		doc = self._disqualification(e.name, st.name, b.name, "ES063-SUP-5", decided_by_user=frappe.session.user)
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)

	def test_invalid_exception_record_blocked(self):
		_, _, _, e = self._minimal_chain("6")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES063_B6", "ES063-SUP-6")
		doc = self._disqualification(e.name, st.name, b.name, "ES063-SUP-6", exception_record="nonexistent-ex-063-xyz")
		self.assertRaises(frappe.ValidationError, doc.insert, ignore_permissions=True)
