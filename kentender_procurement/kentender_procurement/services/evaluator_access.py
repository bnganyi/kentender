# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Evaluator assignment and conflict-of-interest access checks (PROC-STORY-068).

Peer score visibility stays in scoring stories (e.g. PROC-STORY-069). When ``bid_submission`` is
passed to ``validate_evaluator_access``, only tender/session consistency is enforced (minimal rule).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

COI = "Conflict of Interest Declaration"
EA = "Evaluator Assignment"
ES = "Evaluation Session"
BS = "Bid Submission"

_STATUS_PENDING = "Pending"
_STATUS_NO_CONFLICT = "Declared No Conflict"
_STATUS_CONFLICT = "Declared Conflict"
_STATUS_REJECTED = "Rejected from Participation"
_STATUS_CLEARED = "Reviewed and Cleared"

_DECLARATION_STATUSES = frozenset(
	{
		_STATUS_PENDING,
		_STATUS_NO_CONFLICT,
		_STATUS_CONFLICT,
		_STATUS_REJECTED,
		_STATUS_CLEARED,
	}
)

_ALLOWED_ACCESS_STATUSES = frozenset({_STATUS_NO_CONFLICT, _STATUS_CLEARED})

_ACTIVE = "Active"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _latest_coi(evaluation_session_id: str, evaluator_user: str) -> str | None:
	sn = _norm(evaluation_session_id)
	un = _norm(evaluator_user)
	if not sn or not un:
		return None
	rows = (
		frappe.get_all(
			COI,
			filters={"evaluation_session": sn, "evaluator_user": un},
			pluck="name",
			order_by="modified desc",
			limit=1,
		)
		or []
	)
	return rows[0] if rows else None


def _active_assignment_name(evaluation_session_id: str, evaluator_user: str) -> str | None:
	sn = _norm(evaluation_session_id)
	un = _norm(evaluator_user)
	if not sn or not un:
		return None
	rows = (
		frappe.get_all(
			EA,
			filters={
				"evaluation_session": sn,
				"evaluator_user": un,
				"assignment_status": _ACTIVE,
			},
			pluck="name",
			limit=2,
		)
		or []
	)
	if not rows:
		return None
	return rows[0]


def submit_conflict_declaration(
	evaluation_session_id: str,
	evaluator_user: str,
	*,
	declaration_status: str,
	declaration_datetime=None,
	conflict_summary: str | None = None,
	related_bid_submission: str | None = None,
	related_supplier: str | None = None,
) -> dict[str, Any]:
	"""Insert or update the Conflict of Interest Declaration for (session, evaluator)."""
	sn = _norm(evaluation_session_id)
	un = _norm(evaluator_user)
	st = _norm(declaration_status)
	if not sn:
		frappe.throw(_("Evaluation session is required."), frappe.ValidationError, title=_("Missing session"))
	if not un:
		frappe.throw(_("Evaluator user is required."), frappe.ValidationError, title=_("Missing user"))
	if not st:
		frappe.throw(_("Declaration status is required."), frappe.ValidationError, title=_("Missing status"))
	if st not in _DECLARATION_STATUSES:
		frappe.throw(_("Invalid declaration status."), frappe.ValidationError, title=_("Invalid status"))
	if not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	dt = declaration_datetime if declaration_datetime is not None else now_datetime()
	if dt is not None:
		dt = get_datetime(dt)

	existing = _latest_coi(sn, un)
	fields = {
		"evaluation_session": sn,
		"evaluator_user": un,
		"declaration_status": st,
		"declaration_datetime": dt,
		"conflict_summary": conflict_summary,
		"related_bid_submission": related_bid_submission,
		"related_supplier": related_supplier,
	}
	if existing:
		doc = frappe.get_doc(COI, existing)
		for k, v in fields.items():
			if k in ("evaluation_session", "evaluator_user"):
				continue
			setattr(doc, k, v)
		doc.save(ignore_permissions=True)
		name = doc.name
	else:
		fields["doctype"] = COI
		doc = frappe.get_doc(fields)
		doc.insert(ignore_permissions=True)
		name = doc.name

	return {"name": name, "declaration_status": st}


def validate_evaluator_access(
	evaluation_session: str,
	user: str,
	bid_submission: str | None = None,
) -> dict[str, Any]:
	"""Require an active assignment and a clearance-level COI before evaluation access.

	:param bid_submission: If set, must belong to the same tender as the evaluation session.
	:returns: Dict with evaluator_assignment, conflict_declaration names.
	:raises frappe.ValidationError: If assignment or declaration rules fail.
	"""
	sn = _norm(evaluation_session)
	un = _norm(user)
	if not sn:
		frappe.throw(_("Evaluation session is required."), frappe.ValidationError, title=_("Missing session"))
	if not un:
		frappe.throw(_("User is required."), frappe.ValidationError, title=_("Missing user"))
	if not frappe.db.exists(ES, sn):
		frappe.throw(_("Evaluation Session not found."), frappe.ValidationError, title=_("Invalid session"))

	ea_name = _active_assignment_name(sn, un)
	if not ea_name:
		frappe.throw(
			_("Evaluator is not actively assigned to this evaluation session."),
			frappe.ValidationError,
			title=_("Not assigned"),
		)

	coi_name = _latest_coi(sn, un)
	if not coi_name:
		frappe.throw(
			_("Conflict of Interest declaration is required."),
			frappe.ValidationError,
			title=_("Declaration required"),
		)

	status = _norm(frappe.db.get_value(COI, coi_name, "declaration_status"))
	if status not in _ALLOWED_ACCESS_STATUSES:
		frappe.throw(
			_("Conflict declaration does not allow evaluation access."),
			frappe.ValidationError,
			title=_("Access denied"),
		)

	bn = _norm(bid_submission)
	if bn:
		if not frappe.db.exists(BS, bn):
			frappe.throw(_("Bid Submission not found."), frappe.ValidationError, title=_("Invalid bid"))
		tn = frappe.db.get_value(ES, sn, "tender")
		bt = frappe.db.get_value(BS, bn, "tender")
		if tn and bt and _norm(bt) != _norm(tn):
			frappe.throw(
				_("Bid Submission must belong to the same tender as the evaluation session."),
				frappe.ValidationError,
				title=_("Bid tender mismatch"),
			)

	return {
		"ok": True,
		"evaluator_assignment": ea_name,
		"conflict_declaration": coi_name,
	}
