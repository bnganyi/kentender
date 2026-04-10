# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""PROC-STORY-094–099: contract services, queues, script reports."""

import importlib

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE

from kentender_procurement.services.contract_activation_service import activate_contract
from kentender_procurement.services.contract_approval_signature_services import (
	approve_contract,
	record_contract_signature,
	send_contract_for_signature,
	submit_contract_for_review,
)
from kentender_procurement.services.contract_from_award import create_contract_from_award
from kentender_procurement.services.contract_lifecycle_services import (
	close_contract,
	resume_contract,
	suspend_contract,
)
from kentender_procurement.services.contract_queue_queries import (
	get_active_contracts,
	get_contracts_near_end_date,
	get_draft_contracts,
	get_variations_awaiting_action,
)
from kentender_procurement.services.contract_variation_services import (
	apply_contract_variation,
	approve_contract_variation,
	request_contract_variation,
)
from kentender_procurement.services.award_approval_services import final_approve_award
from kentender_procurement.services.award_from_evaluation import create_award_decision_from_evaluation
from kentender_procurement.services.evaluation_aggregation import aggregate_evaluation_results
from kentender_procurement.services.evaluation_report_services import (
	generate_evaluation_report,
	submit_evaluation_report,
)

PC = "Procurement Contract"
PCV = "Procurement Contract Variation"
PCSE = "Procurement Contract Status Event"
AD = "Award Decision"
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
PREFIX = "_KT_CON094"

_REPORT_MODULES = (
	"kentender_procurement.kentender_procurement.report.draft_contracts.draft_contracts",
	"kentender_procurement.kentender_procurement.report.contracts_pending_signature.contracts_pending_signature",
	"kentender_procurement.kentender_procurement.report.active_contracts.active_contracts",
	"kentender_procurement.kentender_procurement.report.variations_awaiting_action.variations_awaiting_action",
	"kentender_procurement.kentender_procurement.report.contracts_near_end_date.contracts_near_end_date",
	"kentender_procurement.kentender_procurement.report.suspended_terminated_contracts.suspended_terminated_contracts",
)


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _cleanup_con094():
	frappe.flags.allow_contract_status_event_delete = True
	for pc in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in (PCSE, "Procurement Contract Signing Record", "Procurement Contract Approval Record", PCV):
			for ch in frappe.get_all(dt, filters={"procurement_contract": pc}, pluck="name") or []:
				frappe.delete_doc(dt, ch, force=True, ignore_permissions=True)
		frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": PC, "target_docname": pc})
		frappe.delete_doc(PC, pc, force=True, ignore_permissions=True)
	for row in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		frappe.delete_doc(AD, row, force=True, ignore_permissions=True)
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
	frappe.flags.allow_contract_status_event_delete = False


class TestContractServices094to099(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_con094)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_con094)
		super().tearDown()

	def _ready_award(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "CON094",
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
		a = create_award_decision_from_evaluation(e.name, business_id=f"{PREFIX}_AD{suffix}")
		ad = frappe.get_doc(AD, a["name"])
		ad.approved_bid_submission = ad.recommended_bid_submission
		ad.approved_supplier = ad.recommended_supplier
		ad.approved_amount = ad.recommended_amount
		ad.save(ignore_permissions=True)
		final_approve_award(ad.name)
		return t, e, ad

	def test_KT_CON094_create_blocked_when_not_ready(self):
		t, e, rep, b, ad = self._minimal_award_blocked()
		with self.assertRaises(frappe.ValidationError):
			create_contract_from_award(ad.name, business_id=f"{PREFIX}_PCX")

	def _minimal_award_blocked(self):
		"""Award exists but not approved — readiness fails."""
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_TX",
				"business_id": f"{PREFIX}_TX-BIZ",
				"title": "X",
				"tender_number": "X",
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
				"business_id": f"{PREFIX}_SX",
				"tender": t.name,
				"procuring_entity": self.entity.name,
				"status": "Draft",
				"workflow_state": "Draft",
			}
		).insert(ignore_permissions=True)
		r = frappe.get_doc(
			{
				"doctype": BOR,
				"business_id": f"{PREFIX}_RX",
				"tender": t.name,
				"bid_opening_session": s.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		e = frappe.get_doc(
			{
				"doctype": ES,
				"business_id": f"{PREFIX}_EX",
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
				"business_id": f"{PREFIX}_ERX",
				"evaluation_session": e.name,
				"tender": t.name,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
		b = frappe.get_doc(
			{
				"doctype": "Bid Submission",
				"business_id": f"{PREFIX}_BX",
				"tender": t.name,
				"supplier": "SX",
				"tender_lot_scope": "Whole Tender",
				"procuring_entity": self.entity.name,
				"procurement_method": "Open National Tender",
				"status": "Draft",
				"workflow_state": "Draft",
				"submission_version_no": 1,
			}
		).insert(ignore_permissions=True)
		ad = frappe.get_doc(
			{
				"doctype": AD,
				"business_id": f"{PREFIX}_ADX",
				"tender": t.name,
				"evaluation_session": e.name,
				"evaluation_report": rep.name,
				"decision_justification": "x",
				"recommended_bid_submission": b.name,
				"recommended_supplier": "SX",
				"approved_bid_submission": b.name,
				"approved_supplier": "SX",
				"currency": self.currency,
			}
		).insert(ignore_permissions=True)
		return t, e, rep, b, ad

	def test_KT_CON094_create_success_and_KT_CON095_096_flow(self):
		_t, _e, ad = self._ready_award("A")
		c = create_contract_from_award(ad.name, business_id=f"{PREFIX}_PC1")
		self.assertTrue(c["name"])
		submit_contract_for_review(c["name"])
		approve_contract(c["name"])
		send_contract_for_signature(c["name"])
		record_contract_signature(c["name"], hash_value="sha256-test-hash")
		out = activate_contract(c["name"])
		self.assertEqual(out["status"], "Active")

	def test_KT_CON097_variation_apply(self):
		_t, _e, ad = self._ready_award("B")
		c = create_contract_from_award(ad.name, business_id=f"{PREFIX}_PC2")
		pc = frappe.get_doc(PC, c["name"])
		pc.status = "Active"
		pc.workflow_state = "Active"
		pc.save(ignore_permissions=True)
		v = request_contract_variation(
			c["name"],
			reason="Adjust value",
			variation_type="Value",
			new_contract_value=float(pc.contract_value),
		)
		approve_contract_variation(v["name"])
		apply_contract_variation(v["name"])
		pcv = frappe.get_doc(PCV, v["name"])
		self.assertEqual(_norm(pcv.status), "Applied")

	def test_KT_CON098_lifecycle(self):
		_t, _e, ad = self._ready_award("C")
		c = create_contract_from_award(ad.name, business_id=f"{PREFIX}_PC3")
		pc = frappe.get_doc(PC, c["name"])
		pc.status = "Active"
		pc.workflow_state = "Active"
		pc.save(ignore_permissions=True)
		suspend_contract(c["name"], reason="pause")
		res = frappe.get_doc(PC, c["name"])
		self.assertEqual(res.status, "Suspended")
		resume_contract(c["name"])
		close_contract(c["name"], notes="done")
		self.assertEqual(frappe.db.get_value(PC, c["name"], "status"), "Closed")

	def test_KT_CON099_queues_and_reports(self):
		for mod_path in _REPORT_MODULES:
			mod = importlib.import_module(mod_path)
			cols, data = mod.execute({})
			self.assertTrue(isinstance(cols, list) and len(cols) > 0, msg=mod_path)
			self.assertIsInstance(data, list, msg=mod_path)
			self.assertIsInstance(mod.get_filters(), list)
		for fn in (get_draft_contracts, get_active_contracts, get_variations_awaiting_action, get_contracts_near_end_date):
			self.assertIsInstance(fn(procuring_entity=None), list)
