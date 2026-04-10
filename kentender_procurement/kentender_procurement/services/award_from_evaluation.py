# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Create Award Decision from a submitted evaluation report (PROC-STORY-080)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender.services.audit_event_service import log_audit_event

AD = "Award Decision"
ERPT = "Evaluation Report"
ES = "Evaluation Session"
EAR = "Evaluation Aggregation Result"
BS = "Bid Submission"

SOURCE_MODULE = "kentender_procurement.award_from_evaluation"
EVT_CREATED = "award.decision.created_from_evaluation"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _procuring_entity_for_tender(tender_id: str) -> str | None:
	if not tender_id:
		return None
	return frappe.db.get_value("Tender", tender_id, "procuring_entity")


def create_award_decision_from_evaluation(
	evaluation_session_id: str,
	*,
	business_id: str | None = None,
) -> dict[str, Any]:
	"""Draft **Award Decision** from a locked (submitted) evaluation report for the session.

	Does not final-approve. Copies recommendation fields and builds outcome lines from aggregation.
	"""
	sn = _norm(evaluation_session_id)
	if not sn or not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	reports = (
		frappe.get_all(
			ERPT,
			filters={"evaluation_session": sn},
			fields=["name", "status", "tender", "recommended_bid_submission", "recommended_supplier", "recommended_amount", "currency"],
			order_by="modified desc",
		)
		or []
	)
	if not reports:
		frappe.throw(
			_("No evaluation report exists for this session."),
			frappe.ValidationError,
			title=_("Missing report"),
		)
	rep_row = reports[0]
	if _norm(rep_row.get("status")) != "Locked":
		frappe.throw(
			_("Evaluation report must be submitted (locked) before creating an award."),
			frappe.ValidationError,
			title=_("Report not submitted"),
		)
	rn = _norm(rep_row.get("name"))
	tender = _norm(rep_row.get("tender"))

	existing = frappe.get_all(AD, filters={"evaluation_report": rn}, pluck="name", limit=1)
	if existing:
		frappe.throw(
			_("An award decision already exists for this evaluation report."),
			frappe.ValidationError,
			title=_("Duplicate award"),
		)

	biz = _norm(business_id) or f"AWD-{_norm(frappe.db.get_value(ES, sn, 'business_id')) or sn[:12]}"

	doc = frappe.new_doc(AD)
	doc.business_id = biz
	doc.tender = tender
	doc.evaluation_session = sn
	doc.evaluation_report = rn
	doc.decision_justification = "Created from submitted evaluation report."
	doc.recommended_bid_submission = _norm(rep_row.get("recommended_bid_submission")) or None
	doc.recommended_supplier = _norm(rep_row.get("recommended_supplier")) or None
	doc.recommended_amount = rep_row.get("recommended_amount")
	doc.currency = _norm(rep_row.get("currency")) or None

	resp, nonr, disq = _ear_counts(sn)
	doc.responsive_bid_count = resp
	doc.non_responsive_bid_count = nonr
	doc.disqualified_bid_count = disq

	for line in _outcome_lines_from_aggregation(sn, tender):
		doc.append("outcome_lines", line)

	doc.insert(ignore_permissions=True)

	pe = _procuring_entity_for_tender(tender)
	ts = now_datetime()
	log_audit_event(
		event_type=EVT_CREATED,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=AD,
		target_docname=doc.name,
		procuring_entity=pe,
		new_state=json.dumps({"evaluation_session": sn, "evaluation_report": rn}),
		reason=_("Award decision created from evaluation"),
		event_datetime=ts,
	)

	return {"name": doc.name, "business_id": doc.business_id}


def _ear_counts(session_id: str) -> tuple[int, int, int]:
	rows = frappe.get_all(EAR, filters={"evaluation_session": session_id}, fields=["preliminary_result"]) or []
	resp = nonr = disq = 0
	for r in rows:
		p = _norm(r.get("preliminary_result"))
		if p == "Disqualified":
			disq += 1
		elif p == "Non-Responsive":
			nonr += 1
		else:
			resp += 1
	return resp, nonr, disq


def _outcome_lines_from_aggregation(session_id: str, tender_id: str) -> list[dict[str, Any]]:
	rows = (
		frappe.get_all(
			EAR,
			filters={"evaluation_session": session_id, "calculation_status": "Complete"},
			fields=[
				"bid_submission",
				"supplier",
				"preliminary_result",
				"ranking_position",
				"combined_score",
			],
		)
		or []
	)

	def sort_key(r: dict[str, Any]) -> tuple[int, int]:
		rp = r.get("ranking_position")
		if rp is None:
			return (1, 9999)
		try:
			return (0, int(rp))
		except (TypeError, ValueError):
			return (1, 9999)

	rows.sort(key=sort_key)
	out: list[dict[str, Any]] = []
	for r in rows:
		bid = _norm(r.get("bid_submission"))
		sup = _norm(r.get("supplier"))
		if not bid or not sup:
			continue
		pr = _norm(r.get("preliminary_result"))
		rp = r.get("ranking_position")
		try:
			rpi = int(rp) if rp is not None else None
		except (TypeError, ValueError):
			rpi = None
		if pr == "Disqualified":
			ot = "Unsuccessful"
		elif rpi == 1:
			ot = "Awarded"
		else:
			ot = "Unsuccessful"
		amt = frappe.db.get_value(BS, bid, "quoted_total_amount")
		out.append(
			{
				"bid_submission": bid,
				"supplier": sup,
				"outcome_type": ot,
				"evaluated_amount": amt,
				"ranking_position": rpi,
			}
		)
	return out
