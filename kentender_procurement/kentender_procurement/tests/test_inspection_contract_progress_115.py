# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-115: inspection_contract_progress_services."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.acceptance_decision_services import submit_acceptance_decision
from kentender_procurement.services.inspection_contract_progress_services import apply_acceptance_progress_from_inspection

AD = "Award Decision"
AR = "Acceptance Record"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Report"
EVAL = "Evaluation Session"
IMT = "Inspection Method Template"
IR = "Inspection Record"
PC = "Procurement Contract"
PCM = "Procurement Contract Milestone"
PCD = "Procurement Contract Deliverable"
TENDER = "Tender"
PREFIX = "_KT_INSP115"


def _cleanup_115():
	for row in frappe.get_all(AR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IR, row, force=True, ignore_permissions=True)
	pc_names = frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []
	for cn in pc_names:
		for row in frappe.get_all(PCD, filters={"procurement_contract": cn}, pluck="name") or []:
			frappe.delete_doc(PCD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PCM, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(PCM, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IMT, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, row, force=True, ignore_permissions=True)
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


class TestInspectionContractProgress115(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_115)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()
		if not frappe.db.exists("UOM", "Nos"):
			frappe.get_doc({"doctype": "UOM", "uom_name": "Nos"}).insert(ignore_permissions=True)

	def tearDown(self):
		run_test_db_cleanup(_cleanup_115)
		super().tearDown()

	def _minimal_award_and_pc(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "INSP115",
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
				"decision_justification": "115 tests.",
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
				"contract_title": "115 contract",
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

	def _template(self, suf: str):
		c = f"{PREFIX}_{suf}"
		return frappe.get_doc(
			{
				"doctype": IMT,
				"template_code": c,
				"template_name": "Tpl",
				"inspection_domain": "General",
				"applicable_contract_type": "Goods",
				"inspection_method_type": "Checklist",
				"default_pass_logic": "All Mandatory Pass",
				"active": 1,
			}
		).insert(ignore_permissions=True)

	def test_KT_INSP115_accepted_milestone_updates_contract_percent(self):
		pc = self._minimal_award_and_pc("A")
		m1 = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M1A",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M1",
				"status": "Planned",
				"completion_percent": 0,
			}
		).insert(ignore_permissions=True)
		m2 = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M2A",
				"procurement_contract": pc.name,
				"milestone_no": 2,
				"title": "M2",
				"status": "Planned",
				"completion_percent": 0,
			}
		).insert(ignore_permissions=True)
		tpl = self._template("TPLA")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRA",
				"contract": pc.name,
				"inspection_scope_type": "Milestone",
				"contract_milestone": m1.name,
				"inspection_title": "M1 inspection",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		submit_acceptance_decision(
			ir.name,
			{"business_id": f"{PREFIX}_ARA", "acceptance_decision": "Accepted"},
		)
		out = apply_acceptance_progress_from_inspection(ir.name)
		self.assertEqual(frappe.db.get_value(PCM, m1.name, "status"), "Achieved")
		self.assertEqual(float(frappe.db.get_value(PCM, m1.name, "completion_percent") or 0), 100.0)
		self.assertAlmostEqual(out["completion_percent"], 50.0)
		arn = frappe.db.get_value(IR, ir.name, "acceptance_record")
		self.assertEqual(int(frappe.db.get_value(AR, arn, "contract_progress_update_required") or 0), 0)

	def test_KT_INSP115_conditional_partial_milestone_percent(self):
		pc = self._minimal_award_and_pc("B")
		m1 = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M1B",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M1",
				"status": "Planned",
				"completion_percent": 0,
			}
		).insert(ignore_permissions=True)
		tpl = self._template("TPLB")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRB",
				"contract": pc.name,
				"inspection_scope_type": "Milestone",
				"contract_milestone": m1.name,
				"inspection_title": "Partial",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		submit_acceptance_decision(
			ir.name,
			{"business_id": f"{PREFIX}_ARB", "acceptance_decision": "Conditional"},
		)
		apply_acceptance_progress_from_inspection(ir.name, partial_milestone_percent=35.0)
		self.assertEqual(frappe.db.get_value(PCM, m1.name, "status"), "In Progress")
		self.assertEqual(float(frappe.db.get_value(PCM, m1.name, "completion_percent") or 0), 35.0)

	def test_KT_INSP115_rejected_deliverable(self):
		pc = self._minimal_award_and_pc("C")
		m1 = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M1C",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M1",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		dd = frappe.get_doc(
			{
				"doctype": PCD,
				"procurement_contract": pc.name,
				"contract_milestone": m1.name,
				"deliverable_title": "Widget",
				"status": "Planned",
				"uom": "Nos",
			}
		).insert(ignore_permissions=True)
		tpl = self._template("TPLC")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRC",
				"contract": pc.name,
				"inspection_scope_type": "Deliverable",
				"contract_deliverable": dd.name,
				"inspection_title": "Deliverable inspection",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Fail",
			}
		).insert(ignore_permissions=True)
		submit_acceptance_decision(
			ir.name,
			{"business_id": f"{PREFIX}_ARC", "acceptance_decision": "Rejected"},
		)
		apply_acceptance_progress_from_inspection(ir.name)
		self.assertEqual(frappe.db.get_value(PCD, dd.name, "status"), "Rejected")

	def test_KT_INSP115_second_apply_blocked_without_flag(self):
		pc = self._minimal_award_and_pc("D")
		m1 = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M1D",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M1",
				"status": "Planned",
				"completion_percent": 0,
			}
		).insert(ignore_permissions=True)
		tpl = self._template("TPLD")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRD",
				"contract": pc.name,
				"inspection_scope_type": "Milestone",
				"contract_milestone": m1.name,
				"inspection_title": "x",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		submit_acceptance_decision(
			ir.name,
			{"business_id": f"{PREFIX}_ARD", "acceptance_decision": "Accepted"},
		)
		apply_acceptance_progress_from_inspection(ir.name)
		self.assertRaises(frappe.ValidationError, apply_acceptance_progress_from_inspection, ir.name)

	def test_KT_INSP115_deferred_contract_wide_no_row_changes(self):
		pc = self._minimal_award_and_pc("E")
		m1 = frappe.get_doc(
			{
				"doctype": PCM,
				"business_id": f"{PREFIX}_M1E",
				"procurement_contract": pc.name,
				"milestone_no": 1,
				"title": "M1",
				"status": "Planned",
				"completion_percent": 10,
			}
		).insert(ignore_permissions=True)
		tpl = self._template("TPLE")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRE",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Wide",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		submit_acceptance_decision(
			ir.name,
			{
				"business_id": f"{PREFIX}_ARE",
				"acceptance_decision": "Deferred",
				"contract_progress_update_required": True,
			},
		)
		out = apply_acceptance_progress_from_inspection(ir.name)
		self.assertEqual(out["updated_milestones"], [])
		self.assertEqual(float(frappe.db.get_value(PCM, m1.name, "completion_percent") or 0), 10.0)
