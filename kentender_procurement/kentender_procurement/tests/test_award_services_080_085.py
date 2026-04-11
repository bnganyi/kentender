# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-080–085: award services, readiness gate, queues, and script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.award_approval_services import (
	detect_award_deviation,
	final_approve_award,
	submit_award_for_approval,
)
from kentender_procurement.services.award_from_evaluation import create_award_decision_from_evaluation
from kentender_procurement.services.award_notification_standstill_services import (
	initialize_standstill_period,
	release_award_for_contract,
	send_award_notifications,
)
from kentender_procurement.services.award_queue_queries import (
	get_award_deviation_register,
	get_award_notification_status,
	get_awards_pending_approval,
	get_awards_pending_final_approval,
	get_awards_ready_for_contract,
	get_standstill_active_awards,
)
from kentender_procurement.services.contract_readiness_gate import get_award_contract_readiness
from kentender_procurement.services.evaluation_aggregation import aggregate_evaluation_results
from kentender_procurement.services.evaluation_report_services import (
	generate_evaluation_report,
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
EA = "Evaluator Assignment"
AD = "Award Decision"
ADR = "Award Deviation Record"
SSP = "Standstill Period"
AN = "Award Notification"
BCP = "Budget Control Period"
PREFIX = "_KT_AWD08"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _cleanup_award_workflow_policies():
	pol_code = f"{PREFIX}_AWPOL"
	tpl_code = f"{PREFIX}_AWTPL"
	for name in frappe.get_all(
		"KenTender Approval Route Instance",
		filters={"reference_doctype": AD, "reference_docname": ("like", f"{PREFIX}%")},
		pluck="name",
	):
		try:
			frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
		except Exception:
			pass
	frappe.db.delete(
		"KenTender Approval Action",
		{"reference_doctype": AD, "reference_docname": ("like", f"{PREFIX}%")},
	)
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		frappe.delete_doc("KenTender Workflow Policy", pol_code, force=True, ignore_permissions=True)
	if frappe.db.exists("KenTender Approval Route Template", {"template_code": tpl_code}):
		frappe.delete_doc("KenTender Approval Route Template", tpl_code, force=True, ignore_permissions=True)


def _ensure_award_route_policy(*, n_steps: int = 1) -> None:
	pol_code = f"{PREFIX}_AWPOL"
	tpl_code = f"{PREFIX}_AWTPL"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		return
	steps = []
	for i in range(n_steps):
		steps.append(
			{
				"doctype": "KenTender Approval Route Template Step",
				"step_order": i + 1,
				"step_name": f"A{i + 1}",
				"actor_type": "Role",
				"role_required": "System Manager",
			}
		)
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": tpl_code,
			"template_name": f"Award route {n_steps}-step",
			"object_type": AD,
			"steps": steps,
		}
	)
	tpl.insert()
	pol = frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": pol_code,
			"applies_to_doctype": AD,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	)
	pol.insert()


def _submit_and_final_approve(ad_name: str) -> None:
	_ensure_award_route_policy(n_steps=1)
	submit_award_for_approval(ad_name)
	final_approve_award(ad_name)


_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.awards_pending_approval.awards_pending_approval",
	"kentender_procurement.kentender_procurement.report.awards_pending_final_approval.awards_pending_final_approval",
	"kentender_procurement.kentender_procurement.report.standstill_active_awards.standstill_active_awards",
	"kentender_procurement.kentender_procurement.report.awards_ready_for_contract.awards_ready_for_contract",
	"kentender_procurement.kentender_procurement.report.award_deviation_register.award_deviation_register",
	"kentender_procurement.kentender_procurement.report.award_notification_status.award_notification_status",
)


def _cleanup_awd08():
	_cleanup_award_workflow_policies()
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.db.delete(EA, {"evaluation_session": es_name})
	for ad_name in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in (AN, "Award Return Record", "Award Approval Record", ADR, SSP):
			for row in frappe.get_all(dt, filters={"award_decision": ad_name}, pluck="name") or []:
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
		frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": AD, "target_docname": ad_name})
		frappe.delete_doc(AD, ad_name, force=True, ignore_permissions=True)
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
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
		frappe.delete_doc(ES, es_name, force=True, ignore_permissions=True)
	for row in frappe.get_all("Bid Submission", filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc("Bid Submission", row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOR, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOR, row, force=True, ignore_permissions=True)
	for row in frappe.get_all(BOS, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(BOS, row, force=True, ignore_permissions=True)
	for tn in frappe.get_all(TENDER, filters={"name": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(TENDER, tn, force=True, ignore_permissions=True)
	frappe.db.delete(BCP, {"name": ("like", f"{PREFIX}%")})
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})


class TestAwardServices080to085(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_awd08)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_awd08)
		super().tearDown()

	def _full_chain_submitted_report(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "AWD08",
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
				"business_id": f"{PREFIX}_B1{suffix}",
				"tender": t.name,
				"supplier": f"S1-{suffix}",
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
				"business_id": f"{PREFIX}_B2{suffix}",
				"tender": t.name,
				"supplier": f"S2-{suffix}",
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
			(b1, f"S1-{suffix}", f"{PREFIX}_EV1{suffix}", 80.0),
			(b2, f"S2-{suffix}", f"{PREFIX}_EV2{suffix}", 50.0),
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
		g = generate_evaluation_report(e.name, business_id=f"{PREFIX}_ERPT{suffix}")
		submit_evaluation_report(g["name"])
		return t, e, b1, b2, g["name"]

	def test_KT_AWD080_create_blocked_without_submitted_report(self):
		t, e, b1, _b2, _rpt = self._full_chain_submitted_report("A")
		frappe.db.set_value(ERPT, _rpt, "status", "Draft")
		frappe.db.set_value(ERPT, _rpt, "locked_hash", None)
		frappe.db.set_value(ERPT, _rpt, "submitted_on", None)
		frappe.db.set_value(ERPT, _rpt, "submitted_by_user", None)
		with self.assertRaises(frappe.ValidationError):
			create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_ADBAD")

	def test_KT_AWD080_create_success_and_duplicate_blocked(self):
		t, e, b1, _b2, rpt = self._full_chain_submitted_report("B")
		a1 = create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_AD1")
		self.assertTrue(a1["name"])
		ad = frappe.get_doc(AD, a1["name"])
		self.assertEqual(_norm(ad.evaluation_report), rpt)
		self.assertTrue(ad.outcome_lines)
		self.assertEqual(_norm(ad.recommended_bid_submission), b1.name)
		with self.assertRaises(frappe.ValidationError):
			create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_AD2")

	def test_KT_AWD081_evaluator_cannot_final_approve(self):
		_t, e, _b1, _b2, _rpt = self._full_chain_submitted_report("C")
		a = create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_ADC")
		frappe.get_doc(
			{
				"doctype": EA,
				"evaluation_session": e.name,
				"evaluator_user": frappe.session.user,
				"committee_role": "Member",
				"assignment_status": "Active",
			}
		).insert(ignore_permissions=True)
		ad = frappe.get_doc(AD, a["name"])
		ad.approved_bid_submission = ad.recommended_bid_submission
		ad.approved_supplier = ad.recommended_supplier
		ad.approved_amount = ad.recommended_amount
		ad.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			_ensure_award_route_policy(n_steps=1)
			submit_award_for_approval(a["name"])
			final_approve_award(a["name"])
		frappe.db.delete(EA, {"evaluation_session": e.name})
		_cleanup_award_workflow_policies()
		ad_reset = frappe.get_doc(AD, a["name"])
		with workflow_mutation_context():
			ad_reset.workflow_state = "Draft"
			ad_reset.approval_status = "Draft"
			ad_reset.status = "In Progress"
			ad_reset.save(ignore_permissions=True)
		_ensure_award_route_policy(n_steps=1)
		submit_award_for_approval(a["name"])
		out = final_approve_award(a["name"])
		self.assertEqual(out["status"], "Approved")

	def test_KT_AWD082_deviation_required_before_final(self):
		_t, e, b1, b2, _rpt = self._full_chain_submitted_report("D")
		a = create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_ADD")
		ad = frappe.get_doc(AD, a["name"])
		ad.approved_bid_submission = b2.name
		ad.approved_supplier = f"S2-D"
		ad.approved_amount = ad.recommended_amount
		ad.save(ignore_permissions=True)
		d = detect_award_deviation(a["name"])
		self.assertTrue(d["material_deviation"])
		with self.assertRaises(frappe.ValidationError):
			_ensure_award_route_policy(n_steps=1)
			submit_award_for_approval(a["name"])
			final_approve_award(a["name"])
		ad.reload()
		dev = frappe.get_doc(
			{
				"doctype": ADR,
				"award_decision": ad.name,
				"recommended_bid_submission": b1.name,
				"approved_bid_submission": b2.name,
				"recommended_supplier": f"S1-D",
				"approved_supplier": f"S2-D",
				"deviation_type": "Different Bid",
				"deviation_reason": "Documented override.",
				"status": "Acknowledged",
			}
		).insert(ignore_permissions=True)
		ad.is_deviation_from_recommendation = 1
		ad.deviation_record = dev.name
		ad.save(ignore_permissions=True)
		out = final_approve_award(ad.name)
		self.assertEqual(out["status"], "Approved")

	def test_KT_AWD083_standstill_and_KT_AWD084_readiness(self):
		_t, e, b1, _b2, _rpt = self._full_chain_submitted_report("E")
		a = create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_ADE")
		ad = frappe.get_doc(AD, a["name"])
		ad.approved_bid_submission = ad.recommended_bid_submission
		ad.approved_supplier = ad.recommended_supplier
		ad.approved_amount = ad.recommended_amount
		ad.standstill_required = 1
		ad.save(ignore_permissions=True)
		_submit_and_final_approve(ad.name)
		r0 = get_award_contract_readiness(ad.name)
		self.assertFalse(r0["ready"])
		self.assertIn("standstill_missing", r0["blockers"])
		init = initialize_standstill_period(ad.name, days=5)
		self.assertTrue(init.get("name"))
		r1 = get_award_contract_readiness(ad.name)
		self.assertFalse(r1["ready"])
		self.assertIn("standstill_not_released", r1["blockers"])
		sp = frappe.get_doc(SSP, init["name"])
		sp.complaint_hold_flag = 1
		sp.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			release_award_for_contract(ad.name)
		sp.complaint_hold_flag = 0
		sp.save(ignore_permissions=True)
		release_award_for_contract(ad.name)
		r2 = get_award_contract_readiness(ad.name)
		self.assertTrue(r2["ready"])

	def test_KT_AWD083_notifications(self):
		_t, e, b1, _b2, _rpt = self._full_chain_submitted_report("F")
		a = create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_ADF")
		ad = frappe.get_doc(AD, a["name"])
		ad.approved_bid_submission = ad.recommended_bid_submission
		ad.approved_supplier = ad.recommended_supplier
		ad.approved_amount = ad.recommended_amount
		ad.save(ignore_permissions=True)
		_submit_and_final_approve(ad.name)
		ns = send_award_notifications(ad.name)
		self.assertGreaterEqual(len(ns["notifications"]), 1)

	def test_KT_AWD085_script_reports_and_queues(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			filters = mod.get_filters()
			self.assertIsInstance(filters, list)
		for fn in (
			get_awards_pending_approval,
			get_awards_pending_final_approval,
			get_standstill_active_awards,
			get_awards_ready_for_contract,
			get_award_deviation_register,
			get_award_notification_status,
		):
			self.assertIsInstance(fn(procuring_entity=None), list)
