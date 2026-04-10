# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-114: non_conformance_services."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, now_datetime, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

from kentender_procurement.services.non_conformance_services import (
	approve_non_conformance_resolution,
	create_reinspection,
	raise_non_conformance,
	submit_corrective_action_resolution,
)

AD = "Award Decision"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Report"
EVAL = "Evaluation Session"
IMT = "Inspection Method Template"
IR = "Inspection Record"
ISE = "Inspection Status Event"
NC = "Non Conformance Record"
PC = "Procurement Contract"
RR = "Reinspection Record"
TENDER = "Tender"
PREFIX = "_KT_INSP114"


def _cleanup_114():
	frappe.flags.allow_inspection_status_event_delete = True
	ir_names = frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []
	for irn in ir_names:
		for row in frappe.get_all(ISE, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(ISE, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(RR, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(RR, row, force=True, ignore_permissions=True)
		for row in frappe.get_all(NC, filters={"inspection_record": irn}, pluck="name") or []:
			frappe.delete_doc(NC, row, force=True, ignore_permissions=True)
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
	frappe.flags.allow_inspection_status_event_delete = False


class TestNonConformanceServices114(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_114)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_114)
		super().tearDown()

	def _minimal_award_and_pc(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "INSP114",
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
				"decision_justification": "114 tests.",
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
				"contract_title": "114 contract",
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

	def _ir(self, pc, biz: str, tpl):
		return frappe.get_doc(
			{
				"doctype": IR,
				"business_id": biz,
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "114",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
				"status": "In Progress",
				"workflow_state": "In Progress",
				"inspection_result": "Pending",
			}
		).insert(ignore_permissions=True)

	def test_KT_INSP114_raise_non_conformance_audit_and_count(self):
		pc = self._minimal_award_and_pc("A")
		tpl = self._template("TPLA")
		ir = self._ir(pc, f"{PREFIX}_IR1", tpl)
		out = raise_non_conformance(
			ir.name,
			{
				"business_id": f"{PREFIX}_NC1",
				"issue_type": "Defect",
				"issue_title": "Scratch",
				"severity": "Minor",
				"required_corrective_action": "Repaint",
			},
		)
		self.assertTrue(out["name"])
		self.assertEqual(int(frappe.db.get_value(IR, ir.name, "non_conformance_count") or 0), 1)
		ev = frappe.get_all(
			ISE,
			filters={"inspection_record": ir.name, "event_type": "NonConformanceRaised"},
			pluck="related_non_conformance_record",
		)
		self.assertEqual(ev, [out["name"]])

	def test_KT_INSP114_submit_then_approve_resolved(self):
		pc = self._minimal_award_and_pc("B")
		tpl = self._template("TPLB")
		ir = self._ir(pc, f"{PREFIX}_IR2", tpl)
		nc = raise_non_conformance(
			ir.name,
			{
				"business_id": f"{PREFIX}_NC2",
				"issue_type": "Quality",
				"issue_title": "Q1",
				"severity": "Major",
			},
		)["name"]
		sub = submit_corrective_action_resolution(nc, {"resolution_summary": "Repaired panel."})
		self.assertEqual(sub["status"], "In Progress")
		app = approve_non_conformance_resolution(nc, {"outcome": "Resolved"})
		self.assertEqual(app["status"], "Resolved")
		doc = frappe.get_doc(NC, nc)
		self.assertTrue(doc.resolved_on)

	def test_KT_INSP114_approve_waiver_requires_approver_user(self):
		pc = self._minimal_award_and_pc("C")
		tpl = self._template("TPLC")
		ir = self._ir(pc, f"{PREFIX}_IR3", tpl)
		nc = raise_non_conformance(
			ir.name,
			{
				"business_id": f"{PREFIX}_NC3",
				"issue_type": "Documentation",
				"issue_title": "Missing page",
				"severity": "Minor",
			},
		)["name"]
		submit_corrective_action_resolution(nc, {"resolution_summary": "Will submit next week."})
		self.assertRaises(
			frappe.ValidationError,
			approve_non_conformance_resolution,
			nc,
			{"outcome": "Waived"},
		)
		approve_non_conformance_resolution(
			nc,
			{"outcome": "Waived", "waiver_approved_by_user": "Administrator"},
		)
		self.assertEqual(frappe.db.get_value(NC, nc, "status"), "Waived")

	def test_KT_INSP114_approve_blocked_from_open(self):
		pc = self._minimal_award_and_pc("D")
		tpl = self._template("TPLD")
		ir = self._ir(pc, f"{PREFIX}_IR4", tpl)
		nc = raise_non_conformance(
			ir.name,
			{
				"business_id": f"{PREFIX}_NC4",
				"issue_type": "Other",
				"issue_title": "X",
				"severity": "Critical",
			},
		)["name"]
		self.assertRaises(
			frappe.ValidationError,
			approve_non_conformance_resolution,
			nc,
			{"outcome": "Resolved"},
		)

	def test_KT_INSP114_create_reinspection_flags_and_event(self):
		pc = self._minimal_award_and_pc("E")
		tpl = self._template("TPLE")
		ir = self._ir(pc, f"{PREFIX}_IR5", tpl)
		when = now_datetime()
		out = create_reinspection(
			ir.name,
			{"scheduled_datetime": when, "remarks": "Follow-up after NC"},
		)
		self.assertTrue(out["name"])
		self.assertEqual(int(frappe.db.get_value(IR, ir.name, "is_reinspection_required") or 0), 1)
		self.assertEqual(getdate(frappe.db.get_value(IR, ir.name, "reinspection_due_date")), getdate(when))
		ev = frappe.get_all(
			ISE,
			filters={"inspection_record": ir.name, "event_type": "ReinspectionScheduled"},
			pluck="name",
		)
		self.assertEqual(len(ev), 1)

	def test_KT_INSP114_reinspection_chain_followup_link(self):
		pc = self._minimal_award_and_pc("F")
		tpl = self._template("TPLF")
		ir_orig = self._ir(pc, f"{PREFIX}_IR6", tpl)
		ir_follow = self._ir(pc, f"{PREFIX}_IR6F", tpl)
		rr = create_reinspection(
			ir_orig.name,
			{"linked_followup_inspection": ir_follow.name, "trigger_reason": "Non Conformance"},
		)
		self.assertEqual(frappe.db.get_value(RR, rr["name"], "linked_followup_inspection"), ir_follow.name)
