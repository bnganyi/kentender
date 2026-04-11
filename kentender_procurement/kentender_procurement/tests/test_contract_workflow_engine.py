# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-013: Procurement Contract approval via kentender.workflow_engine."""

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.tests.test_procuring_entity import _ensure_test_currency, _make_entity, run_test_db_cleanup
from kentender_budget.tests.test_budget_control_period import _bcp
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.services.contract_activation_service import activate_contract
from kentender_procurement.services.contract_approval_signature_services import (
	approve_contract,
	approve_contract_review_step,
	submit_contract_for_review,
)
from kentender_procurement.services.contract_from_award import create_contract_from_award
from kentender_procurement.services.award_approval_services import final_approve_award, submit_award_for_approval
from kentender_procurement.services.award_from_evaluation import create_award_decision_from_evaluation
from kentender_procurement.services.evaluation_aggregation import aggregate_evaluation_results
from kentender_procurement.services.evaluation_report_services import (
	generate_evaluation_report,
	submit_evaluation_report,
)

PC = "Procurement Contract"
AD = "Award Decision"
TENDER = "Tender"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
EAR = "Evaluation Aggregation Result"
ERPT = "Evaluation Report"
PREFIX = "_KT_PCWF"


def _cleanup_pcwf():
	for name in frappe.get_all(
		"KenTender Approval Route Instance",
		filters={"reference_docname": ("like", f"{PREFIX}%")},
		pluck="name",
	):
		try:
			frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
		except Exception:
			pass
	frappe.db.delete("KenTender Approval Action", {"reference_docname": ("like", f"{PREFIX}%")})
	for pol_code, tpl_code in (
		(f"{PREFIX}_POL", f"{PREFIX}_TPL"),
		(f"{PREFIX}_AWPOL", f"{PREFIX}_AWTPL"),
	):
		if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
			frappe.delete_doc("KenTender Workflow Policy", pol_code, force=True, ignore_permissions=True)
		if frappe.db.exists("KenTender Approval Route Template", {"template_code": tpl_code}):
			frappe.delete_doc("KenTender Approval Route Template", tpl_code, force=True, ignore_permissions=True)

	for pc in frappe.get_all(PC, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in ("Procurement Contract Signing Record", "Procurement Contract Approval Record"):
			for row in frappe.get_all(dt, filters={"procurement_contract": pc}, pluck="name") or []:
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
		# Append-only audit trail: on_trash blocks delete_doc; test cleanup uses direct DB delete.
		frappe.db.delete("Procurement Contract Status Event", {"procurement_contract": pc})
		frappe.delete_doc(PC, pc, force=True, ignore_permissions=True)
	for ad_name in frappe.get_all(AD, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for dt in ("Award Return Record", "Award Approval Record"):
			for row in frappe.get_all(dt, filters={"award_decision": ad_name}, pluck="name") or []:
				frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
		frappe.delete_doc(AD, ad_name, force=True, ignore_permissions=True)
	for es_name in frappe.get_all(ES, filters={"business_id": ("like", f"{PREFIX}%")}, pluck="name") or []:
		for row in frappe.get_all(ERPT, filters={"evaluation_session": es_name}, pluck="name") or []:
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
	frappe.db.delete("Budget Control Period", {"name": ("like", f"{PREFIX}%")})
	frappe.db.delete("Procuring Entity", {"entity_code": f"{PREFIX}_PE"})


def _ensure_policy(doctype: str, pol_code: str, tpl_code: str, *, n_steps: int) -> None:
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		return
	steps = []
	for i in range(n_steps):
		steps.append(
			{
				"doctype": "KenTender Approval Route Template Step",
				"step_order": i + 1,
				"step_name": f"C{i + 1}",
				"actor_type": "Role",
				"role_required": "System Manager",
			}
		)
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": tpl_code,
			"template_name": f"PCWF {doctype} {n_steps}",
			"object_type": doctype,
			"steps": steps,
		}
	)
	tpl.insert()
	pol = frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": pol_code,
			"applies_to_doctype": doctype,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	)
	pol.insert()


class TestContractWorkflowEngine(FrappeTestCase):
	def setUp(self):
		super().setUp()
		self.currency = _ensure_test_currency()
		run_test_db_cleanup(_cleanup_pcwf)
		self.entity = _make_entity(f"{PREFIX}_PE").insert()
		self.period = _bcp(f"{PREFIX}_BCP", self.entity.name).insert()

	def tearDown(self):
		run_test_db_cleanup(_cleanup_pcwf)
		super().tearDown()

	def _award_and_contract(self, suffix: str):
		t = frappe.get_doc(
			{
				"doctype": TENDER,
				"name": f"{PREFIX}_T{suffix}",
				"business_id": f"{PREFIX}_T{suffix}-BIZ",
				"title": "PCWF",
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
		_ensure_policy(AD, f"{PREFIX}_AWPOL", f"{PREFIX}_AWTPL", n_steps=1)
		submit_award_for_approval(ad.name)
		final_approve_award(ad.name)
		c = create_contract_from_award(ad.name, business_id=f"{PREFIX}_PC{suffix}")
		return frappe.get_doc(PC, c["name"])

	def test_one_step_submit_approve(self):
		_ensure_policy(PC, f"{PREFIX}_POL", f"{PREFIX}_TPL", n_steps=1)
		pc = self._award_and_contract("1")
		submit_contract_for_review(pc.name)
		pc.reload()
		self.assertEqual(pc.workflow_state, "In Review")
		approve_contract(pc.name)
		pc.reload()
		self.assertEqual(pc.workflow_state, "Pending Signature")
		self.assertEqual(pc.approval_status, "Approved")

	def test_two_step_review_then_final(self):
		_ensure_policy(PC, f"{PREFIX}_POL", f"{PREFIX}_TPL", n_steps=2)
		pc = self._award_and_contract("2")
		submit_contract_for_review(pc.name)
		approve_contract_review_step(pc.name, workflow_step="C1", decision_level="L1")
		pc.reload()
		self.assertEqual(pc.workflow_state, "Pending Approval")
		approve_contract(pc.name)
		pc.reload()
		self.assertEqual(pc.workflow_state, "Pending Signature")

	def test_activate_requires_signature_evidence(self):
		_ensure_policy(PC, f"{PREFIX}_POL", f"{PREFIX}_TPL", n_steps=1)
		pc = self._award_and_contract("3")
		submit_contract_for_review(pc.name)
		approve_contract(pc.name)
		with self.assertRaises(frappe.ValidationError):
			activate_contract(pc.name)

	def test_direct_workflow_save_blocked_after_submit(self):
		_ensure_policy(PC, f"{PREFIX}_POL", f"{PREFIX}_TPL", n_steps=1)
		pc = self._award_and_contract("4")
		submit_contract_for_review(pc.name)
		pc.reload()
		with self.assertRaises(frappe.ValidationError):
			pc.workflow_state = "Active"
			pc.save(ignore_permissions=True)

	def test_mutation_context_allows_contract_save(self):
		_ensure_policy(PC, f"{PREFIX}_POL", f"{PREFIX}_TPL", n_steps=1)
		pc = self._award_and_contract("5")
		submit_contract_for_review(pc.name)
		pc.reload()
		with workflow_mutation_context():
			pc.workflow_state = "Draft"
			pc.save(ignore_permissions=True)
