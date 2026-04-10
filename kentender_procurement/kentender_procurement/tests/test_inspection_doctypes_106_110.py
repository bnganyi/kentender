# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-106–110: Inspection Evidence, Non Conformance, Acceptance, Reinspection, Status Event."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, now_datetime, nowdate

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp

AD = "Award Decision"
AR = "Acceptance Record"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ERPT = "Evaluation Report"
ES = "Evaluation Session"
IE = "Inspection Evidence"
IMT = "Inspection Method Template"
IR = "Inspection Record"
ISE = "Inspection Status Event"
NC = "Non Conformance Record"
PC = "Procurement Contract"
RR = "Reinspection Record"
TENDER = "Tender"
PREFIX = "_KT_INSP106"


def _cleanup_insp106():
	frappe.flags.allow_inspection_status_event_delete = True
	frappe.flags.allow_inspection_status_event_mutate = True
	ir_names = frappe.get_all(IR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []
	if ir_names:
		for dt in (IE, RR, ISE):
			for row in frappe.get_all(dt, filters={"inspection_record": ("in", ir_names)}, pluck="name") or []:
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(NC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(NC, row, force=True, ignore_permissions=True)
	for row in ir_names:
		frappe.delete_doc(IR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(IMT, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(IMT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(PC, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ERPT, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(ES, row, force=True, ignore_permissions=True)
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
	frappe.flags.allow_inspection_status_event_mutate = False


class TestInspectionDocTypes106to110(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_insp106)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_insp106)
		super().tearDown()

	def _minimal_award_and_pc(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "INSP106",
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
				"doctype": ES,
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
				"doctype": ERPT,
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
				"decision_justification": "Inspection 106 tests.",
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
				"contract_title": "Inspection contract",
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

	def _template(self, suf: str = "TPL"):
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
			}
		).insert(ignore_permissions=True)

	def _base_ir(self, pc, tpl, ir_biz: str):
		return frappe.get_doc(
			{
				"doctype": IR,
				"business_id": ir_biz,
				"contract": pc.name,
				"inspection_scope_type": "Contract Wide",
				"inspection_title": "Base inspection",
				"inspection_method_type": "Checklist",
				"inspection_method_template": tpl.name,
				"procuring_entity": self.entity.name,
			}
		).insert(ignore_permissions=True)

	def test_KT_INSP107_non_conformance_record(self):
		pc = self._minimal_award_and_pc("A")
		tpl = self._template()
		ir = self._base_ir(pc, tpl, f"{PREFIX}_IR1")
		nc = frappe.get_doc(
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
		self.assertTrue(nc.display_label)

	def test_KT_INSP108_acceptance_record(self):
		pc = self._minimal_award_and_pc("B")
		tpl = self._template("B")
		ir = self._base_ir(pc, tpl, f"{PREFIX}_IR2")
		ar = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_AR1",
				"inspection_record": ir.name,
				"contract": pc.name,
				"acceptance_decision": "Pending",
				"standards_compliance_status": "Not Assessed",
				"payment_eligibility_signal_status": "Unknown",
				"next_action_type": "None",
			}
		).insert(ignore_permissions=True)
		self.assertEqual(ar.inspection_record, ir.name)

	def test_KT_INSP106_inspection_evidence(self):
		pc = self._minimal_award_and_pc("C")
		tpl = self._template("C")
		ir = self._base_ir(pc, tpl, f"{PREFIX}_IR3")
		nc = frappe.get_doc(
			{
				"doctype": NC,
				"business_id": f"{PREFIX}_NC2",
				"inspection_record": ir.name,
				"contract": pc.name,
				"issue_type": "Quality",
				"issue_title": "Q1",
				"severity": "Major",
				"status": "Open",
			}
		).insert(ignore_permissions=True)
		ar = frappe.get_doc(
			{
				"doctype": AR,
				"business_id": f"{PREFIX}_AR2",
				"inspection_record": ir.name,
				"contract": pc.name,
				"acceptance_decision": "Pending",
				"standards_compliance_status": "Not Assessed",
				"payment_eligibility_signal_status": "Unknown",
				"next_action_type": "None",
			}
		).insert(ignore_permissions=True)
		ev = frappe.get_doc(
			{
				"doctype": IE,
				"inspection_record": ir.name,
				"acceptance_record": ar.name,
				"non_conformance_record": nc.name,
				"evidence_type": "Photo",
				"title": "Site photo",
				"uploaded_by_user": "Administrator",
				"uploaded_on": now_datetime(),
				"hash_value": "sha256-test",
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)
		self.assertIn("Site photo", ev.display_label or "")

	def test_KT_INSP109_reinspection_record(self):
		pc = self._minimal_award_and_pc("D")
		tpl = self._template("D")
		ir = self._base_ir(pc, tpl, f"{PREFIX}_IR4")
		rr = frappe.get_doc(
			{
				"doctype": RR,
				"inspection_record": ir.name,
				"contract": pc.name,
				"trigger_reason": "Non Conformance",
				"status": "Planned",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(rr.display_label)

	def test_KT_INSP110_status_event_append_only(self):
		pc = self._minimal_award_and_pc("E")
		tpl = self._template("E")
		ir = self._base_ir(pc, tpl, f"{PREFIX}_IR5")
		ev = frappe.get_doc(
			{
				"doctype": ISE,
				"inspection_record": ir.name,
				"event_type": "Created",
				"event_datetime": now_datetime(),
				"summary": "Inspection opened.",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(ev.event_hash)
		ev.summary = "Changed"
		self.assertRaises(frappe.ValidationError, ev.save, ignore_permissions=True)

	def test_KT_INSP110_status_event_delete_guard(self):
		pc = self._minimal_award_and_pc("F")
		tpl = self._template("F")
		ir = self._base_ir(pc, tpl, f"{PREFIX}_IR6")
		ev = frappe.get_doc(
			{
				"doctype": ISE,
				"inspection_record": ir.name,
				"event_type": "Scheduled",
				"event_datetime": now_datetime(),
				"summary": "Scheduled.",
			}
		).insert(ignore_permissions=True)
		def _delete_ev():
			frappe.delete_doc(ISE, ev.name, force=True, ignore_permissions=True)

		self.assertRaises(frappe.ValidationError, _delete_ev)
