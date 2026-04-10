# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-067: initialize evaluation from completed opening."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.evaluation_initialization import initialize_evaluation_session
from kentender_procurement.services.opening_execution import execute_bid_opening

TENDER = "Tender"
BS = "Bid Submission"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BOEL = "Bid Opening Event Log"
ES = "Evaluation Session"
EST = "Evaluation Stage"
BCP = "Budget Control Period"


def _cleanup_es067():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES067_%")}, pluck="name") or []:
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
		frappe.delete_doc(ES, es_name, force=True, ignore_permissions=True)
	for sn in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES067_%")}, pluck="name") or []:
		frappe.db.delete(BOEL, {"bid_opening_session": sn})
	for sn in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES067_%")}, pluck="name") or []:
		for rn in frappe.get_all(BOR, filters={"bid_opening_session": sn}, pluck="name") or []:
			frappe.delete_doc(BOR, rn, force=True, ignore_permissions=True)
	for row in frappe.get_all(BS, filters={"business_id": ("like", "_KT_ES067_%")}, pluck="name") or []:
		frappe.delete_doc(BS, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES067_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES067_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES067_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES067_PE"})


class TestEvaluationInitialization067(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es067)
		self.entity = _make_entity("_KT_ES067_PE").insert()
		self.period = _bcp("_KT_ES067_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es067)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES067 tender",
				"tender_number": f"{name}-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)

	def _published_tender_past_deadline(self, name: str):
		t = self._tender(name)
		past = add_days(now_datetime(), -1)
		frappe.db.set_value(
			TENDER,
			t.name,
			{
				"workflow_state": "Published",
				"status": "Active",
				"approval_status": "Published",
				"submission_status": "Open",
				"submission_deadline": past,
				"opening_datetime": add_days(now_datetime(), 1),
			},
			update_modified=False,
		)
		return t

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

	def _submitted_bid(self, tender_name: str, business_id: str):
		b = frappe.get_doc(
			{
				"doctype": BS,
				"business_id": business_id,
				"tender": tender_name,
				"supplier": "ES067-SUP",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			BS,
			b.name,
			{
				"workflow_state": "Submitted",
				"status": "Submitted",
				"is_final_submission": 1,
				"active_submission_flag": 1,
				"sealed_status": "Sealed",
				"submitted_on": now_datetime(),
			},
			update_modified=False,
		)
		return b

	def test_initialize_success(self):
		t = self._published_tender_past_deadline("_KT_ES067_T1")
		s = self._session(t.name, "_KT_ES067_S1")
		self._submitted_bid(t.name, "_KT_ES067_B1")
		ex = execute_bid_opening(s.name, actor_user="Administrator")
		out = initialize_evaluation_session(
			opening_session_id=s.name,
			business_id="_KT_ES067_ES1",
			evaluation_mode="Two Envelope",
		)
		self.assertTrue(out.get("evaluation_session"))
		self.assertEqual(out.get("candidate_bid_count"), 1)
		self.assertEqual(len(out.get("stages") or []), 3)
		es = frappe.get_doc(ES, out["evaluation_session"])
		self.assertEqual(es.opening_session, s.name)
		self.assertEqual(es.opening_register, ex.get("register"))
		self.assertEqual(es.candidate_bid_count, 1)
		types = [
			frappe.db.get_value(EST, n, "stage_type") for n in (out.get("stages") or [])
		]
		self.assertEqual(
			types,
			["Preliminary Examination", "Technical Evaluation", "Financial Evaluation"],
		)

	def test_blocks_before_opening_complete(self):
		t = self._published_tender_past_deadline("_KT_ES067_T2")
		s = self._session(t.name, "_KT_ES067_S2")
		reg = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_ES067_RG2",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Generated",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			BOS,
			s.name,
			{
				"opening_register": reg.name,
				"register_locked": 0,
				"is_atomic_opening_complete": 0,
			},
			update_modified=False,
		)
		self.assertRaises(
			frappe.ValidationError,
			initialize_evaluation_session,
			opening_session_id=s.name,
			business_id="_KT_ES067_ES2",
		)

	def test_duplicate_opening_session_blocked(self):
		t = self._published_tender_past_deadline("_KT_ES067_T3")
		s = self._session(t.name, "_KT_ES067_S3")
		self._submitted_bid(t.name, "_KT_ES067_B3")
		execute_bid_opening(s.name, actor_user="Administrator")
		initialize_evaluation_session(opening_session_id=s.name, business_id="_KT_ES067_ES3A")
		self.assertRaises(
			frappe.ValidationError,
			initialize_evaluation_session,
			opening_session_id=s.name,
			business_id="_KT_ES067_ES3B",
		)

	def test_initialize_by_tender_id_when_single_completed_session(self):
		t = self._published_tender_past_deadline("_KT_ES067_T4")
		s = self._session(t.name, "_KT_ES067_S4")
		self._submitted_bid(t.name, "_KT_ES067_B4")
		execute_bid_opening(s.name, actor_user="Administrator")
		out = initialize_evaluation_session(tender_id=t.name, business_id="_KT_ES067_ES4")
		self.assertEqual(out.get("opening_session"), s.name)
		self.assertEqual(len(out.get("stages") or []), 3)
