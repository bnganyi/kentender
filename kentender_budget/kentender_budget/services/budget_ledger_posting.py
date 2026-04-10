# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget ledger posting (BUD-008). All control movements go through these functions.

Creates append-only **Budget Ledger Entry** rows and syncs denormalized **Budget Line** amounts.
Authoritative balances are ledger sums; line fields are convenience copies.

See :mod:`kentender_budget.services.budget_availability` for read-side aggregation (BUD-009).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from kentender_budget.services.budget_audit import log_budget_audit
from kentender_budget.services.budget_availability import (
	ENTRY_COMMIT_FROM_AVAILABLE,
	ENTRY_COMMIT_FROM_RESERVED,
	ENTRY_RELEASE_COMMITMENT,
	ENTRY_RELEASE_RESERVATION,
	ENTRY_RESERVE,
	aggregate_ledger_buckets,
	availability_headroom,
)
from kentender_budget.services.budget_line_derived_totals import on_budget_ledger_post_recalculate_line

BLE = "Budget Ledger Entry"
BL = "Budget Line"

DIR_IN = "In"


def _require_budget_line(budget_line_id: str):
	if not budget_line_id or not frappe.db.exists(BL, budget_line_id):
		frappe.throw(_("Budget Line {0} not found.").format(budget_line_id), frappe.DoesNotExistError)
	line = frappe.get_doc(BL, budget_line_id)
	if (line.status or "").strip() == "Cancelled":
		frappe.throw(_("Budget Line is cancelled."), frappe.ValidationError, title=_("Invalid line"))
	return line


def _new_ledger_entry_name(prefix: str = "KT-BLE") -> str:
	return f"{prefix}-{frappe.generate_hash(length=14)}"


def _insert_ledger_row(
	line,
	*,
	entry_type: str,
	amount: float,
	source_doctype: str,
	source_docname: str,
	source_action: str,
	source_business_id: str | None = None,
	posting_datetime: datetime | str | None = None,
	related: dict[str, str | None] | None = None,
	reversal_of_entry: str | None = None,
	idempotency_key: str | None = None,
) -> frappe.model.document.Document:
	"""Insert one posted entry. *line* is Budget Line document."""
	related = related or {}
	row = {
		"doctype": BLE,
		"name": _new_ledger_entry_name(),
		"budget_line": line.name,
		"budget": line.budget,
		"procuring_entity": line.procuring_entity,
		"fiscal_year": line.fiscal_year,
		"currency": line.currency,
		"entry_type": entry_type,
		"entry_direction": DIR_IN,
		"amount": flt(amount),
		"posting_datetime": posting_datetime or now_datetime(),
		"status": "Posted",
		"source_doctype": source_doctype,
		"source_docname": source_docname,
		"source_action": source_action,
		"source_business_id": source_business_id,
		"related_requisition": related.get("related_requisition"),
		"related_procurement_plan_item": related.get("related_procurement_plan_item"),
		"related_tender": related.get("related_tender"),
		"related_award_decision": related.get("related_award_decision"),
		"related_contract": related.get("related_contract"),
		"reversal_of_entry": reversal_of_entry,
	}
	ik = (idempotency_key or "").strip()
	if ik:
		row["idempotency_key"] = ik
	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return doc


def _sync_budget_line_denorm(budget_line_id: str) -> None:
	r, c, rel = aggregate_ledger_buckets(budget_line_id)
	frappe.db.set_value(
		BL,
		budget_line_id,
		{
			"reserved_amount": r,
			"committed_amount": c,
			"released_amount": rel,
		},
		update_modified=False,
	)
	on_budget_ledger_post_recalculate_line(budget_line_id)


def _log_ledger_audit(
	*,
	event_type: str,
	budget_line_name: str,
	procuring_entity: str | None,
	payload: dict[str, Any],
) -> None:
	log_budget_audit(
		event_type=event_type,
		procuring_entity=procuring_entity,
		target_doctype=BL,
		target_docname=budget_line_name,
		payload=payload,
	)


def _lock_budget_line_row(budget_line_id: str) -> None:
	"""Row-level lock for concurrency-safe posting (BUD-010); runs in request transaction."""
	frappe.db.sql(f"select name from `tab{BL}` where name = %s for update", (budget_line_id,))


def lock_budget_line_for_update(budget_line_id: str) -> None:
	"""Public alias for row-level lock (BUD-013 revision apply)."""
	_lock_budget_line_row(budget_line_id)


def reserve_budget(
	budget_line_id: str,
	amount: float,
	*,
	source_doctype: str,
	source_docname: str,
	source_action: str,
	source_business_id: str | None = None,
	related: dict[str, str | None] | None = None,
	idempotency_key: str | None = None,
	posting_datetime: datetime | str | None = None,
) -> str:
	"""Post a reservation. Raises if insufficient uncommitted balance."""
	_lock_budget_line_row(budget_line_id)
	if idempotency_key:
		existing = frappe.db.get_value(
			BLE,
			{"idempotency_key": idempotency_key, "budget_line": budget_line_id},
			"name",
		)
		if existing:
			return existing
	line = _require_budget_line(budget_line_id)
	amt = flt(amount)
	if amt <= 0:
		frappe.throw(_("Amount must be positive."), frappe.ValidationError)
	if availability_headroom(budget_line_id, as_of_datetime=posting_datetime) < amt:
		frappe.throw(
			_("Insufficient budget availability to reserve {0}.").format(amt),
			frappe.ValidationError,
			title=_("Insufficient funds"),
		)
	doc = _insert_ledger_row(
		line,
		entry_type=ENTRY_RESERVE,
		amount=amt,
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_action=source_action,
		source_business_id=source_business_id,
		posting_datetime=posting_datetime,
		related=related,
		idempotency_key=idempotency_key,
	)
	_sync_budget_line_denorm(budget_line_id)
	_log_ledger_audit(
		event_type="kt.budget.ledger.reserve",
		budget_line_name=line.name,
		procuring_entity=line.procuring_entity,
		payload={"amount": amt, "entry": doc.name},
	)
	return doc.name


def release_reservation(
	budget_line_id: str,
	amount: float,
	*,
	source_doctype: str,
	source_docname: str,
	source_action: str,
	source_business_id: str | None = None,
	related: dict[str, str | None] | None = None,
	idempotency_key: str | None = None,
	posting_datetime: datetime | str | None = None,
) -> str:
	_lock_budget_line_row(budget_line_id)
	if idempotency_key:
		existing = frappe.db.get_value(
			BLE,
			{"idempotency_key": idempotency_key, "budget_line": budget_line_id},
			"name",
		)
		if existing:
			return existing
	line = _require_budget_line(budget_line_id)
	amt = flt(amount)
	if amt <= 0:
		frappe.throw(_("Amount must be positive."), frappe.ValidationError)
	r, _, _ = aggregate_ledger_buckets(budget_line_id, as_of_datetime=posting_datetime)
	if r < amt - 1e-9:
		frappe.throw(
			_("Reserved balance {0} is less than release amount {1}.").format(r, amt),
			frappe.ValidationError,
			title=_("Insufficient reservation"),
		)
	doc = _insert_ledger_row(
		line,
		entry_type=ENTRY_RELEASE_RESERVATION,
		amount=amt,
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_action=source_action,
		source_business_id=source_business_id,
		posting_datetime=posting_datetime,
		related=related,
		idempotency_key=idempotency_key,
	)
	_sync_budget_line_denorm(budget_line_id)
	_log_ledger_audit(
		event_type="kt.budget.ledger.release_reservation",
		budget_line_name=line.name,
		procuring_entity=line.procuring_entity,
		payload={"amount": amt, "entry": doc.name},
	)
	return doc.name


def commit_budget(
	budget_line_id: str,
	amount: float,
	*,
	from_reservation: bool = True,
	source_doctype: str,
	source_docname: str,
	source_action: str,
	source_business_id: str | None = None,
	related: dict[str, str | None] | None = None,
	idempotency_key: str | None = None,
	posting_datetime: datetime | str | None = None,
) -> str:
	"""Post a commitment. If ``from_reservation``, requires reserved balance >= amount.

	Otherwise posts **Commit From Available** and requires uncommitted availability >= amount.
	"""
	_lock_budget_line_row(budget_line_id)
	if idempotency_key:
		existing = frappe.db.get_value(
			BLE,
			{"idempotency_key": idempotency_key, "budget_line": budget_line_id},
			"name",
		)
		if existing:
			return existing
	line = _require_budget_line(budget_line_id)
	amt = flt(amount)
	if amt <= 0:
		frappe.throw(_("Amount must be positive."), frappe.ValidationError)
	if from_reservation:
		r, _, _ = aggregate_ledger_buckets(budget_line_id, as_of_datetime=posting_datetime)
		if r < amt - 1e-9:
			frappe.throw(
				_("Reserved balance {0} is less than commit amount {1}.").format(r, amt),
				frappe.ValidationError,
				title=_("Insufficient reservation"),
			)
		entry_type = ENTRY_COMMIT_FROM_RESERVED
	else:
		if availability_headroom(budget_line_id, as_of_datetime=posting_datetime) < amt:
			frappe.throw(
				_("Insufficient budget availability to commit {0}.").format(amt),
				frappe.ValidationError,
				title=_("Insufficient funds"),
			)
		entry_type = ENTRY_COMMIT_FROM_AVAILABLE
	doc = _insert_ledger_row(
		line,
		entry_type=entry_type,
		amount=amt,
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_action=source_action,
		source_business_id=source_business_id,
		posting_datetime=posting_datetime,
		related=related,
		idempotency_key=idempotency_key,
	)
	_sync_budget_line_denorm(budget_line_id)
	_log_ledger_audit(
		event_type="kt.budget.ledger.commit",
		budget_line_name=line.name,
		procuring_entity=line.procuring_entity,
		payload={"amount": amt, "entry": doc.name, "from_reservation": from_reservation},
	)
	return doc.name


def release_commitment(
	budget_line_id: str,
	amount: float,
	*,
	source_doctype: str,
	source_docname: str,
	source_action: str,
	source_business_id: str | None = None,
	related: dict[str, str | None] | None = None,
	idempotency_key: str | None = None,
	posting_datetime: datetime | str | None = None,
) -> str:
	"""Post release of commitment (capacity back via ``released`` bucket)."""
	_lock_budget_line_row(budget_line_id)
	if idempotency_key:
		existing = frappe.db.get_value(
			BLE,
			{"idempotency_key": idempotency_key, "budget_line": budget_line_id},
			"name",
		)
		if existing:
			return existing
	line = _require_budget_line(budget_line_id)
	amt = flt(amount)
	if amt <= 0:
		frappe.throw(_("Amount must be positive."), frappe.ValidationError)
	_, c, _ = aggregate_ledger_buckets(budget_line_id, as_of_datetime=posting_datetime)
	if c < amt - 1e-9:
		frappe.throw(
			_("Committed balance {0} is less than release amount {1}.").format(c, amt),
			frappe.ValidationError,
			title=_("Insufficient commitment"),
		)
	doc = _insert_ledger_row(
		line,
		entry_type=ENTRY_RELEASE_COMMITMENT,
		amount=amt,
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_action=source_action,
		source_business_id=source_business_id,
		posting_datetime=posting_datetime,
		related=related,
		idempotency_key=idempotency_key,
	)
	_sync_budget_line_denorm(budget_line_id)
	_log_ledger_audit(
		event_type="kt.budget.ledger.release_commitment",
		budget_line_name=line.name,
		procuring_entity=line.procuring_entity,
		payload={"amount": amt, "entry": doc.name},
	)
	return doc.name
