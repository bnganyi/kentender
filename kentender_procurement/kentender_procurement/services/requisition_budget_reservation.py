# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget reservation on final requisition approval (PROC-STORY-006).

Delegates all ledger movement to ``kentender_budget.services.budget_ledger_posting``.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender_budget.services.budget_availability import availability_headroom
from kentender_budget.services.budget_ledger_posting import reserve_budget

PR_DOCTYPE = "Purchase Requisition"
SOURCE_ACTION_FINAL_APPROVE = "final_approve"
SOURCE_MODULE = "kentender_procurement"

AUDIT_RESERVED = "kt.procurement.requisition.budget_reserved"
AUDIT_RESERVATION_SKIPPED = "kt.procurement.requisition.budget_reservation_skipped"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _idempotency_key(doc: Document) -> str:
	return f"{PR_DOCTYPE}|{doc.name}|reserve"


def apply_budget_reservation_on_final_approve(doc: Document) -> None:
	"""If ``budget_line`` is set, reserve ``requested_amount`` and snapshot fields on *doc*.

	If ``budget_line`` is empty, skip ledger calls and leave budget fields unchanged.

	Raises ``ValidationError`` when a line is set but ``requested_amount`` is not positive,
	or when ``reserve_budget`` rejects (e.g. insufficient availability).
	"""
	bl = _norm(doc.get("budget_line"))
	if not bl:
		log_audit_event(
			event_type=AUDIT_RESERVATION_SKIPPED,
			source_module=SOURCE_MODULE,
			target_doctype=PR_DOCTYPE,
			target_docname=doc.name,
			procuring_entity=_norm(doc.get("procuring_entity")) or None,
			reason=_("No budget line on requisition; reservation skipped."),
			new_state=json.dumps({"budget_line": ""}, sort_keys=True),
		)
		return

	amt = flt(doc.get("requested_amount"))
	if amt <= 0:
		frappe.throw(
			_("A positive requested amount is required to approve against a budget line."),
			frappe.ValidationError,
			title=_("Invalid amount"),
		)

	headroom = availability_headroom(bl)
	ble_name = reserve_budget(
		bl,
		amt,
		source_doctype=PR_DOCTYPE,
		source_docname=doc.name,
		source_action=SOURCE_ACTION_FINAL_APPROVE,
		source_business_id=_norm(doc.name) or None,
		related={"related_requisition": doc.name},
		idempotency_key=_idempotency_key(doc),
	)

	doc.set("available_budget_at_check", headroom)
	doc.set("budget_check_datetime", now_datetime())
	doc.set("reserved_amount", amt)
	doc.set("budget_reservation_status", "Reserved")
	doc.set("last_budget_action_ref", ble_name)

	log_audit_event(
		event_type=AUDIT_RESERVED,
		source_module=SOURCE_MODULE,
		target_doctype=PR_DOCTYPE,
		target_docname=doc.name,
		procuring_entity=_norm(doc.get("procuring_entity")) or None,
		reason=_("Budget reserved on final approval."),
		new_state=json.dumps(
			{
				"budget_line": bl,
				"amount": amt,
				"available_before": headroom,
				"budget_ledger_entry": ble_name,
			},
			sort_keys=True,
		),
	)
