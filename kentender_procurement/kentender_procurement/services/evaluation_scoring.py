# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluation scoring submission and stage progression (PROC-STORY-069).

Aggregation and ranking remain in PROC-STORY-070. Mutations are server-side; use
:func:`validate_evaluator_access` for assignment and COI clearance.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from kentender.services.audit_event_service import log_audit_event

from kentender_procurement.services.evaluator_access import validate_evaluator_access

ER = "Evaluation Record"
EST = "Evaluation Stage"
EDR = "Evaluation Disqualification Record"
ES = "Evaluation Session"

SOURCE_MODULE = "kentender_procurement.evaluation_scoring"

EVT_RECORD_SUBMITTED = "evaluation.record.submitted"
EVT_STAGE_STARTED = "evaluation.stage.started"
EVT_STAGE_COMPLETED = "evaluation.stage.completed"
EVT_DQ_PROPOSED = "evaluation.disqualification.proposed"
EVT_DQ_CONFIRMED = "evaluation.disqualification.confirmed"

_STATUS_DRAFT = "Draft"
_STATUS_IN_PROGRESS = "In Progress"
_STATUS_SUBMITTED = "Submitted"
_STATUS_LOCKED = "Locked"
_STATUS_CANCELLED = "Cancelled"

_STAGE_DRAFT = "Draft"
_STAGE_IN_PROGRESS = "In Progress"
_STAGE_COMPLETED = "Completed"
_STAGE_SKIPPED = "Skipped"

_EDR_PROPOSED = "Proposed"
_EDR_CONFIRMED = "Confirmed"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _json_state(**kwargs: Any) -> str:
	return json.dumps(kwargs, sort_keys=True, default=str)


def _procuring_entity_for_session(session_id: str) -> str | None:
	tn = frappe.db.get_value(ES, session_id, "tender")
	if not tn:
		return None
	return frappe.db.get_value("Tender", tn, "procuring_entity")


def submit_evaluation_record(record_id: str) -> dict[str, Any]:
	"""Submit and lock an evaluation record for the current user."""
	rn = _norm(record_id)
	if not rn:
		frappe.throw(_("Evaluation record is required."), frappe.ValidationError, title=_("Missing record"))
	if not frappe.db.exists(ER, rn):
		frappe.throw(_("Evaluation Record not found."), frappe.ValidationError, title=_("Invalid record"))

	doc = frappe.get_doc(ER, rn)
	su = _norm(frappe.session.user)
	if _norm(doc.evaluator_user) != su:
		frappe.throw(
			_("Only the assigned evaluator can submit this evaluation record."),
			frappe.ValidationError,
			title=_("Not your record"),
		)

	validate_evaluator_access(doc.evaluation_session, su, bid_submission=_norm(doc.bid_submission))

	st = _norm(doc.status)
	if st in (_STATUS_SUBMITTED, _STATUS_LOCKED, _STATUS_CANCELLED):
		frappe.throw(
			_("Evaluation record cannot be submitted in its current state."),
			frappe.ValidationError,
			title=_("Invalid status"),
		)
	if st not in (_STATUS_DRAFT, _STATUS_IN_PROGRESS):
		frappe.throw(
			_("Evaluation record cannot be submitted in its current state."),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	old_status = st
	ts = now_datetime()
	doc.status = _STATUS_LOCKED
	doc.submitted_on = ts
	doc.locked_on = ts
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_session(doc.evaluation_session)
	log_audit_event(
		event_type=EVT_RECORD_SUBMITTED,
		actor=su,
		source_module=SOURCE_MODULE,
		target_doctype=ER,
		target_docname=doc.name,
		procuring_entity=pe or None,
		old_state=_json_state(status=old_status),
		new_state=_json_state(status=_STATUS_LOCKED, submitted_on=str(ts), locked_on=str(ts)),
		changed_fields_summary="status,submitted_on,locked_on",
		reason=_("Evaluation record submitted and locked"),
		event_datetime=ts,
	)

	return {"name": doc.name, "status": doc.status}


def _validate_prior_stages_completed_or_skipped(session_id: str, stage_order: int) -> None:
	if stage_order <= 1:
		return
	priors = (
		frappe.get_all(
			EST,
			filters={"evaluation_session": session_id, "stage_order": ("<", stage_order)},
			fields=["name", "status", "stage_order"],
		)
		or []
	)
	for row in priors:
		st = _norm(row.get("status"))
		if st not in (_STAGE_COMPLETED, _STAGE_SKIPPED):
			frappe.throw(
				_("Earlier evaluation stages must be completed or skipped before starting this stage."),
				frappe.ValidationError,
				title=_("Stage ordering"),
			)


def start_evaluation_stage(stage_id: str) -> dict[str, Any]:
	"""Move a stage from Draft to In Progress when ordering rules pass."""
	sn = _norm(stage_id)
	if not sn:
		frappe.throw(_("Evaluation stage is required."), frappe.ValidationError, title=_("Missing stage"))
	if not frappe.db.exists(EST, sn):
		frappe.throw(_("Evaluation Stage not found."), frappe.ValidationError, title=_("Invalid stage"))

	doc = frappe.get_doc(EST, sn)
	su = _norm(frappe.session.user)
	validate_evaluator_access(doc.evaluation_session, su)

	st = _norm(doc.status)
	if st != _STAGE_DRAFT:
		frappe.throw(
			_("Evaluation stage cannot be started in its current state."),
			frappe.ValidationError,
			title=_("Invalid stage status"),
		)

	order = int(doc.stage_order or 0)
	_validate_prior_stages_completed_or_skipped(doc.evaluation_session, order)

	old_status = st
	ts = now_datetime()
	doc.status = _STAGE_IN_PROGRESS
	if not doc.started_on:
		doc.started_on = ts
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_session(doc.evaluation_session)
	log_audit_event(
		event_type=EVT_STAGE_STARTED,
		actor=su,
		source_module=SOURCE_MODULE,
		target_doctype=EST,
		target_docname=doc.name,
		procuring_entity=pe or None,
		old_state=_json_state(status=old_status),
		new_state=_json_state(status=_STAGE_IN_PROGRESS, started_on=str(doc.started_on)),
		changed_fields_summary="status,started_on",
		reason=_("Evaluation stage started"),
		event_datetime=ts,
	)

	return {"name": doc.name, "status": doc.status}


def _scoring_stage_has_open_records(stage_name: str) -> bool:
	rows = (
		frappe.get_all(
			ER,
			filters={
				"evaluation_stage": stage_name,
				"status": ("in", [_STATUS_DRAFT, _STATUS_IN_PROGRESS]),
			},
			pluck="name",
			limit=1,
		)
		or []
	)
	return bool(rows)


def complete_evaluation_stage(stage_id: str) -> dict[str, Any]:
	"""Complete an in-progress stage; scoring stages require no open evaluation records."""
	sn = _norm(stage_id)
	if not sn:
		frappe.throw(_("Evaluation stage is required."), frappe.ValidationError, title=_("Missing stage"))
	if not frappe.db.exists(EST, sn):
		frappe.throw(_("Evaluation Stage not found."), frappe.ValidationError, title=_("Invalid stage"))

	doc = frappe.get_doc(EST, sn)
	su = _norm(frappe.session.user)
	validate_evaluator_access(doc.evaluation_session, su)

	st = _norm(doc.status)
	if st != _STAGE_IN_PROGRESS:
		frappe.throw(
			_("Evaluation stage cannot be completed in its current state."),
			frappe.ValidationError,
			title=_("Invalid stage status"),
		)
	if not doc.started_on:
		frappe.throw(
			_("Evaluation stage has no start time."),
			frappe.ValidationError,
			title=_("Missing started on"),
		)

	if cint(doc.is_scoring_stage) and _scoring_stage_has_open_records(doc.name):
		frappe.throw(
			_("All evaluation records for this stage must be submitted before completing the stage."),
			frappe.ValidationError,
			title=_("Open evaluation records"),
		)

	old_status = st
	ts = now_datetime()
	doc.status = _STAGE_COMPLETED
	doc.completed_on = ts
	doc.save(ignore_permissions=True)

	pe = _procuring_entity_for_session(doc.evaluation_session)
	log_audit_event(
		event_type=EVT_STAGE_COMPLETED,
		actor=su,
		source_module=SOURCE_MODULE,
		target_doctype=EST,
		target_docname=doc.name,
		procuring_entity=pe or None,
		old_state=_json_state(status=old_status),
		new_state=_json_state(status=_STAGE_COMPLETED, completed_on=str(ts)),
		changed_fields_summary="status,completed_on",
		reason=_("Evaluation stage completed"),
		event_datetime=ts,
	)

	return {"name": doc.name, "status": doc.status}


def propose_disqualification(
	*,
	evaluation_session: str,
	evaluation_stage: str,
	bid_submission: str,
	supplier: str,
	disqualification_reason_type: str,
	reason_details: str,
	exception_record: str,
	disqualification_id: str | None = None,
) -> dict[str, Any]:
	"""Create or update a disqualification as Proposed (no decision fields)."""
	sess = _norm(evaluation_session)
	stg = _norm(evaluation_stage)
	bid = _norm(bid_submission)
	sup = _norm(supplier)
	rtype = _norm(disqualification_reason_type)
	rdet = _norm(reason_details)
	exc = _norm(exception_record)
	su = _norm(frappe.session.user)

	if not sess or not stg or not bid or not sup or not rtype or not rdet or not exc:
		frappe.throw(
			_("evaluation_session, evaluation_stage, bid_submission, supplier, disqualification_reason_type, reason_details, and exception_record are required."),
			frappe.ValidationError,
			title=_("Missing fields"),
		)

	validate_evaluator_access(sess, su, bid_submission=bid)

	ts = now_datetime()
	pe = _procuring_entity_for_session(sess)

	if _norm(disqualification_id):
		did = _norm(disqualification_id)
		if not frappe.db.exists(EDR, did):
			frappe.throw(_("Evaluation Disqualification Record not found."), frappe.ValidationError, title=_("Invalid record"))
		doc = frappe.get_doc(EDR, did)
		if _norm(doc.evaluation_session) != sess:
			frappe.throw(
				_("Disqualification does not match the evaluation session."),
				frappe.ValidationError,
				title=_("Session mismatch"),
			)
		doc.evaluation_stage = stg
		doc.bid_submission = bid
		doc.supplier = sup
		doc.disqualification_reason_type = rtype
		doc.reason_details = rdet
		doc.exception_record = exc
		doc.status = _EDR_PROPOSED
		doc.decided_by_user = None
		doc.decided_on = None
		doc.save(ignore_permissions=True)
		new_name = doc.name
	else:
		doc = frappe.get_doc(
			{
				"doctype": EDR,
				"evaluation_session": sess,
				"evaluation_stage": stg,
				"bid_submission": bid,
				"supplier": sup,
				"disqualification_reason_type": rtype,
				"reason_details": rdet,
				"exception_record": exc,
				"status": _EDR_PROPOSED,
			}
		)
		doc.insert(ignore_permissions=True)
		new_name = doc.name

	log_audit_event(
		event_type=EVT_DQ_PROPOSED,
		actor=su,
		source_module=SOURCE_MODULE,
		target_doctype=EDR,
		target_docname=new_name,
		procuring_entity=pe or None,
		old_state=_json_state(upsert=bool(_norm(disqualification_id))),
		new_state=_json_state(status=_EDR_PROPOSED),
		changed_fields_summary="status",
		reason=_("Disqualification proposed"),
		event_datetime=ts,
	)

	return {"name": new_name, "status": _EDR_PROPOSED}


def confirm_disqualification(
	disqualification_id: str,
	*,
	decided_by_user: str | None = None,
	decided_on=None,
) -> dict[str, Any]:
	"""Confirm a Proposed disqualification (sets decided_by / decided_on)."""
	did = _norm(disqualification_id)
	if not did:
		frappe.throw(_("Disqualification record is required."), frappe.ValidationError, title=_("Missing record"))
	if not frappe.db.exists(EDR, did):
		frappe.throw(_("Evaluation Disqualification Record not found."), frappe.ValidationError, title=_("Invalid record"))

	doc = frappe.get_doc(EDR, did)
	su = _norm(frappe.session.user)
	validate_evaluator_access(doc.evaluation_session, su, bid_submission=_norm(doc.bid_submission))

	if _norm(doc.status) != _EDR_PROPOSED:
		frappe.throw(
			_("Only a proposed disqualification can be confirmed."),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	dbu = _norm(decided_by_user) or su
	dt = decided_on if decided_on is not None else now_datetime()
	dt = get_datetime(dt)

	old_status = doc.status
	doc.status = _EDR_CONFIRMED
	doc.decided_by_user = dbu
	doc.decided_on = dt
	doc.save(ignore_permissions=True)

	ts = now_datetime()
	pe = _procuring_entity_for_session(doc.evaluation_session)
	log_audit_event(
		event_type=EVT_DQ_CONFIRMED,
		actor=su,
		source_module=SOURCE_MODULE,
		target_doctype=EDR,
		target_docname=doc.name,
		procuring_entity=pe or None,
		old_state=_json_state(status=old_status),
		new_state=_json_state(status=_EDR_CONFIRMED, decided_by_user=dbu, decided_on=str(dt)),
		changed_fields_summary="status,decided_by_user,decided_on",
		reason=_("Disqualification confirmed"),
		event_datetime=ts,
	)

	return {"name": doc.name, "status": doc.status}
