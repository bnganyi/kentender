# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-112: inspection_result_services — tolerance, record_*, recompute, apply template."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.inspection_result_services import (
	apply_inspection_template,
	evaluate_parameter_tolerance,
	recompute_inspection_result,
	record_checklist_result,
	record_parameter_result,
)

AD = "Award Decision"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Report"
EVAL = "Evaluation Session"
IMT = "Inspection Method Template"
IR = "Inspection Record"
IPL = "Inspection Parameter Line"
ITR = "Inspection Test Result"
PC = "Procurement Contract"
TENDER = "Tender"
PREFIX = "_KT_INSP112"


def _cleanup_112():
	ir_names = frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []
	for irn in ir_names:
		for row in frappe.get_all(ITR, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(ITR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(IPL, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(IPL, row, force=True, ignore_permissions=True)
	for row in ir_names:
		frappe.delete_doc(IR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IMT, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(EVAL, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(EVAL, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	frappe.db.delete("Budget Control Period", {"name": ("like", f"{PREFIX}%")})
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})


class TestInspectionResultServices112(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_112)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()
		if not frappe.db.exists("UOM", "Nos"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_112)
		super().tearDown()

	def _minimal_award_and_pc(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "INSP112",
				"tender_number": f"{PREFIX}_TN{suffix}",
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
				"business_id": f"{PREFIX}_S{suffix}",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": f"{PREFIX}_R{suffix}",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		e = frappe.get_doc(
			{
				"doctype": EVAL,
				"business_id": f"{PREFIX}_E{suffix}",
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
		rep = frappe.get_doc(
			{
				"doctype": ES,
				"business_id": f"{PREFIX}_ER{suffix}",
				"evaluation_session": e.name,
				"tender": t.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		b = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": f"{PREFIX}_B{suffix}",
				"tender": t.name,
				"supplier": f"S-{suffix}",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
				"quoted_total_amount": 5000,
			}
		).insert(ignore_permissions=True)
		ad = frappe.get_doc(
			{
				"doctype": AD,
				"business_id": f"{PREFIX}_AD{suffix}",
				"tender": t.name,
				"evaluation_session": e.name,
				"evaluation_report": rep.name,
				"decision_justification": "112 tests.",
				"recommended_bid_submission": b.name,
				"recommended_supplier": f"S-{suffix}",
				"recommended_amount": 5000,
				"approved_bid_submission": b.name,
				"approved_supplier": f"S-{suffix}",
				"approved_amount": 5000,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		pc = frappe.get_doc(
			{
				"doctype": PC,
				"business_id": f"{PREFIX}_PC{suffix}",
				"contract_title": "112 contract",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-{suffix}",
				"procuring_entity": self.entity.name,
				"contract_value": 5000,
				"currency": self.currency,
				"contract_start_date": getdate(nowdate()),
			}
		).insert(ignore_permissions=True)
		return pc

	def _template(self, code_suffix: str, **extra):
		c = f"{PREFIX}_{code_suffix}"
		row = {
			"doctype": IMT,
			"template_code": c,
			"template_name": "Tpl",
			"inspection_domain": "General",
			"applicable_contract_type": "Goods",
			"inspection_method_type": extra.get("inspection_method_type", "Checklist"),
			"default_pass_logic": "All Mandatory Pass",
			"active": 1,
		}
		row.update({k: v for k, v in extra.items() if k != "inspection_method_type"})
		return frappe.get_doc(row).insert(ignore_permissions=True)

	def _ir(self, pc, suf: str, tpl, **kw):
		return frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IR{suf}",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "112",
				"inspection_method_type": kw.get("inspection_method_type", "Parameter Testing"),
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				**{k: v for k, v in kw.items() if k != "inspection_method_type"},
			}
		).insert(ignore_permissions=True)

	def test_KT_INSP112_tolerance_minmax(self):
		pc = self._minimal_award_and_pc("A")
		tpl = self._template("TPLA")
		ir = self._ir(pc, "A", tpl)
		pl = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "MM",
				"parameter_name": "MinMax",
				"parameter_category": "Dimensional",
				"tolerance_type": "MinMax",
				"expected_min_value": 1.0,
				"expected_max_value": 2.0,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(evaluate_parameter_tolerance(pl.name, observed_numeric=1.5), "Pass")
		self.assertEqual(evaluate_parameter_tolerance(pl.name, observed_numeric=0.5), "Fail")

	def test_KT_INSP112_tolerance_absolute_percent_pass_fail_only_none(self):
		pc = self._minimal_award_and_pc("B")
		tpl = self._template("TPLB")
		ir = self._ir(pc, "B", tpl)
		p_abs = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "A1",
				"parameter_name": "Abs",
				"parameter_category": "Dimensional",
				"tolerance_type": "Absolute",
				"target_value": 10.0,
				"tolerance_value": 1.0,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(evaluate_parameter_tolerance(p_abs.name, observed_numeric=10.5), "Pass")
		self.assertEqual(evaluate_parameter_tolerance(p_abs.name, observed_numeric=12.0), "Fail")
		p_pct = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "P1",
				"parameter_name": "Pct",
				"parameter_category": "Dimensional",
				"tolerance_type": "Percent",
				"target_value": 100.0,
				"tolerance_value": 10.0,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(evaluate_parameter_tolerance(p_pct.name, observed_numeric=95.0), "Pass")
		self.assertEqual(evaluate_parameter_tolerance(p_pct.name, observed_numeric=80.0), "Fail")
		p_pf = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "PF",
				"parameter_name": "PF",
				"parameter_category": "Other",
				"tolerance_type": "PassFailOnly",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(evaluate_parameter_tolerance(p_pf.name, observed_boolean=True), "Pass")
		self.assertEqual(evaluate_parameter_tolerance(p_pf.name, observed_boolean=False), "Fail")
		self.assertEqual(evaluate_parameter_tolerance(p_pf.name), "Inconclusive")
		p_none = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "N",
				"parameter_name": "None",
				"parameter_category": "Other",
				"tolerance_type": "None",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(evaluate_parameter_tolerance(p_none.name, observed_numeric=1.0), "Inconclusive")

	def test_KT_INSP112_record_parameter_and_recompute(self):
		pc = self._minimal_award_and_pc("C")
		tpl = self._template("TPLC")
		ir = self._ir(pc, "C", tpl)
		pl = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "R1",
				"parameter_name": "R",
				"parameter_category": "Dimensional",
				"tolerance_type": "MinMax",
				"expected_min_value": 0.0,
				"expected_max_value": 10.0,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		out = record_parameter_result(ir.name, pl.name, observed_numeric_value=5.0)
		self.assertEqual(out["pass_fail_result"], "Pass")
		self.assertEqual(frappe.db.get_value(IPL, pl.name, "status"), "Passed")
		rec = recompute_inspection_result(ir.name)
		self.assertEqual(rec["parameter_tests_count"], 1)
		self.assertEqual(rec["parameter_tests_passed_count"], 1)
		self.assertEqual(rec["parameter_tests_failed_count"], 0)
		self.assertEqual(rec["inspection_result"], "Pass")

	def test_KT_INSP112_record_parameter_inconclusive_pending(self):
		pc = self._minimal_award_and_pc("D")
		tpl = self._template("TPLD")
		ir = self._ir(pc, "D", tpl)
		pl = frappe.get_doc(
			{
				"doctype": IPL,
				"inspection_record": ir.name,
				"parameter_code": "I1",
				"parameter_name": "I",
				"parameter_category": "Other",
				"tolerance_type": "None",
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		out = record_parameter_result(ir.name, pl.name, observed_numeric_value=1.0)
		self.assertEqual(out["pass_fail_result"], "Pending")
		self.assertEqual(frappe.db.get_value(IPL, pl.name, "status"), "Pending")
		rec = recompute_inspection_result(ir.name)
		self.assertEqual(rec["inspection_result"], "Pending")

	def test_KT_INSP112_recompute_fail_from_checklist(self):
		pc = self._minimal_award_and_pc("E")
		tpl = self._template("TPLE")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRE",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "chk",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"checklist_lines": [
					{
						"check_item_no": 1,
						"requirement_type": "Visual",
						"requirement_title": "A",
						"result_status": "Fail",
					}
				],
			}
		).insert(ignore_permissions=True)
		rec = recompute_inspection_result(ir.name)
		self.assertEqual(rec["inspection_result"], "Fail")
		self.assertEqual(rec["checklist_items_count"], 1)

	def test_KT_INSP112_record_checklist_result(self):
		pc = self._minimal_award_and_pc("F")
		tpl = self._template("TPLF")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRF",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "chk2",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"checklist_lines": [
					{
						"check_item_no": 1,
						"requirement_type": "Visual",
						"requirement_title": "B",
						"result_status": "Pending",
					}
				],
			}
		).insert(ignore_permissions=True)
		record_checklist_result(ir.name, check_item_no=1, result_status="Pass", observed_result="OK")
		doc = frappe.get_doc(IR, ir.name)
		self.assertEqual(doc.checklist_lines[0].result_status, "Pass")
		self.assertEqual(doc.checklist_lines[0].observed_result, "OK")

	def test_KT_INSP112_apply_inspection_template(self):
		pc = self._minimal_award_and_pc("G")
		tpl_a = self._template("TPLGA", inspection_method_type="Checklist", requires_sampling=0)
		tpl_b = self._template(
			"TPLGB",
			inspection_method_type="Parameter Testing",
			requires_sampling=1,
			requires_lab_test=1,
		)
		ir = self._ir(pc, "G", tpl_a, inspection_method_type="Checklist")
		self.assertEqual(frappe.db.get_value(IR, ir.name, "inspection_method_type"), "Checklist")
		apply_inspection_template(ir.name, tpl_b.name)
		self.assertEqual(frappe.db.get_value(IR, ir.name, "inspection_method_type"), "Parameter Testing")
		self.assertEqual(int(frappe.db.get_value(IR, ir.name, "requires_sampling") or 0), 1)
		self.assertEqual(int(frappe.db.get_value(IR, ir.name, "requires_lab_test") or 0), 1)
