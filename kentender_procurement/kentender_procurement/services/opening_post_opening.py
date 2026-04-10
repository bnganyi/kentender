# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Post-opening lock and finalization (PROC-STORY-055)."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

BOR = "Bid Opening Register"
BOS = "Bid Opening Session"
BOEL = "Bid Opening Event Log"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _event_hash(payload: str) -> str:
	return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def lock_opening_register_and_finalize(
	register_name: str,
	session_name: str,
	*,
	actor_user: str | None = None,
) -> dict[str, Any]:
	"""Lock the opening register, mark session register locked, emit audit event."""
	rn = _norm(register_name)
	sn = _norm(session_name)
	if not rn or not frappe.db.exists(BOR, rn):
		frappe.throw(_("Bid Opening Register not found."), frappe.ValidationError)
	if not sn or not frappe.db.exists(BOS, sn):
		frappe.throw(_("Bid Opening Session not found."), frappe.ValidationError)

	actor = _norm(actor_user) or frappe.session.user
	now = now_datetime()

	row = frappe.db.get_value(BOR, rn, ["register_hash", "tender", "bid_opening_session"], as_dict=True)
	base = (row.get("register_hash") if row else None) or rn
	reg_hash = _event_hash(f"lock|{rn}|{base}|{now}")

	frappe.db.set_value(
		BOR,
		rn,
		{
			"is_locked": 1,
			"status": "Locked",
			"register_hash": reg_hash,
		},
		update_modified=False,
	)

	frappe.db.set_value(
		BOS,
		sn,
		{
			"register_locked": 1,
		},
		update_modified=False,
	)

	frappe.get_doc(
		{
			"doctype": BOEL,
			"bid_opening_session": sn,
			"event_type": "Register Locked",
			"event_datetime": now,
			"actor_user": actor,
			"event_summary": _("Opening register {0} locked.").format(rn),
			"result_status": "Success",
			"event_hash": _event_hash(f"lock|{rn}|{sn}"),
		}
	).insert(ignore_permissions=True)

	return {"register": rn, "session": sn, "register_hash": reg_hash}
