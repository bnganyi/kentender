# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-062: Evaluation Score Line."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
TCR = "Tender Criteria"
BCP = "Budget Control Period"


def _cleanup_es062():
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES062_%")}, pluck="name") or []:
		for row in frappe.get_all(ER, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(ER, row, force=True, ignore_permissions=True)
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES062_%")}, pluck="name") or []:
		for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
			frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", "_KT_ES062_%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", "_KT_ES062_%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(TCR, filters={"tender": ("like", "_KT_ES062_%")}, pluck="name") or []:
		frappe.delete_doc(TCR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", "_KT_ES062_%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", "_KT_ES062_%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", "_KT_ES062_%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", "_KT_ES062_%")})
	frappe.db.delete("Procuring Entity", {"entity_code": "_KT_ES062_PE"})


class TestEvaluationScoreLine062(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_es062)
		self.entity = _make_entity("_KT_ES062_PE").insert()
		self.period = _bcp("_KT_ES062_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_es062)
		super().tearDown()

	def _tender(self, name: str):
		return frappe.get_doc(
			{
				"doctype": TENDER,
				"name": name,
				"business_id": f"{name}-BIZ",
				"title": "ES062 tender",
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
		t = self._tender(f"_KT_ES062_T{suffix}")
		s = self._opening_session(t.name, f"_KT_ES062_S{suffix}")
		r = self._register(t.name, s.name, f"_KT_ES062_R{suffix}")
		e = self._evaluation_session(t.name, s.name, r.name, f"_KT_ES062_E{suffix}")
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

	def _criteria_numeric(self, tender_name: str, code: str = "ES062-N1"):
		return frappe.get_doc(
			{
				"doctype": TCR,
				"tender": tender_name,
				"criteria_type": "Technical",
				"criteria_code": code,
				"criteria_title": "Numeric criterion",
				"score_type": "Numeric",
				"max_score": 100,
				"weight_percentage": 40,
				"minimum_pass_mark": 40,
				"display_order": 1,
				"applies_to_stage": "Technical Evaluation",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _criteria_pass_fail(self, tender_name: str, code: str = "ES062-PF1"):
		return frappe.get_doc(
			{
				"doctype": TCR,
				"tender": tender_name,
				"criteria_type": "Mandatory",
				"criteria_code": code,
				"criteria_title": "Pass fail criterion",
				"score_type": "Pass/Fail",
				"weight_percentage": 10,
				"minimum_pass_mark": 0.5,
				"display_order": 2,
				"applies_to_stage": "Preliminary",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

	def _base_record(self, e, st, b):
		return frappe.get_doc(
			{
				"doctype": ER,
				"business_id": "_KT_ES062_REC",
				"evaluation_session": e.name,
				"evaluation_stage": st.name,
				"bid_submission": b.name,
				"evaluator_user": frappe.session.user,
				"supplier": "ES062-SUP",
				"status": "Draft",
				"pass_fail_result": "Pending",
			}
		)

	def _numeric_line_dict(self, tc):
		return {
			"tender_criteria": tc.name,
			"criteria_type": tc.criteria_type,
			"criteria_title": tc.criteria_title,
			"score_value": 50,
			"pass_fail_result": "Not Applicable",
			"max_score": tc.max_score,
			"weight_percentage": tc.weight_percentage,
		}

	def _pass_fail_line_dict(self, tc):
		return {
			"tender_criteria": tc.name,
			"criteria_type": tc.criteria_type,
			"criteria_title": tc.criteria_title,
			"pass_fail_result": "Pass",
			"max_score": tc.max_score,
			"weight_percentage": tc.weight_percentage,
		}

	def test_numeric_score_line_valid(self):
		_, _, _, e = self._minimal_chain("1")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES062_B1", "ES062-SUP")
		tc = self._criteria_numeric(e.tender)
		rec = self._base_record(e, st, b)
		rec.business_id = "_KT_ES062_ER1"
		rec.append("score_lines", self._numeric_line_dict(tc))
		rec.insert(ignore_permissions=True)
		line = rec.score_lines[0]
		self.assertAlmostEqual(float(line.weighted_score or 0), 20.0, places=5)

	def test_numeric_score_above_max_blocked(self):
		_, _, _, e = self._minimal_chain("2")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES062_B2", "ES062-SUP")
		tc = self._criteria_numeric(e.tender)
		rec = self._base_record(e, st, b)
		rec.business_id = "_KT_ES062_ER2"
		row = self._numeric_line_dict(tc)
		row["score_value"] = 150
		rec.append("score_lines", row)
		self.assertRaises(frappe.ValidationError, rec.insert, ignore_permissions=True)

	def test_pass_fail_line_valid(self):
		_, _, _, e = self._minimal_chain("3")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES062_B3", "ES062-SUP")
		tc = self._criteria_pass_fail(e.tender)
		rec = self._base_record(e, st, b)
		rec.business_id = "_KT_ES062_ER3"
		rec.append("score_lines", self._pass_fail_line_dict(tc))
		rec.insert(ignore_permissions=True)
		self.assertAlmostEqual(float(rec.score_lines[0].weighted_score or 0), 0.0, places=5)

	def test_criteria_wrong_tender_blocked(self):
		_, _, _, e_a = self._minimal_chain("4A")
		t_b = self._tender("_KT_ES062_T4B")
		st = self._stage(e_a.name, 1)
		b = self._bid(e_a.tender, "_KT_ES062_B4", "ES062-SUP")
		tc = self._criteria_numeric(t_b.name, code="ES062-WRONG")
		rec = self._base_record(e_a, st, b)
		rec.business_id = "_KT_ES062_ER4"
		rec.append("score_lines", self._numeric_line_dict(tc))
		self.assertRaises(frappe.ValidationError, rec.insert, ignore_permissions=True)

	def test_duplicate_criteria_lines_blocked(self):
		_, _, _, e = self._minimal_chain("5")
		st = self._stage(e.name, 1)
		b = self._bid(e.tender, "_KT_ES062_B5", "ES062-SUP")
		tc = self._criteria_numeric(e.tender)
		rec = self._base_record(e, st, b)
		rec.business_id = "_KT_ES062_ER5"
		row = self._numeric_line_dict(tc)
		rec.append("score_lines", row)
		rec.append("score_lines", dict(row))
		self.assertRaises(frappe.ValidationError, rec.insert, ignore_permissions=True)
