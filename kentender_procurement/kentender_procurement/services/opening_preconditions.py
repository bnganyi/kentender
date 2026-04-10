# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Opening precondition checks (PROC-STORY-052)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

TENDER = "Tender"
SESSION = "Bid Opening Session"

WS_PUBLISHED = "Published"
T_CANCELLED = "Cancelled"
S_COMPLETED = "Completed"
S_CANCELLED = "Cancelled"


def validate_opening_preconditions(tender_id: str, opening_session_id: str) -> dict[str, Any]:
	"""Return structured pass/fail for opening ceremony readiness (does not mutate data).

	``checks`` entries are explainable audit-friendly rows: ``code``, ``ok``, ``detail``.
	"""
	tid = (tender_id or "").strip()
	sid = (opening_session_id or "").strip()
	checks: list[dict[str, Any]] = []

	def add(code: str, ok: bool, detail: str) -> None:
		checks.append({"code": code, "ok": ok, "detail": detail})

	if not tid:
		add("tender_id", False, _("Tender is required."))
		return {"ok": False, "checks": checks}
	if not frappe.db.exists(TENDER, tid):
		add("tender_exists", False, _("Tender not found."))
		return {"ok": False, "checks": checks}

	trow = frappe.db.get_value(
		TENDER,
		tid,
		["workflow_state", "status", "submission_deadline", "submission_status"],
		as_dict=True,
	) or {}
	ws = (trow.get("workflow_state") or "").strip()
	st = (trow.get("status") or "").strip()
	ok_pub = ws == WS_PUBLISHED
	add("tender_published", ok_pub, _("Tender must be Published.") if not ok_pub else _("OK"))
	ok_nc = st != T_CANCELLED and ws != "Cancelled"
	add("tender_not_cancelled", ok_nc, _("Tender must not be cancelled.") if not ok_nc else _("OK"))

	deadline = trow.get("submission_deadline")
	now = now_datetime()
	ok_deadline = False
	detail_deadline = _("No submission deadline set on tender.")
	if deadline:
		ok_deadline = get_datetime(now) >= get_datetime(deadline)
		detail_deadline = (
			_("Submission deadline has not passed yet.")
			if not ok_deadline
			else _("Submission deadline has passed.")
		)
	add("submission_deadline_passed", ok_deadline, detail_deadline)

	if not sid:
		add("session_id", False, _("Opening session is required."))
		return {"ok": False, "checks": checks}
	if not frappe.db.exists(SESSION, sid):
		add("session_exists", False, _("Bid Opening Session not found."))
		return {"ok": False, "checks": checks}

	srow = frappe.db.get_value(
		SESSION,
		sid,
		[
			"tender",
			"workflow_state",
			"status",
			"is_atomic_opening_complete",
		],
		as_dict=True,
	) or {}
	st_tender = (srow.get("tender") or "").strip()
	ok_match = st_tender == tid
	add("session_tender_match", ok_match, _("Session tender mismatch.") if not ok_match else _("OK"))

	sws = (srow.get("workflow_state") or "").strip()
	ok_sess = sws not in (S_COMPLETED, S_CANCELLED)
	add(
		"session_not_terminal",
		ok_sess,
		_("Session is already completed or cancelled.") if not ok_sess else _("OK"),
	)

	if srow.get("is_atomic_opening_complete"):
		add("session_not_already_executed", False, _("Atomic opening already marked complete for this session."))
	else:
		add("session_not_already_executed", True, _("OK"))

	ok = all(c.get("ok") for c in checks)
	return {"ok": ok, "checks": checks}
