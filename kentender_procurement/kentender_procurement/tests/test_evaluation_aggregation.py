# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-070: Evaluation aggregation and ranking services."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.evaluation_aggregation import (
	aggregate_evaluation_results,
	aggregate_technical_scores,
	calculate_final_ranking,
	calculate_financial_score,
)

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
EAR = "Evaluation Aggregation Result"
EDR = "Evaluation Disqualification Record"
EX = "Exception Record"
BCP = "Budget Control Period"


def _cleanup_es070():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES070_%")}, pluck="name") or []:
		for row in frappe.get_all(EDR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EDR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(EAR, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EAR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(ER, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ER, row, force=True, ignore_permissions=True)
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES070_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES070_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES070_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES070_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES070_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	if frappe.db.exists(EX, "_KT_ES070_EX"):
		frappe.delete_doc(EX, "_KT_ES070_EX", force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES070_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES070_PE"})


class TestEvaluationAggregation070(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es070)
		self.entity = _make_entity("_KT_ES070_PE").insert()
		self.period = _bcp("_KT_ES070_BCP", self.entity.name).insert()
		self.exception = frappe.get_doc(
			{
				"doctype": EX,
				"name": "_KT_ES070_EX",
				"exception_type": "Other",
				"severity": "Medium",
				"approval_status": "Draft",
				"procuring_entity": self.entity.name,
				"triggered_by": frappe.session.user,
				"justification": "ES070 test exception.",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es070)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES070 tender",
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
		t = self._tender(f"_KT_ES070_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES070_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES070_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES070_E{suffix}")
		return t, s, r, e

	def _stage(self, evaluation_session_name: str, stage_type: str, stage_order: int, **extra):
		kw = {
			"doctype": EST,
			"evaluation_session": evaluation_session_name,
			"stage_type": stage_type,
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

	def _locked_record(self, es_name, stage_name, bid_name, supplier: str, business_id: str, total: float):
		return frappe.get_doc(
			{
				"doctype": ER,
				"business_id": business_id,
				"evaluation_session": es_name,
				"evaluation_stage": stage_name,
				"bid_submission": bid_name,
				"evaluator_user": frappe.session.user,
				"supplier": supplier,
				"status": "Locked",
				"pass_fail_result": "Not Applicable",
				"total_stage_score": total,
				"submitted_on": "2026-04-10 12:00:00",
				"locked_on": "2026-04-10 12:00:00",
			}
		).insert(ignore_permissions=True)

	def test_aggregate_evaluation_results_ranks_bids(self):
		_, _, _, e = self._minimal_chain("1")
		st = self._stage(e.name, "Technical Evaluation", 1)
		st_fin = self._stage(e.name, "Financial Evaluation", 2, is_scoring_stage=1)
		b_hi = self._bid(e.tender, "_KT_ES070_B1A", "ES070-SUP-A")
		b_lo = self._bid(e.tender, "_KT_ES070_B1B", "ES070-SUP-B")
		self._locked_record(e.name, st.name, b_hi.name, "ES070-SUP-A", "_KT_ES070_ER_A", 90.0)
		self._locked_record(e.name, st.name, b_lo.name, "ES070-SUP-B", "_KT_ES070_ER_B", 50.0)
		self._locked_record(e.name, st_fin.name, b_hi.name, "ES070-SUP-A", "_KT_ES070_ER_AF", 80.0)
		self._locked_record(e.name, st_fin.name, b_lo.name, "ES070-SUP-B", "_KT_ES070_ER_BF", 40.0)

		out = aggregate_evaluation_results(e.name, technical_weight=0.7, financial_weight=0.3)
		self.assertEqual(out["status"], "Complete")
		rows = {r.bid_submission: r for r in frappe.get_all(EAR, filters={"evaluation_session": e.name}, fields=["*"])}
		self.assertEqual(rows[b_hi.name].ranking_position, 1)
		self.assertEqual(rows[b_lo.name].ranking_position, 2)
		self.assertEqual(rows[b_hi.name].calculation_status, "Complete")
		self.assertAlmostEqual(float(rows[b_hi.name].technical_score_average), 90.0)
		self.assertAlmostEqual(float(rows[b_hi.name].financial_score), 80.0)

	def test_disqualified_bid_not_ranked(self):
		_, _, _, e = self._minimal_chain("2")
		st = self._stage(e.name, "Technical Evaluation", 1)
		b1 = self._bid(e.tender, "_KT_ES070_B2A", "ES070-S2-A")
		b2 = self._bid(e.tender, "_KT_ES070_B2B", "ES070-S2-B")
		self._locked_record(e.name, st.name, b1.name, "ES070-S2-A", "_KT_ES070_ER2A", 70.0)
		self._locked_record(e.name, st.name, b2.name, "ES070-S2-B", "_KT_ES070_ER2B", 60.0)
		frappe.get_doc(
			{
				"doctype": EDR,
				"evaluation_session": e.name,
				"evaluation_stage": st.name,
				"bid_submission": b1.name,
				"supplier": "ES070-S2-A",
				"disqualification_reason_type": "Other",
				"reason_details": "dq test",
				"status": "Confirmed",
				"exception_record": self.exception.name,
				"decided_by_user": frappe.session.user,
				"decided_on": "2026-04-10 14:00:00",
			}
		).insert(ignore_permissions=True)

		aggregate_evaluation_results(e.name)
		rows = {r.bid_submission: r for r in frappe.get_all(EAR, filters={"evaluation_session": e.name}, fields=["*"])}
		self.assertEqual(rows[b1.name].preliminary_result, "Disqualified")
		self.assertEqual(rows[b1.name].ranking_position, 0)
		self.assertEqual(rows[b2.name].ranking_position, 1)

	def test_aggregate_technical_and_financial_incremental(self):
		_, _, _, e = self._minimal_chain("3")
		st = self._stage(e.name, "Technical Evaluation", 1)
		b = self._bid(e.tender, "_KT_ES070_B3", "ES070-S3")
		self._locked_record(e.name, st.name, b.name, "ES070-S3", "_KT_ES070_ER3", 40.0)
		self._stage(e.name, "Financial Evaluation", 2, is_scoring_stage=1)
		aggregate_technical_scores(e.name)
		calculate_financial_score(e.name)
		row = frappe.get_all(EAR, filters={"evaluation_session": e.name, "bid_submission": b.name}, fields=["*"])[0]
		self.assertAlmostEqual(float(row.technical_score_average), 40.0)
		# No locked financial-stage records: service leaves financial unset (NULL); ORM may surface as 0.0.
		self.assertTrue(row.financial_score is None or float(row.financial_score or 0) == 0.0)

	def test_calculate_final_ranking_alone(self):
		_, _, _, e = self._minimal_chain("4")
		st = self._stage(e.name, "Technical Evaluation", 1)
		b1 = self._bid(e.tender, "_KT_ES070_B4A", "ES070-S4-A")
		b2 = self._bid(e.tender, "_KT_ES070_B4B", "ES070-S4-B")
		self._locked_record(e.name, st.name, b1.name, "ES070-S4-A", "_KT_ES070_ER4A", 10.0)
		self._locked_record(e.name, st.name, b2.name, "ES070-S4-B", "_KT_ES070_ER4B", 20.0)
		aggregate_technical_scores(e.name)
		for name in frappe.get_all(EAR, filters={"evaluation_session": e.name}, pluck="name"):
			d = frappe.get_doc(EAR, name)
			d.preliminary_result = "Responsive"
			d.combined_score = d.technical_score_average or 0
			frappe.flags.in_evaluation_aggregation_service = True
			try:
				d.save(ignore_permissions=True)
			finally:
				frappe.flags.in_evaluation_aggregation_service = False
		calculate_final_ranking(e.name)
		rows = {r.bid_submission: r for r in frappe.get_all(EAR, filters={"evaluation_session": e.name}, fields=["*"])}
		self.assertEqual(rows[b2.name].ranking_position, 1)
		self.assertEqual(rows[b1.name].ranking_position, 2)
