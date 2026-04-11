# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-069: Evaluation scoring and stage progression services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.uat.kt_test_local_users import delete_kt_test_local_user
from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE

from kentender_procurement.services.evaluator_access import submit_conflict_declaration
from kentender_procurement.services.evaluation_scoring import (
	EVT_RECORD_SUBMITTED,
	complete_evaluation_stage,
	confirm_disqualification,
	propose_disqualification,
	start_evaluation_stage,
	submit_evaluation_record,
)

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
EA = "Evaluator Assignment"
COI = "Conflict of Interest Declaration"
EDR = "Evaluation Disqualification Record"
EX = "Exception Record"
BCP = "Budget Control Period"


def _ensure_es069_second_user() -> str:
	email = "_kt_es069_b@test.local"
	if frappe.db.exists("User", email):
		return email
	u = frappe.new_doc("User")
	u.email = email
	u.first_name = "ES069"
	u.send_welcome_email = 0
	u.enabled = 1
	u.user_type = "System User"
	u.insert(ignore_permissions=True)
	u.add_roles("System Manager")
	return email


def _delete_audit_for_session_docs(session_names: list[str]) -> None:
	for es_name in session_names:
		for dt in (EDR, ER, EST):
			for n in frappe.get_all(dt, filters={"evaluation_session": es_name}, pluck="name") or []:
				frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": dt, "target_docname": n})


def _cleanup_es069():
	es_names = frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES069_%")}, pluck="name") or []
	_delete_audit_for_session_docs(list(es_names))
	for es_name in es_names:
		for row in frappe.get_all(EDR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EDR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(ER, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ER, row, force=True, ignore_permissions=True)
	for es_name in es_names:
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
		for row in frappe.get_all(COI, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(COI, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(EA, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EA, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES069_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES069_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES069_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES069_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES069_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	if frappe.db.exists(EX, "_KT_ES069_EX"):
		frappe.delete_doc(EX, "_KT_ES069_EX", force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES069_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES069_PE"})
	delete_kt_test_local_user("_kt_es069_b@test.local")


class TestEvaluationScoring069(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es069)
		self.entity = _make_entity("_KT_ES069_PE").insert()
		self.period = _bcp("_KT_ES069_BCP", self.entity.name).insert()
		self.exception = frappe.get_doc(
			{
				"doctype": EX,
				"name": "_KT_ES069_EX",
				"exception_type": "Other",
				"severity": "Medium",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"triggered_by": frappe.session.user,
				"justification": "ES069 test exception for disqualification.",
			}
		).insert(ignore_permissions=True)
		self.second_user = _ensure_es069_second_user()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es069)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES069 tender",
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
		t = self._tender(f"_KT_ES069_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES069_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES069_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES069_E{suffix}")
		return t, s, r, e

	def _assignment(self, evaluation_session_name: str, evaluator_user: str | None = None, **extra):
		kw = {
			"doctype": EA,
			"evaluation_session": evaluation_session_name,
			"evaluator_user": evaluator_user or frappe.session.user,
			"committee_role": "Member",
			"assignment_status": "Active",
		}
		kw.update(extra)
		return frappe.get_doc(kw).insert(ignore_permissions=True)

	def _cleared_evaluator(self, e):
		self._assignment(e.name)
		submit_conflict_declaration(
			e.name,
			frappe.session.user,
			declaration_status="Declared No Conflict",
		)

	def _stage(self, evaluation_session_name: str, stage_order: int = 1, **extra):
		kw = {
			"doctype": EST,
			"evaluation_session": evaluation_session_name,
			"stage_type": "Technical Evaluation",
			"stage_order": stage_order,
			"status": "Draft",
			"is_scoring_stage": 1,
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

	def _evaluation_record(self, **kw):
		base = {
			"doctype": ER,
			"business_id": kw.pop("business_id"),
			"evaluation_session": kw.pop("evaluation_session"),
			"evaluation_stage": kw.pop("evaluation_stage"),
			"bid_submission": kw.pop("bid_submission"),
			"evaluator_user": kw.pop("evaluator_user", frappe.session.user),
			"supplier": kw.pop("supplier"),
			"status": kw.pop("status", "Draft"),
			"pass_fail_result": kw.pop("pass_fail_result", "Not Applicable"),
		}
		base.update(kw)
		return frappe.get_doc(base).insert(ignore_permissions=True)

	def test_submit_evaluation_record_locks_and_audits(self):
		_, _, _, e = self._minimal_chain("1")
		self._cleared_evaluator(e)
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES069_B1", "ES069-SUP-1")
		rec = self._evaluation_record(
			business_id="_KT_ES069_ER1",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES069-SUP-1",
		)
		out = submit_evaluation_record(rec.name)
		self.assertEqual(out["status"], "Locked")
		doc = frappe.get_doc(ER, rec.name)
		self.assertTrue(doc.submitted_on)
		self.assertTrue(doc.locked_on)
		self.assertTrue(
			frappe.db.exists(
				AUDIT_EVENT_DOCTYPE,
				{"event_type": EVT_RECORD_SUBMITTED, "target_doctype": ER, "target_docname": rec.name},
			)
		)

	def test_submit_denied_without_assignment(self):
		_, _, _, e = self._minimal_chain("2")
		submit_conflict_declaration(
			e.name,
			frappe.session.user,
			declaration_status="Declared No Conflict",
		)
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES069_B2", "ES069-SUP-2")
		rec = self._evaluation_record(
			business_id="_KT_ES069_ER2",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES069-SUP-2",
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			submit_evaluation_record(rec.name)
		self.assertIn("assigned", str(ctx.exception).lower())

	def test_submit_denied_wrong_evaluator_user(self):
		_, _, _, e = self._minimal_chain("3")
		self._assignment(e.name, evaluator_user=self.second_user)
		submit_conflict_declaration(
			e.name,
			self.second_user,
			declaration_status="Declared No Conflict",
		)
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES069_B3", "ES069-SUP-3")
		rec = self._evaluation_record(
			business_id="_KT_ES069_ER3",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES069-SUP-3",
			evaluator_user=self.second_user,
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			submit_evaluation_record(rec.name)
		self.assertIn("evaluator", str(ctx.exception).lower())

	def test_start_stage_blocked_when_prior_stage_draft(self):
		_, _, _, e = self._minimal_chain("4")
		self._cleared_evaluator(e)
		s1 = self._stage(e.name, 1, is_scoring_stage=0)
		s2 = self._stage(e.name, 2, is_scoring_stage=0)
		with self.assertRaises(frappe.ValidationError) as ctx:
			start_evaluation_stage(s2.name)
		self.assertIn("earlier", str(ctx.exception).lower())
		self.assertTrue(s1.name)

	def test_complete_scoring_stage_blocked_with_draft_record(self):
		_, _, _, e = self._minimal_chain("5")
		self._cleared_evaluator(e)
		st = self._stage(e.name, 1, is_scoring_stage=1)
		start_evaluation_stage(st.name)
		b = self._bid(e.tender, "_KT_ES069_B5", "ES069-SUP-5")
		self._evaluation_record(
			business_id="_KT_ES069_ER5",
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES069-SUP-5",
			status="Draft",
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			complete_evaluation_stage(st.name)
		self.assertIn("submitted", str(ctx.exception).lower())

	def test_propose_and_confirm_disqualification(self):
		_, _, _, e = self._minimal_chain("6")
		self._cleared_evaluator(e)
		st = self._stage(e.name, 1, is_scoring_stage=0)
		b = self._bid(e.tender, "_KT_ES069_B6", "ES069-SUP-6")
		out = propose_disqualification(
			evaluation_session=e.name,
			evaluation_stage=st.name,
			bid_submission=b.name,
			supplier="ES069-SUP-6",
			disqualification_reason_type="Technical Non-Compliance",
			reason_details="ES069 propose DQ",
			exception_record=self.exception.name,
		)
		self.assertEqual(out["status"], "Proposed")
		c = confirm_disqualification(out["name"])
		self.assertEqual(c["status"], "Confirmed")
		doc = frappe.get_doc(EDR, out["name"])
		self.assertTrue(doc.decided_on)
		self.assertTrue(doc.decided_by_user)

	def test_confirm_disqualification_blocked_from_draft(self):
		_, _, _, e = self._minimal_chain("7")
		self._cleared_evaluator(e)
		st = self._stage(e.name, 1, is_scoring_stage=0)
		b = self._bid(e.tender, "_KT_ES069_B7", "ES069-SUP-7")
		d = frappe.get_doc(
			{
				"doctype": EDR,
				"evaluation_session": e.name,
				"evaluation_stage": st.name,
				"bid_submission": b.name,
				"supplier": "ES069-SUP-7",
				"disqualification_reason_type": "Other",
				"reason_details": "draft dq",
				"status": "Draft",
				"exception_record": self.exception.name,
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			confirm_disqualification(d.name)
