# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-116: inspection queue queries and script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, now_datetime, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.inspection_queue_queries import (
	get_inspections_awaiting_acceptance,
	get_non_conformance_register_rows,
	get_partial_or_rejected_acceptance_rows,
	get_reinspections_due_rows,
	get_scheduled_inspections,
)

AD = "Award Decision"
AR = "Acceptance Record"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Report"
EVAL = "Evaluation Session"
IMT = "Inspection Method Template"
IR = "Inspection Record"
NC = "Non Conformance Record"
PC = "Procurement Contract"
RR = "Reinspection Record"
TENDER = "Tender"
PREFIX = "_KT_INSP116"

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.scheduled_inspections.scheduled_inspections",
	"kentender_procurement.kentender_procurement.report.inspections_awaiting_acceptance.inspections_awaiting_acceptance",
	"kentender_procurement.kentender_procurement.report.non_conformance_register.non_conformance_register",
	"kentender_procurement.kentender_procurement.report.reinspections_due.reinspections_due",
	"kentender_procurement.kentender_procurement.report.inspection_partial_rejection_summary.inspection_partial_rejection_summary",
)


def _exec_report(module_path: str, filters: dict):
	mod = importlib.import_module(module_path)
	return mod.execute(filters)


def _cleanup_116():
	for row in frappe.get_all(AR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AR, row, force=True, ignore_permissions=True)
	ir_for_rr = frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []
	for irn in ir_for_rr:
		for row in frappe.get_all(RR, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(RR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(NC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(NC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
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
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE_OTHER"})


class TestInspectionQueues116(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_116)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.other_entity = _make_entity(f"{PREFIX}_PE_OTHER").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_116)
		super().tearDown()

	def _minimal_award_and_pc(self, suffix: str, entity_name: str | None = None):
		ent = entity_name or self.entity.name
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "INSP116",
				"tender_number": f"{PREFIX}_TN{suffix}",
				"workflow_state": "Draft",
				"status": "Draft",
				"approval_status": "Draft",
				"origin_type": "Manual",
				"procuring_entity": ent,
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		s = frappe.get_doc(
			{
				"doctype": BOS,
				"business_id": f"{PREFIX}_S{suffix}",
				"tender": t.name,
				"procuring_entity": ent,
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
				"procuring_entity": ent,
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
				"procuring_entity": ent,
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
				"decision_justification": "116 tests.",
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
				"contract_title": "116 contract",
				"award_decision": ad.name,
				"tender": t.name,
				"evaluation_session": e.name,
				"approved_bid_submission": b.name,
				"supplier": f"S-{suffix}",
				"procuring_entity": ent,
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

	def test_KT_INSP116_scheduled_and_awaiting_queues(self):
		pc = self._minimal_award_and_pc("A")
		tpl = self._template("TPLA")
		ir_sched = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRS",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Scheduled",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Scheduled",
				"workflow_state": "Scheduled",
				"scheduled_inspection_datetime": now_datetime(),
				"inspection_result": "Pending",
			}
		).insert(ignore_permissions=True)
		ir_wait = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRW",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Awaiting",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		sched_rows = get_scheduled_inspections(procuring_entity=self.entity.name)
		self.assertTrue(any(r["name"] == ir_sched.name for r in sched_rows))
		wait_rows = get_inspections_awaiting_acceptance(procuring_entity=self.entity.name)
		self.assertTrue(any(r["name"] == ir_wait.name for r in wait_rows))
		_, data_s = _exec_report(_REPORT_MODULES[0], {"procuring_entity": self.entity.name})
		self.assertTrue(any(row[0] == ir_sched.name for row in data_s))
		_, data_w = _exec_report(_REPORT_MODULES[1], {"procuring_entity": self.entity.name})
		self.assertTrue(any(row[0] == ir_wait.name for row in data_w))
		other_sched = get_scheduled_inspections(procuring_entity=self.other_entity.name)
		self.assertFalse(any(r["name"] == ir_sched.name for r in other_sched))

	def test_KT_INSP116_non_conformance_and_reinspection_queues(self):
		pc = self._minimal_award_and_pc("B")
		tpl = self._template("TPLB")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRB",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Base",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "In Progress",
				"workflow_state": "In Progress",
				"inspection_result": "Pending",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": NC,
				"business_id": f"{PREFIX}_NC1",
				"inspection_record": ir.name,
				"contract": pc.name,
				"issue_type": "Defect",
				"issue_title": "Scratch",
				"severity": "Minor",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": RR,
				"inspection_record": ir.name,
				"contract": pc.name,
				"trigger_reason": "Non Conformance",
				"status": "Planned",
				"scheduled_datetime": now_datetime(),
			}
		).insert(ignore_permissions=True)
		nc_rows = get_non_conformance_register_rows(procuring_entity=self.entity.name)
		self.assertEqual(len(nc_rows), 1)
		rr_rows = get_reinspections_due_rows(procuring_entity=self.entity.name)
		self.assertEqual(len(rr_rows), 1)
		_, data_nc = _exec_report(_REPORT_MODULES[2], {"procuring_entity": self.entity.name})
		self.assertEqual(len(data_nc), 1)
		_, data_rr = _exec_report(_REPORT_MODULES[3], {"procuring_entity": self.entity.name})
		self.assertEqual(len(data_rr), 1)

	def test_KT_INSP116_partial_rejection_summary(self):
		pc = self._minimal_award_and_pc("C")
		tpl = self._template("TPLC")
		ir = frappe.get_doc(
			{
				"doctype": IR,
				"business_id": f"{PREFIX}_IRC",
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "X",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "Completed",
				"workflow_state": "Completed",
				"inspection_result": "Pass",
			}
		).insert(ignore_permissions=True)
		ar = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_ARC",
				"inspection_record": ir.name,
				"contract": pc.name,
				"acceptance_decision": "Conditional",
				"status": "Submitted",
				"workflow_state": "Pending Approval",
				"standards_compliance_status": "Not Assessed",
				"payment_eligibility_signal_status": "Conditional",
				"next_action_type": "Variation",
			}
		)
		with workflow_mutation_context():
			ar.insert(ignore_permissions=True)
		rows = get_partial_or_rejected_acceptance_rows(procuring_entity=self.entity.name)
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["acceptance_decision"], "Conditional")
		_, data = _exec_report(_REPORT_MODULES[4], {"procuring_entity": self.entity.name})
		self.assertEqual(len(data), 1)

	def test_KT_INSP116_all_script_reports_execute(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			self.assertIsInstance(mod.get_filters(), list, msg=mod_path)
