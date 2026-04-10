# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation report generation and submission (PROC-STORY-071).

Requires **Evaluation Aggregation Result** rows with ``calculation_status == Complete`` (PROC-STORY-070).
Does not create Award Decision (PROC-STORY-073+).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender.services.audit_event_service import log_audit_event

EAR = "Evaluation Aggregation Result"
ERPT = "Evaluation Report"
ES = "Evaluation Session"
EASR = "Evaluation Approval Submission Record"
BS = "Bid Submission"

SOURCE_MODULE = "kentender_procurement.evaluation_report_services"
EVT_GENERATED = "evaluation.report.generated"
EVT_SUBMITTED = "evaluation.report.submitted"
EVT_RETURNED = "evaluation.report.returned_for_revision"

_CALC_COMPLETE = "Complete"
_ACTION_SUBMIT = "Submit"
_ACTION_RETURN = "Return for Revision"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _procuring_entity_for_session(session_id: str) -> str | None:
	tn = frappe.db.get_value(ES, session_id, "tender")
	if not tn:
		return None
	return frappe.db.get_value("Tender", tn, "procuring_entity")


def _assert_aggregation_finalized(evaluation_session_id: str) -> None:
	sn = _norm(evaluation_session_id)
	rows = frappe.get_all(EAR, filters={"evaluation_session": sn}, fields=["name", "calculation_status"]) or []
	if not rows:
		frappe.throw(
			_("No aggregation results exist for this evaluation session."),
			frappe.ValidationError,
			title=_("Missing aggregation"),
		)
	for r in rows:
		if _norm(r.get("calculation_status")) != _CALC_COMPLETE:
			frappe.throw(
				_("Aggregation must be complete before this action."),
				frappe.ValidationError,
				title=_("Aggregation incomplete"),
			)


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


def _winning_bid_name(session_id: str) -> str | None:
	rows = (
		frappe.get_all(
			EAR,
			filters={"evaluation_session": session_id, "ranking_position": 1},
			fields=["bid_submission", "preliminary_result"],
			limit=1,
		)
		or []
	)
	if not rows:
		return None
	if _norm(rows[0].get("preliminary_result")) == "Disqualified":
		return None
	return _norm(rows[0].get("bid_submission"))


def generate_evaluation_report(
	evaluation_session_id: str,
	*,
	business_id: str | None = None,
) -> dict[str, Any]:
	"""Create or refresh a draft evaluation report from finalized aggregation."""
	sn = _norm(evaluation_session_id)
	if not sn or not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	_assert_aggregation_finalized(sn)
	tender = _norm(frappe.db.get_value(ES, sn, "tender"))
	if not tender:
		frappe.throw(_("Evaluation Session has no tender."), frappe.ValidationError, title=_("Missing tender"))

	resp, nonr, disq = _ear_counts(sn)
	win = _winning_bid_name(sn)

	existing = frappe.get_all(ERPT, filters={"evaluation_session": sn}, pluck="name", limit=1)
	bid = _norm(win)
	supplier = _norm(frappe.db.get_value(BS, bid, "supplier")) if bid else ""
	amt = frappe.db.get_value(BS, bid, "quoted_total_amount") if bid else None
	cur = frappe.db.get_value("Tender", tender, "currency") if tender else None

	just = "<p>Auto-generated from aggregation results (PROC-STORY-071).</p>"
	if bid:
		just += "<p>Recommended bid selected by ranking position.</p>"

	fields = {
		"evaluation_session": sn,
		"tender": tender,
		"status": "Draft",
		"responsive_bid_count": resp,
		"non_responsive_bid_count": nonr,
		"disqualified_bid_count": disq,
		"process_summary": "<p>Evaluation process summary (draft).</p>",
		"recommendation_justification": just,
	}
	if bid:
		fields["recommended_bid_submission"] = bid
		fields["recommended_supplier"] = supplier
		if amt is not None:
			fields["recommended_amount"] = amt
	if cur:
		fields["currency"] = cur

	ts = now_datetime()
	if existing:
		doc = frappe.get_doc(ERPT, existing[0])
		if _norm(doc.status) in ("Locked", "Cancelled"):
			frappe.throw(
				_("Cannot regenerate a locked or cancelled evaluation report."),
				frappe.ValidationError,
				title=_("Report locked"),
			)
		for k, v in fields.items():
			if k in ("evaluation_session", "tender"):
				continue
			setattr(doc, k, v)
		doc.save(ignore_permissions=True)
		name = doc.name
	else:
		bid_id = _norm(business_id) or f"ERP-{sn[:8]}"
		fields["doctype"] = ERPT
		fields["business_id"] = bid_id
		doc = frappe.get_doc(fields)
		doc.insert(ignore_permissions=True)
		name = doc.name

	pe = _procuring_entity_for_session(sn)
	log_audit_event(
		event_type=EVT_GENERATED,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=ERPT,
		target_docname=name,
		procuring_entity=pe,
		new_state=json.dumps({"evaluation_session": sn, "report": name}),
		reason=_("Evaluation report generated from aggregation"),
		event_datetime=ts,
	)

	return {"name": name, "evaluation_session": sn, "recommended_bid_submission": bid or None}


def _report_locked_hash_payload(doc) -> str:
	parts = {
		"business_id": _norm(doc.business_id),
		"evaluation_session": _norm(doc.evaluation_session),
		"recommended_bid_submission": _norm(doc.recommended_bid_submission),
		"responsive_bid_count": doc.responsive_bid_count,
		"non_responsive_bid_count": doc.non_responsive_bid_count,
		"disqualified_bid_count": doc.disqualified_bid_count,
	}
	return json.dumps(parts, sort_keys=True)


def _insert_submission_record(
	evaluation_session: str,
	report_name: str,
	action_type: str,
	comments: str | None = None,
) -> None:
	role = (frappe.get_roles(_norm(frappe.session.user)) or ["Guest"])[0]
	frappe.get_doc(
		{
			"doctype": EASR,
			"evaluation_session": evaluation_session,
			"evaluation_report": report_name,
			"actor_user": _norm(frappe.session.user) or "Administrator",
			"actor_role": role,
			"action_type": action_type,
			"action_datetime": now_datetime(),
			"comments": _norm(comments) or None,
		}
	).insert(ignore_permissions=True)


def submit_evaluation_report(evaluation_report_id: str) -> dict[str, Any]:
	"""Lock report after aggregation is complete; append submission record and audit."""
	rn = _norm(evaluation_report_id)
	if not rn or not frappe.db.exists(ERPT, rn):
		frappe.throw(_("Evaluation Report not found."), frappe.ValidationError, title=_("Invalid report"))

	doc = frappe.get_doc(ERPT, rn)
	sn = _norm(doc.evaluation_session)
	_assert_aggregation_finalized(sn)

	st = _norm(doc.status)
	if st in ("Locked", "Cancelled"):
		frappe.throw(
			_("Evaluation report cannot be submitted in its current state."),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	ts = now_datetime()
	payload = _report_locked_hash_payload(doc)
	h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
	doc.status = "Locked"
	doc.submitted_by_user = _norm(frappe.session.user) or "Administrator"
	doc.submitted_on = ts
	doc.locked_hash = h
	doc.save(ignore_permissions=True)

	_insert_submission_record(sn, doc.name, _ACTION_SUBMIT)

	pe = _procuring_entity_for_session(sn)
	log_audit_event(
		event_type=EVT_SUBMITTED,
		actor=doc.submitted_by_user,
		source_module=SOURCE_MODULE,
		target_doctype=ERPT,
		target_docname=doc.name,
		procuring_entity=pe,
		new_state=json.dumps({"status": "Locked", "locked_hash": h[:16]}),
		reason=_("Evaluation report submitted"),
		event_datetime=ts,
	)

	return {"name": doc.name, "status": doc.status, "locked_hash": h}


def return_evaluation_for_revision(
	evaluation_report_id: str,
	*,
	comments: str | None = None,
) -> dict[str, Any]:
	"""Return a locked report for revision (append-only submission record)."""
	rn = _norm(evaluation_report_id)
	if not rn or not frappe.db.exists(ERPT, rn):
		frappe.throw(_("Evaluation Report not found."), frappe.ValidationError, title=_("Invalid report"))

	doc = frappe.get_doc(ERPT, rn)
	if _norm(doc.status) != "Locked":
		frappe.throw(
			_("Only a locked evaluation report can be returned for revision."),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	sn = _norm(doc.evaluation_session)
	ts = now_datetime()
	doc.status = "In Progress"
	doc.locked_hash = None
	doc.submitted_on = None
	doc.submitted_by_user = None
	doc.save(ignore_permissions=True)

	_insert_submission_record(sn, doc.name, _ACTION_RETURN, comments=comments)

	pe = _procuring_entity_for_session(sn)
	log_audit_event(
		event_type=EVT_RETURNED,
		actor=_norm(frappe.session.user) or "Administrator",
		source_module=SOURCE_MODULE,
		target_doctype=ERPT,
		target_docname=doc.name,
		procuring_entity=pe,
		new_state=json.dumps({"status": "In Progress"}),
		reason=_("Evaluation report returned for revision"),
		event_datetime=ts,
	)

	return {"name": doc.name, "status": doc.status}
