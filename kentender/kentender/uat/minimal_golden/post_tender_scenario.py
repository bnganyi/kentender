# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Minimal Golden — post-bid chain: publish tender, opening, evaluation, award, contract (E2E UAT seed)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, now_datetime

from kentender_procurement.services.award_approval_services import final_approve_award, submit_award_for_approval
from kentender_procurement.services.award_from_evaluation import create_award_decision_from_evaluation
from kentender_procurement.services.contract_activation_service import activate_contract
from kentender_procurement.services.contract_approval_signature_services import (
	approve_contract,
	record_contract_signature,
	send_contract_for_signature,
	submit_contract_for_review,
)
from kentender_procurement.services.contract_from_award import create_contract_from_award
from kentender_procurement.services.evaluation_aggregation import aggregate_evaluation_results
from kentender_procurement.services.evaluation_initialization import initialize_evaluation_session
from kentender_procurement.services.evaluation_report_services import generate_evaluation_report, submit_evaluation_report
from kentender_procurement.services.opening_execution import execute_bid_opening
from kentender_procurement.services.tender_publication_readiness import assess_tender_publication_readiness
from kentender_procurement.services.tender_workflow_actions import approve_tender, publish_tender, submit_tender_for_review

TENDER = "Tender"
TCR = "Tender Criteria"
TDOC = "Tender Document"
DTR = "Document Type Registry"
FILE = "File"
BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BS = "Bid Submission"
BR = "Bid Receipt"
ES = "Evaluation Session"
EST = "Evaluation Stage"
ER = "Evaluation Record"
ERPT = "Evaluation Report"
AD = "Award Decision"
PC = "Procurement Contract"
PCSE = "Procurement Contract Status Event"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _email_by_key(ds: dict[str, Any], key: str) -> str:
	for row in (ds.get("users") or {}).get("internal") or []:
		if row.get("key") == key and row.get("email"):
			return _norm(row["email"])
	return ""


def _ensure_document_type_registry() -> str:
	code = "MG-GOLD-DOC"
	if frappe.db.exists(DTR, code):
		return code
	frappe.get_doc(
		{
			"doctype": DTR,
			"document_type_code": code,
			"document_type_name": "Minimal Golden tender document",
		}
	).insert(ignore_permissions=True)
	return code


def ensure_tender_publication_prerequisites(tender_name: str) -> None:
	"""At least one Tender Criteria + Tender Document; DTR row for document type."""
	tn = _norm(tender_name)
	if not tn:
		return
	if frappe.db.count(TCR, {"tender": tn}) < 1:
		frappe.get_doc(
			{
				"doctype": TCR,
				"tender": tn,
				"criteria_type": "Technical",
				"criteria_code": "MG-1",
				"criteria_title": "Minimal Golden mandatory criterion",
				"score_type": "Numeric",
				"max_score": 100,
				"weight_percentage": 100,
				"minimum_pass_mark": 40,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)
	if frappe.db.count(TDOC, {"tender": tn}) < 1:
		dtr = _ensure_document_type_registry()
		fd = frappe.get_doc(
			{
				"doctype": FILE,
				"file_name": "minimal-golden-tender-spec.txt",
				"content": b"Minimal Golden tender specification placeholder.",
				"attached_to_doctype": TENDER,
				"attached_to_name": tn,
			}
		)
		fd.insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": TDOC,
				"tender": tn,
				"document_type": dtr,
				"document_title": "Specification",
				"document_version_no": 1,
				"attached_file": fd.name,
				"status": "Draft",
				"sensitivity_class": "Internal",
			}
		).insert(ignore_permissions=True)


def _align_tender_schedule_for_opening(tender_name: str) -> None:
	"""Publication → submission → opening chain in the past so opening preconditions pass."""
	now = now_datetime()
	pub = add_days(now, -30)
	clar = add_days(now, -20)
	subm = add_days(now, -5)
	opening = add_days(now, -4)
	frappe.db.set_value(
		TENDER,
		tender_name,
		{
			"publication_datetime": pub,
			"clarification_deadline": clar,
			"submission_deadline": subm,
			"opening_datetime": opening,
		},
		update_modified=False,
	)


def _ensure_workflow_policy_award() -> None:
	pol_code = "MG-GOLD-AWARD-POL"
	tpl_code = "MG-GOLD-AWARD-TPL"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		return
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": tpl_code,
			"template_name": "Minimal Golden Award 1-step",
			"object_type": AD,
			"steps": [
				{
					"doctype": "KenTender Approval Route Template Step",
					"step_order": 1,
					"step_name": "Final",
					"actor_type": "Role",
					"role_required": "System Manager",
				}
			],
		}
	)
	tpl.insert(ignore_permissions=True)
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
	pol.insert(ignore_permissions=True)


def _ensure_workflow_policy_contract() -> None:
	pol_code = "MG-GOLD-PC-POL"
	tpl_code = "MG-GOLD-PC-TPL"
	if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
		return
	tpl = frappe.get_doc(
		{
			"doctype": "KenTender Approval Route Template",
			"template_code": tpl_code,
			"template_name": "Minimal Golden Contract 1-step",
			"object_type": PC,
			"steps": [
				{
					"doctype": "KenTender Approval Route Template Step",
					"step_order": 1,
					"step_name": "Approve",
					"actor_type": "Role",
					"role_required": "System Manager",
				}
			],
		}
	)
	tpl.insert(ignore_permissions=True)
	pol = frappe.get_doc(
		{
			"doctype": "KenTender Workflow Policy",
			"policy_code": pol_code,
			"applies_to_doctype": PC,
			"linked_template": tpl.name,
			"active": 1,
			"evaluation_order": 1,
		}
	)
	pol.insert(ignore_permissions=True)


def _mark_bids_submitted_for_opening(ds: dict[str, Any], tender_name: str) -> list[str]:
	"""Set both golden bids to Submitted with receipt linkage (opening candidates)."""
	fut = ds.get("future_business_ids") or {}
	out: list[str] = []
	now = now_datetime()
	cur = _norm(ds.get("currency_code")) or "KES"
	for key in ("bid_1", "bid_2"):
		biz = _norm(fut.get(key))
		if not biz:
			continue
		bname = frappe.db.get_value(BS, {"business_id": biz}, "name")
		if not bname:
			continue
		br = frappe.db.get_value(BR, {"bid_submission": bname}, "name")
		frappe.db.set_value(
			BS,
			bname,
			{
				"workflow_state": "Submitted",
				"status": "Submitted",
				"is_final_submission": 1,
				"active_submission_flag": 1,
				"sealed_status": "Sealed",
				"submitted_on": now,
				"quoted_total_amount": 9000000.0 if key == "bid_1" else 8500000.0,
				"currency": cur,
				"receipt_no": frappe.db.get_value(BR, br, "receipt_no") if br else None,
			},
			update_modified=False,
		)
		out.append(bname)
	return out


def _insert_locked_evaluation_records(
	evaluation_session: str,
	bid_names: list[str],
	suppliers: list[str],
) -> None:
	"""Locked ER rows on Technical + Financial stages (Two Envelope)."""
	tech = (
		frappe.get_all(
			EST,
			filters={"evaluation_session": evaluation_session, "stage_type": "Technical Evaluation"},
			pluck="name",
			limit=1,
		)
		or []
	)
	fin = (
		frappe.get_all(
			EST,
			filters={"evaluation_session": evaluation_session, "stage_type": "Financial Evaluation"},
			pluck="name",
			limit=1,
		)
		or []
	)
	if not tech or not fin:
		frappe.throw("Minimal Golden: Technical/Financial evaluation stages not found.", frappe.ValidationError)
	ts = "2026-04-10 12:00:00"
	# bid_1 wins ranking: higher technical + balanced financial
	scores = ((90.0, 85.0), (80.0, 90.0))
	for i, bn in enumerate(bid_names[:2]):
		sup = suppliers[i] if i < len(suppliers) else _norm(frappe.db.get_value(BS, bn, "supplier"))
		tsc, fsc = scores[i]
		for stage_name, total, sfx in (
			(tech[0], tsc, "T"),
			(fin[0], fsc, "F"),
		):
			frappe.get_doc(
				{
					"doctype": ER,
					"business_id": f"MG-ER-{i + 1}-{sfx}",
					"evaluation_session": evaluation_session,
					"evaluation_stage": stage_name,
					"bid_submission": bn,
					"evaluator_user": frappe.session.user,
					"supplier": sup,
					"status": "Locked",
					"pass_fail_result": "Not Applicable",
					"total_stage_score": total,
					"submitted_on": ts,
					"locked_on": ts,
				}
			).insert(ignore_permissions=True)


def load_post_tender_scenario(ds: dict[str, Any]) -> dict[str, Any]:
	"""Run opening → evaluation → award → contract after bids/receipt exist. Idempotent if ES already seeded."""
	frappe.flags.ignore_permissions = True
	prev_user = frappe.session.user
	frappe.set_user("Administrator")

	try:
		t_spec = ds.get("tender") or {}
		t_name = _norm(t_spec.get("name"))
		fut = ds.get("future_business_ids") or {}
		evs_biz = _norm(fut.get("evaluation_session"))
		evr_biz = _norm(fut.get("evaluation_report"))
		awd_biz = _norm(fut.get("award_decision"))
		pc_biz = _norm(fut.get("contract"))
		bos_biz = _norm(fut.get("opening_session"))
		bor_biz = _norm(fut.get("opening_register"))

		if not t_name or not frappe.db.exists(TENDER, t_name):
			return {"skipped": True, "reason": "no_tender"}

		if evs_biz and frappe.db.exists(ES, {"business_id": evs_biz}):
			esn = frappe.db.get_value(ES, {"business_id": evs_biz}, "name")
			pcn = frappe.db.get_value(PC, {"business_id": pc_biz}, "name") if pc_biz else None
			return {"skipped": True, "reason": "already_seeded", "evaluation_session": esn, "procurement_contract": pcn}

		proc_email = _email_by_key(ds, "procurement") or "Administrator"

		_align_tender_schedule_for_opening(t_name)
		ensure_tender_publication_prerequisites(t_name)
		ready = assess_tender_publication_readiness(t_name)
		if not ready.get("ok"):
			frappe.throw(
				"Tender not ready to publish: " + "; ".join(ready.get("reasons") or []),
				frappe.ValidationError,
			)

		frappe.set_user(proc_email)
		submit_tender_for_review(t_name, user=proc_email)
		approve_tender(t_name, user=proc_email)
		publish_tender(t_name, user=proc_email)
		frappe.set_user("Administrator")

		_bid_names = _mark_bids_submitted_for_opening(ds, t_name)
		if len(_bid_names) < 1:
			frappe.throw("Minimal Golden: no submitted bids for opening.", frappe.ValidationError)

		ent = frappe.db.get_value(TENDER, t_name, "procuring_entity")
		if bos_biz and not frappe.db.exists(BOS, {"business_id": bos_biz}):
			frappe.get_doc(
				{
					"doctype": BOS,
					"business_id": bos_biz,
					"tender": t_name,
					"procuring_entity": ent,
					"status": "Draft",
					"workflow_state": "Draft",
				}
			).insert(ignore_permissions=True)

		bos_name = frappe.db.get_value(BOS, {"business_id": bos_biz}, "name") if bos_biz else None
		if not bos_name:
			frappe.throw("Minimal Golden: Bid Opening Session missing.", frappe.ValidationError)

		ex = execute_bid_opening(bos_name, actor_user="Administrator")
		reg_name = _norm(ex.get("register"))
		if bor_biz and reg_name:
			frappe.db.set_value(BOR, reg_name, "business_id", bor_biz, update_modified=False)

		init = initialize_evaluation_session(
			opening_session_id=bos_name,
			business_id=evs_biz or None,
			evaluation_mode="Two Envelope",
		)
		es_name = _norm(init.get("evaluation_session"))
		suppliers = [
			_norm(frappe.db.get_value(BS, bn, "supplier")) for bn in _bid_names[:2]
		]
		_insert_locked_evaluation_records(es_name, _bid_names, suppliers)

		aggregate_evaluation_results(es_name, technical_weight=0.7, financial_weight=0.3)

		rep = generate_evaluation_report(es_name, business_id=evr_biz or None)
		submit_evaluation_report(rep["name"])

		_ensure_workflow_policy_award()
		aw_out = create_award_decision_from_evaluation(es_name, business_id=awd_biz or None)
		ad = frappe.get_doc(AD, aw_out["name"])
		ad.approved_bid_submission = ad.recommended_bid_submission
		ad.approved_supplier = ad.recommended_supplier
		ad.approved_amount = ad.recommended_amount
		ad.standstill_required = 0
		ad.save(ignore_permissions=True)
		submit_award_for_approval(ad.name)
		final_approve_award(ad.name)

		_ensure_workflow_policy_contract()
		c_out = create_contract_from_award(ad.name, business_id=pc_biz or None)
		cn = _norm(c_out.get("name"))
		submit_contract_for_review(cn)
		approve_contract(cn)
		send_contract_for_signature(cn)
		record_contract_signature(cn, hash_value="sha256:minimal_golden_contract_signature_v1")
		act = activate_contract(cn)

		return {
			"opening_session": bos_name,
			"opening_register": reg_name,
			"evaluation_session": es_name,
			"evaluation_report": rep.get("name"),
			"award_decision": ad.name,
			"procurement_contract": cn,
			"contract_status": act.get("status"),
		}
	finally:
		frappe.set_user(prev_user)


def delete_post_tender_scenario(ds: dict[str, Any]) -> None:
	"""Remove E2E post-tender rows for Minimal Golden (before tender/bids). Safe if missing."""
	from kentender.services.audit_event_service import AUDIT_EVENT_DOCTYPE

	t_name = _norm((ds.get("tender") or {}).get("name"))
	fut = ds.get("future_business_ids") or {}
	pc_biz = _norm(fut.get("contract"))
	awd_biz = _norm(fut.get("award_decision"))
	evs_biz = _norm(fut.get("evaluation_session"))

	frappe.flags.allow_contract_status_event_delete = True
	frappe.flags.allow_evaluation_approval_submission_record_delete = True
	try:
		# Contract + workflow
		pc_name = None
		if pc_biz:
			pc_name = frappe.db.get_value(PC, {"business_id": pc_biz}, "name")
		if not pc_name and t_name:
			pc_name = frappe.db.get_value(PC, {"tender": t_name, "award_decision": ("!=", "")}, "name")
		if pc_name:
			for name in frappe.get_all(
				"KenTender Approval Route Instance",
				filters={"reference_doctype": PC, "reference_docname": pc_name},
				pluck="name",
			) or []:
				try:
					frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
				except Exception:
					pass
			frappe.db.delete(
				"KenTender Approval Action",
				{"reference_doctype": PC, "reference_docname": pc_name},
			)
			for dt in ("Procurement Contract Signing Record", "Procurement Contract Approval Record"):
				for ch in frappe.get_all(dt, filters={"procurement_contract": pc_name}, pluck="name") or []:
					frappe.delete_doc(dt, ch, force=True, ignore_permissions=True)
			frappe.db.delete(PCSE, {"procurement_contract": pc_name})
			frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": PC, "target_docname": pc_name})
			frappe.delete_doc(PC, pc_name, force=True, ignore_permissions=True)

		# Award
		ad_name = None
		if awd_biz:
			ad_name = frappe.db.get_value(AD, {"business_id": awd_biz}, "name")
		if not ad_name and t_name:
			ad_name = frappe.db.get_value(AD, {"tender": t_name}, "name")
		if ad_name:
			for name in frappe.get_all(
				"KenTender Approval Route Instance",
				filters={"reference_doctype": AD, "reference_docname": ad_name},
				pluck="name",
			) or []:
				try:
					frappe.delete_doc("KenTender Approval Route Instance", name, force=True, ignore_permissions=True)
				except Exception:
					pass
			frappe.db.delete(
				"KenTender Approval Action",
				{"reference_doctype": AD, "reference_docname": ad_name},
			)
			for ch in frappe.get_all("Award Approval Record", filters={"award_decision": ad_name}, pluck="name") or []:
				frappe.delete_doc("Award Approval Record", ch, force=True, ignore_permissions=True)
			frappe.delete_doc(AD, ad_name, force=True, ignore_permissions=True)

		# Evaluation tree
		es_name = None
		if evs_biz:
			es_name = frappe.db.get_value(ES, {"business_id": evs_biz}, "name")
		if not es_name and t_name:
			r = frappe.get_all(ES, filters={"tender": t_name}, pluck="name", limit=1)
			es_name = r[0] if r else None
		if es_name:
			for row in frappe.get_all(
				"Evaluation Approval Submission Record",
				filters={"evaluation_session": es_name},
				pluck="name",
			) or []:
				frappe.delete_doc("Evaluation Approval Submission Record", row, force=True, ignore_permissions=True)
			for row in frappe.get_all(ERPT, filters={"evaluation_session": es_name}, pluck="name") or []:
				frappe.db.delete(AUDIT_EVENT_DOCTYPE, {"target_doctype": ERPT, "target_docname": row})
				frappe.delete_doc(ERPT, row, force=True, ignore_permissions=True)
			for row in frappe.get_all("Evaluation Aggregation Result", filters={"evaluation_session": es_name}, pluck="name") or []:
				frappe.delete_doc("Evaluation Aggregation Result", row, force=True, ignore_permissions=True)
			for row in frappe.get_all(ER, filters={"evaluation_session": es_name}, pluck="name") or []:
				frappe.delete_doc(ER, row, force=True, ignore_permissions=True)
			for st in frappe.get_all(EST, filters={"evaluation_session": es_name}, pluck="name") or []:
				frappe.delete_doc(EST, st, force=True, ignore_permissions=True)
			frappe.delete_doc(ES, es_name, force=True, ignore_permissions=True)

		# Opening
		if t_name:
			for sn in frappe.get_all(BOS, filters={"tender": t_name}, pluck="name") or []:
				frappe.db.delete("Bid Opening Event Log", {"bid_opening_session": sn})
				for rn in frappe.get_all(BOR, filters={"bid_opening_session": sn}, pluck="name") or []:
					frappe.delete_doc(BOR, rn, force=True, ignore_permissions=True)
				frappe.delete_doc(BOS, sn, force=True, ignore_permissions=True)

		# Tender publication helpers
		if t_name:
			for dt in (TCR, TDOC):
				for row in frappe.get_all(dt, filters={"tender": t_name}, pluck="name") or []:
					frappe.delete_doc(dt, row, force=True, ignore_permissions=True)
			for fn in (
				frappe.get_all(
					FILE,
					filters={"attached_to_doctype": TENDER, "attached_to_name": t_name, "file_name": ("like", "minimal-golden%")},
					pluck="name",
				)
				or []
			):
				try:
					frappe.delete_doc(FILE, fn, force=True, ignore_permissions=True)
				except Exception:
					pass

		# Workflow policies (idempotent re-seed)
		for pol_code in ("MG-GOLD-AWARD-POL", "MG-GOLD-PC-POL"):
			if frappe.db.exists("KenTender Workflow Policy", {"policy_code": pol_code}):
				frappe.delete_doc("KenTender Workflow Policy", pol_code, force=True, ignore_permissions=True)
		for tpl_code in ("MG-GOLD-AWARD-TPL", "MG-GOLD-PC-TPL"):
			if frappe.db.exists("KenTender Approval Route Template", {"template_code": tpl_code}):
				frappe.delete_doc("KenTender Approval Route Template", tpl_code, force=True, ignore_permissions=True)

		if frappe.db.exists(DTR, "MG-GOLD-DOC"):
			try:
				frappe.delete_doc(DTR, "MG-GOLD-DOC", force=True, ignore_permissions=True)
			except Exception:
				pass
	finally:
		frappe.flags.allow_contract_status_event_delete = False
		frappe.flags.allow_evaluation_approval_submission_record_delete = False
