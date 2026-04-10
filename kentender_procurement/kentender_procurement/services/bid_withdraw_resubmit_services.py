# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid withdrawal and resubmission (PROC-STORY-045).

Withdrawal and resubmission are explicit services — not direct **Bid Submission** edits.
Prior bids stay immutable; new drafts reference :field:`prior_bid_submission`.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from kentender.services.audit_event_service import log_audit_event

from kentender_procurement.services.bid_draft_validate_services import create_bid_draft
from kentender_procurement.services.bid_supplier_eligibility import assess_supplier_bid_eligibility
from kentender_procurement.services.tender_workflow_actions import SUB_OPEN, WS_PUBLISHED

BS = "Bid Submission"
BWR = "Bid Withdrawal Record"
BSE = "Bid Submission Event"

AUDIT_BID_WITHDRAWN = "kt.procurement.bid.withdrawn"
SOURCE_MODULE = "kentender_procurement"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _norm_dt(value) -> str:
	if value is None:
		return ""
	d = get_datetime(value)
	return d.isoformat() if d else str(value)


def _event_hash(
	*,
	bid_name: str,
	event_type: str,
	summary: str,
	actor: str,
	event_datetime,
) -> str:
	payload = {
		"actor_user": actor,
		"bid_submission": bid_name,
		"event_datetime": _norm_dt(event_datetime),
		"event_summary": summary,
		"event_type": event_type,
	}
	canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _insert_bid_event(bid_name: str, event_type: str, summary: str, *, user: str) -> None:
	ts = now_datetime()
	eh = _event_hash(
		bid_name=bid_name,
		event_type=event_type,
		summary=summary,
		actor=user,
		event_datetime=ts,
	)
	frappe.get_doc(
		{
			"doctype": BSE,
			"bid_submission": bid_name,
			"event_type": event_type,
			"event_datetime": ts,
			"event_summary": summary,
			"actor_user": user,
			"event_hash": eh,
		}
	).insert(ignore_permissions=True)


def _assert_withdrawal_window(bid, tender_row: dict) -> None:
	"""Enforce tender rules and deadlines for withdrawal."""
	if not cint(tender_row.get("allows_withdrawal_before_deadline")):
		frappe.throw(
			_("This tender does not allow bid withdrawal."),
			frappe.ValidationError,
			title=_("Withdrawal not allowed"),
		)
	deadline = get_datetime(bid.submission_deadline or tender_row.get("submission_deadline"))
	if deadline and now_datetime() > deadline:
		frappe.throw(
			_("Withdrawal is only allowed before the submission deadline."),
			frappe.ValidationError,
			title=_("Too late to withdraw"),
		)
	opening = get_datetime(tender_row.get("opening_datetime"))
	if opening and now_datetime() >= opening:
		frappe.throw(
			_("Withdrawal is not allowed after the bid opening time."),
			frappe.ValidationError,
			title=_("Too late to withdraw"),
		)


def withdraw_bid(
	bid_submission_id: str,
	*,
	reason: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""Record withdrawal on a **submitted** bid (pre-opening), append **Bid Withdrawal Record**, audit, event."""
	bn = _strip(bid_submission_id)
	u = _strip(user) or _strip(getattr(frappe.session, "user", None)) or "Administrator"
	rs = _strip(reason)
	if not rs:
		frappe.throw(_("Reason is required."), frappe.ValidationError, title=_("Missing reason"))

	bid = frappe.get_doc(BS, bn)
	if _strip(bid.workflow_state) != "Submitted" or _strip(bid.status) != "Submitted":
		frappe.throw(_("Only submitted bids can be withdrawn."), frappe.ValidationError, title=_("Invalid state"))
	if not cint(bid.is_final_submission):
		frappe.throw(_("Only final submitted bids can use this withdrawal service."), frappe.ValidationError)

	tn = _strip(bid.tender)
	t_row = frappe.db.get_value(
		"Tender",
		tn,
		[
			"workflow_state",
			"submission_status",
			"submission_deadline",
			"opening_datetime",
			"allows_withdrawal_before_deadline",
			"procuring_entity",
		],
		as_dict=True,
	)
	if not t_row:
		frappe.throw(_("Tender not found."), frappe.ValidationError)
	if _strip(t_row.get("workflow_state")) != WS_PUBLISHED:
		frappe.throw(_("Tender is not published."), frappe.ValidationError)
	if _strip(t_row.get("submission_status")) != SUB_OPEN:
		frappe.throw(_("Tender submission is not open."), frappe.ValidationError)

	_assert_withdrawal_window(bid, t_row)

	elig = assess_supplier_bid_eligibility(tn, bid.supplier)
	if not elig.get("eligible"):
		msg = "; ".join(elig.get("reasons") or []) or _("Not eligible.")
		frappe.throw(msg, frappe.ValidationError, title=_("Not eligible"))

	ts = now_datetime()

	frappe.get_doc(
		{
			"doctype": BWR,
			"bid_submission": bn,
			"withdrawal_datetime": ts,
			"status": "Withdrawn",
			"withdrawn_by_user": u,
			"reason": rs,
		}
	).insert(ignore_permissions=True)

	frappe.flags.in_bid_withdraw_service = True
	try:
		b2 = frappe.get_doc(BS, bn)
		b2.set("status", "Withdrawn")
		b2.set("workflow_state", "Withdrawn")
		b2.set("withdrawn_by_user", u)
		b2.set("withdrawn_on", ts)
		b2.set("active_submission_flag", 0)
		b2.save(ignore_permissions=True)
	finally:
		frappe.flags.in_bid_withdraw_service = False

	pe = _strip(t_row.get("procuring_entity"))
	log_audit_event(
		event_type=AUDIT_BID_WITHDRAWN,
		actor=u,
		source_module=SOURCE_MODULE,
		target_doctype=BS,
		target_docname=bn,
		procuring_entity=pe or None,
		old_state="Submitted",
		new_state="Withdrawn",
		changed_fields_summary=f"withdrawal_record; reason_len={len(rs)}",
		reason=rs[: 240],
		event_datetime=ts,
	)

	_insert_bid_event(bn, "Withdrawn", _("Bid withdrawn: {0}").format(rs[:120]), user=u)

	return {"bid_submission": bn, "withdrawn_on": ts}


def create_resubmission_from_withdrawn_bid(
	withdrawn_bid_submission_id: str,
	*,
	supplier_id: str | None = None,
	user: str | None = None,
) -> Any:
	"""Create a new **Draft** bid after withdrawal; prior row stays unchanged and linked via prior_bid_submission."""
	pn = _strip(withdrawn_bid_submission_id)
	_ = _strip(user) or _strip(getattr(frappe.session, "user", None)) or "Administrator"

	prev = frappe.get_doc(BS, pn)
	if _strip(prev.workflow_state) != "Withdrawn" or _strip(prev.status) != "Withdrawn":
		frappe.throw(_("Source bid must be withdrawn."), frappe.ValidationError, title=_("Invalid prior bid"))

	sup = _strip(supplier_id) if supplier_id else _strip(prev.supplier)
	if sup != _strip(prev.supplier):
		frappe.throw(_("Supplier must match the withdrawn bid."), frappe.ValidationError)

	tn = _strip(prev.tender)
	t_row = frappe.db.get_value(
		"Tender",
		tn,
		["allows_resubmission_before_deadline", "submission_status", "workflow_state", "submission_deadline"],
		as_dict=True,
	)
	if not t_row:
		frappe.throw(_("Tender not found."), frappe.ValidationError)
	dl = get_datetime(t_row.get("submission_deadline"))
	if dl and now_datetime() > dl:
		frappe.throw(
			_("Resubmission is only allowed before the submission deadline."),
			frappe.ValidationError,
			title=_("Deadline passed"),
		)
	if not cint(t_row.get("allows_resubmission_before_deadline")):
		frappe.throw(
			_("This tender does not allow resubmission."),
			frappe.ValidationError,
			title=_("Resubmission not allowed"),
		)
	if _strip(t_row.get("workflow_state")) != WS_PUBLISHED:
		frappe.throw(_("Tender is not published."), frappe.ValidationError)
	if _strip(t_row.get("submission_status")) != SUB_OPEN:
		frappe.throw(_("Tender submission is not open."), frappe.ValidationError)

	return create_bid_draft(
		tn,
		sup,
		prior_bid_submission=pn,
		submission_version_no=cint(prev.submission_version_no) + 1,
	)
