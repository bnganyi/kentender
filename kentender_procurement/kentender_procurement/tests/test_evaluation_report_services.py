# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-071: Evaluation report generation and submission."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE

from kentender_procurement.services.evaluation_aggregation import aggregate_evaluation_results
from kentender_procurement.services.evaluation_report_services import (
	generate_evaluation_report,
	return_evaluation_for_revision,
	submit_evaluation_report,
)

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
EAR = "Evaluation Aggregation Result"
ERPT = "Evaluation Report"
EASR = "Evaluation Approval Submission Record"
BCP = "Budget Control Period"


def _cleanup_es071():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES071_%")}, pluck="name") or []:
		for row in frappe.get_all(EASR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.db.delete(EASR, {"name": row})
		for row in frappe.get_all(ERPT, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": ERPT, "target_docname": row})
			frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(EAR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EAR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(ER, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ER, row, force=True, ignore_permissions=True)
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES071_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES071_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES071_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES071_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES071_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES071_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES071_PE"})


class TestEvaluationReportServices071(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es071)
		self.entity = _make_entity("_KT_ES071_PE").insert()
		self.period = _bcp("_KT_ES071_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es071)
		super().tearDown()

	def _chain_and_aggregate(self):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_ES071_T1",
				"business_id": "_KT_ES071_T1-BIZ",
				"title": "ES071",
				"tender_number": "_KT_ES071_T1-TN",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		s = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": "_KT_ES071_S1",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_ES071_R1",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		e = frappe.get_doc(
			{
				"doctype": ES,
				"business_id": "_KT_ES071_E1",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"opening_session": s.name,
				"opening_register": r.name,
				"evaluation_mode": "Two Envelope",
				"conflict_clearance_status": "Pending",
			}
		).insert(ignore_permissions=True)
		st = frappe.get_doc(
			{
				"doctype": EST,
				"evaluation_session": e.name,
				"stage_type": "Technical Evaluation",
				"stage_order": 1,
				"status": "Draft",
				"is_scoring_stage": 1,
			}
		).insert(ignore_permissions=True)
		b1 = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": "_KT_ES071_B1",
				"tender": t.name,
				"supplier": "ES071-S1",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
				"quoted_total_amount": 1000,
			}
		).insert(ignore_permissions=True)
		b2 = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": "_KT_ES071_B2",
				"tender": t.name,
				"supplier": "ES071-S2",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
				"quoted_total_amount": 2000,
			}
		).insert(ignore_permissions=True)
		for bid, sup, bid_id, sc in (
			(b1, "ES071-S1", "_KT_ES071_ER1", 80.0),
			(b2, "ES071-S2", "_KT_ES071_ER2", 50.0),
		):
			frappe.get_doc(
				{
					"doctype": ER,
					"business_id": bid_id,
					"evaluation_session": e.name,
					"evaluation_stage": st.name,
					"bid_submission": bid.name,
					"evaluator_user": frappe.session.user,
					"supplier": sup,
					"status": "Locked",
					"pass_fail_result": "Not Applicable",
					"total_stage_score": sc,
					"submitted_on": "2026-04-10 12:00:00",
					"locked_on": "2026-04-10 12:00:00",
				}
			).insert(ignore_permissions=True)
		aggregate_evaluation_results(e.name)
		return e, b1, b2

	def test_generate_blocked_without_aggregation(self):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": "_KT_ES071_TX",
				"business_id": "_KT_ES071_TX-BIZ",
				"title": "ES071x",
				"tender_number": "TX",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": self.entity.name,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		s = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": "_KT_ES071_SX",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": "_KT_ES071_RX",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		e = frappe.get_doc(
			{
				"doctype": ES,
				"business_id": "_KT_ES071_EX",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
				"opening_session": s.name,
				"opening_register": r.name,
				"evaluation_mode": "Two Envelope",
				"conflict_clearance_status": "Pending",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			generate_evaluation_report(e.name)

	def test_generate_submit_return_flow(self):
		e, b1, _b2 = self._chain_and_aggregate()
		g = generate_evaluation_report(e.name, business_id="_KT_ES071_ERPT")
		self.assertTrue(g["name"])
		doc = frappe.get_doc(ERPT, g["name"])
		self.assertEqual((doc.recommended_bid_submission or "").strip(), b1.name)
		su = submit_evaluation_report(g["name"])
		self.assertEqual(su["status"], "Locked")
		self.assertTrue(su["locked_hash"])
		self.assertTrue(
			frappe.db.exists(
				AUDIT_EVENT_DOCTYPE,
				{"event_type": "evaluation.report.submitted", "target_docname": g["name"]},
			)
		)
		ret = return_evaluation_for_revision(g["name"], comments="fix narrative")
		self.assertEqual(ret["status"], "In Progress")
		self.assertIsNone(frappe.db.get_value(ERPT, g["name"], "locked_hash"))
