# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Create Evaluation Session and default Evaluation Stages from a completed opening (PROC-STORY-067).

Assumptions (first-pass scaffold):
- ``evaluation_mode`` selects a **default ordered stage list** (types must match Evaluation Stage options).
- **No Evaluator Assignment** rows are created; callers or later stories assign committee members.
- ``actor_user`` is reserved for future audit hooks; unused in this module.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

BOS = "Bid Opening Session"
BOR = "Bid Opening Register"
BOR_LINE = "Bid Opening Register Line"
ES = "Evaluation Session"
EST = "Evaluation Stage"
TENDER = "Tender"

_MODE_TWO_ENVELOPE = "Two Envelope"
_MODE_COMBINED = "Combined Quality and Price"
_MODE_LEB = "Lowest Evaluated Bid"
_MODE_QUALITY = "Quality Based"
_MODE_OTHER = "Other"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _default_stage_rows(evaluation_mode: str) -> list[dict[str, Any]]:
	"""Return kwargs fragments for Evaluation Stage inserts (``evaluation_session`` added by caller)."""
	m = _norm(evaluation_mode) or _MODE_TWO_ENVELOPE

	def row(
		order: int,
		stage_type: str,
		*,
		scoring: bool = False,
		disqualifying: bool = False,
		pass_mark: float | None = None,
	) -> dict[str, Any]:
		d: dict[str, Any] = {
			"doctype": EST,
			"stage_order": order,
			"stage_type": stage_type,
			"status": "Draft",
			"is_scoring_stage": 1 if scoring else 0,
			"is_disqualifying_stage": 1 if disqualifying else 0,
		}
		if pass_mark is not None:
			d["minimum_pass_mark"] = pass_mark
		return d

	if m == _MODE_TWO_ENVELOPE:
		return [
			row(1, "Preliminary Examination"),
			row(2, "Technical Evaluation", scoring=True, disqualifying=True, pass_mark=0.0),
			row(3, "Financial Evaluation", scoring=True, pass_mark=0.0),
		]
	if m == _MODE_COMBINED:
		return [
			row(1, "Preliminary Examination"),
			row(2, "Combined Ranking", scoring=True, pass_mark=0.0),
		]
	if m == _MODE_LEB:
		return [
			row(1, "Preliminary Examination"),
			row(2, "Technical Evaluation", scoring=True, disqualifying=True, pass_mark=0.0),
			row(3, "Financial Evaluation", scoring=True, pass_mark=0.0),
			row(4, "Combined Ranking", scoring=True, pass_mark=0.0),
		]
	if m == _MODE_QUALITY:
		return [
			row(1, "Preliminary Examination"),
			row(2, "Technical Evaluation", scoring=True, disqualifying=True, pass_mark=0.0),
		]
	return [row(1, "Preliminary Examination")]


def _opened_bid_count(register_name: str) -> int:
	rn = _norm(register_name)
	if not rn:
		return 0
	tob = frappe.db.get_value(BOR, rn, "total_opened_bids")
	if tob is not None:
		try:
			n = int(tob)
			if n >= 0:
				return n
		except (TypeError, ValueError):
			pass
	return frappe.db.count(
		BOR_LINE,
		{"parent": rn, "parenttype": BOR, "parentfield": "register_lines", "was_opened": 1},
	)


def _validate_opening_triangle(bos_name: str, bor_name: str, tender_id: str) -> None:
	bn = _norm(bos_name)
	rn = _norm(bor_name)
	tn = _norm(tender_id)
	if not bn or not frappe.db.exists(BOS, bn):
		frappe.throw(_("Bid Opening Session not found."), frappe.ValidationError, title=_("Invalid opening"))
	if not rn or not frappe.db.exists(BOR, rn):
		frappe.throw(_("Bid Opening Register not found."), frappe.ValidationError, title=_("Invalid opening"))
	bos = frappe.db.get_value(
		BOS,
		bn,
		["tender", "opening_register", "register_locked", "is_atomic_opening_complete", "workflow_state", "status"],
		as_dict=True,
	) or {}
	if _norm(bos.get("opening_register")) != rn:
		frappe.throw(
			_("Opening register on the session does not match the selected register."),
			frappe.ValidationError,
			title=_("Opening mismatch"),
		)
	if _norm(bos.get("tender")) != tn:
		frappe.throw(_("Opening session tender mismatch."), frappe.ValidationError, title=_("Opening mismatch"))
	if not int(bos.get("register_locked") or 0):
		frappe.throw(
			_("Opening session is not register-locked; complete bid opening first."),
			frappe.ValidationError,
			title=_("Opening not finalized"),
		)
	if not int(bos.get("is_atomic_opening_complete") or 0):
		frappe.throw(
			_("Atomic bid opening is not complete for this session."),
			frappe.ValidationError,
			title=_("Opening not complete"),
		)
	ws = _norm(bos.get("workflow_state"))
	st = _norm(bos.get("status"))
	if ws and ws != "Completed":
		frappe.throw(
			_("Bid Opening Session must be Completed before starting evaluation."),
			frappe.ValidationError,
			title=_("Opening not complete"),
		)
	if st and st != "Completed":
		frappe.throw(
			_("Bid Opening Session must be Completed before starting evaluation."),
			frappe.ValidationError,
			title=_("Opening not complete"),
		)

	bor = frappe.db.get_value(
		BOR,
		rn,
		["tender", "bid_opening_session", "is_locked", "status"],
		as_dict=True,
	) or {}
	if _norm(bor.get("tender")) != tn:
		frappe.throw(
			_("Opening register must belong to the same tender as the session."),
			frappe.ValidationError,
			title=_("Register tender mismatch"),
		)
	if _norm(bor.get("bid_opening_session")) != bn:
		frappe.throw(
			_("Opening register must be linked to this Bid Opening Session."),
			frappe.ValidationError,
			title=_("Register session mismatch"),
		)
	if not int(bor.get("is_locked") or 0):
		frappe.throw(
			_("Bid Opening Register must be locked before starting evaluation."),
			frappe.ValidationError,
			title=_("Register not locked"),
		)
	if _norm(bor.get("status")) != "Locked":
		frappe.throw(
			_("Bid Opening Register must be locked before starting evaluation."),
			frappe.ValidationError,
			title=_("Register not locked"),
		)


def _resolve_opening_session_id(tender_id: str | None, opening_session_id: str | None) -> tuple[str, str]:
	tid = _norm(tender_id)
	sid = _norm(opening_session_id)
	if tid and sid:
		frappe.throw(
			_("Pass either tender_id or opening_session_id, not both."),
			frappe.ValidationError,
			title=_("Invalid arguments"),
		)
	if not tid and not sid:
		frappe.throw(
			_("tender_id or opening_session_id is required."),
			frappe.ValidationError,
			title=_("Invalid arguments"),
		)
	if sid:
		tender_from_bos = frappe.db.get_value(BOS, sid, "tender")
		if not _norm(tender_from_bos):
			frappe.throw(_("Opening session has no tender."), frappe.ValidationError, title=_("Invalid opening"))
		return sid, _norm(tender_from_bos)

	candidates = frappe.get_all(
		BOS,
		filters={
			"tender": tid,
			"is_atomic_opening_complete": 1,
			"register_locked": 1,
		},
		pluck="name",
		order_by="modified desc",
	)
	valid: list[str] = []
	for cand in candidates or []:
		rn = frappe.db.get_value(BOS, cand, "opening_register")
		if not _norm(rn):
			continue
		try:
			_validate_opening_triangle(cand, _norm(rn), tid)
		except frappe.ValidationError:
			continue
		valid.append(cand)
	if not valid:
		frappe.throw(
			_("No completed, locked opening session found for this tender."),
			frappe.ValidationError,
			title=_("Opening not ready"),
		)
	if len(valid) > 1:
		frappe.throw(
			_("Multiple completed opening sessions exist; pass opening_session_id explicitly."),
			frappe.ValidationError,
			title=_("Ambiguous opening session"),
		)
	return valid[0], tid


def initialize_evaluation_session(
	tender_id: str | None = None,
	opening_session_id: str | None = None,
	*,
	business_id: str | None = None,
	evaluation_mode: str | None = None,
	actor_user: str | None = None,
) -> dict[str, Any]:
	"""Create an Evaluation Session and default Evaluation Stages after a completed atomic opening.

	:param actor_user: Reserved for future audit integration (unused).
	"""
	bos_name, tender_id_resolved = _resolve_opening_session_id(tender_id, opening_session_id)
	register_name = _norm(frappe.db.get_value(BOS, bos_name, "opening_register"))
	if not register_name:
		frappe.throw(_("Opening session has no register."), frappe.ValidationError, title=_("Invalid opening"))

	_validate_opening_triangle(bos_name, register_name, tender_id_resolved)

	existing = frappe.get_all(ES, filters={"opening_session": bos_name}, pluck="name", limit=1)
	if existing:
		frappe.throw(
			_("An evaluation session already exists for this opening session."),
			frappe.ValidationError,
			title=_("Already initialized"),
		)

	mode = _norm(evaluation_mode) or _MODE_TWO_ENVELOPE
	allowed_modes = {
		_MODE_TWO_ENVELOPE,
		_MODE_COMBINED,
		_MODE_LEB,
		_MODE_QUALITY,
		_MODE_OTHER,
	}
	if mode not in allowed_modes:
		frappe.throw(
			_("Unsupported evaluation_mode: {0}").format(mode),
			frappe.ValidationError,
			title=_("Invalid evaluation mode"),
		)

	t_row = frappe.db.get_value(
		TENDER,
		tender_id_resolved,
		["procuring_entity", "procurement_method", "currency"],
		as_dict=True,
	) or {}
	entity = _norm(t_row.get("procuring_entity"))
	if not entity:
		frappe.throw(_("Tender has no procuring entity."), frappe.ValidationError, title=_("Invalid tender"))

	if _norm(business_id):
		biz = _norm(business_id)
	else:
		biz = f"EVI-{frappe.generate_hash(length=12)}"
		for _i in range(8):
			if not frappe.db.exists(ES, {"business_id": biz}):
				break
			biz = f"EVI-{frappe.generate_hash(length=12)}"
		else:
			frappe.throw(_("Could not allocate a unique evaluation session business_id."), frappe.ValidationError)

	candidate_count = _opened_bid_count(register_name)

	es_doc = frappe.get_doc(
		{
			"doctype": ES,
			"business_id": biz,
			"tender": tender_id_resolved,
			"procuring_entity": entity,
			"opening_session": bos_name,
			"opening_register": register_name,
			"status": "Draft",
			"workflow_state": "Draft",
			"evaluation_mode": mode,
			"conflict_clearance_status": "Pending",
			"candidate_bid_count": candidate_count,
			"disqualified_bid_count": 0,
			"responsive_bid_count": 0,
			"procurement_method": t_row.get("procurement_method"),
			"currency": t_row.get("currency"),
		}
	)
	es_doc.insert(ignore_permissions=True)

	stage_names: list[str] = []
	for spec in _default_stage_rows(mode):
		spec = dict(spec)
		spec["evaluation_session"] = es_doc.name
		st = frappe.get_doc(spec)
		st.insert(ignore_permissions=True)
		stage_names.append(st.name)

	return {
		"evaluation_session": es_doc.name,
		"stages": stage_names,
		"candidate_bid_count": candidate_count,
		"tender": tender_id_resolved,
		"opening_session": bos_name,
		"opening_register": register_name,
	}
