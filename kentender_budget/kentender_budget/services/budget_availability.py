# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget availability from authoritative ledger semantics (BUD-009).

Balances are derived from **Budget Ledger Entry** rows only—not from hand-edited Budget Line
movement fields (those are synced for UX and must match ledger totals after posting).

``allocated`` comes from ``Budget Line.allocated_amount`` (envelope). ``available`` uses the
same formula as :func:`kentender_budget.services.budget_line_derived_totals.compute_available_amount`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import frappe
from frappe.utils import flt, get_datetime

from kentender_budget.services.budget_line_derived_totals import compute_available_amount

BLE = "Budget Ledger Entry"
BL = "Budget Line"

ENTRY_RESERVE = "Reserve"
ENTRY_RELEASE_RESERVATION = "Release Reservation"
ENTRY_COMMIT_FROM_RESERVED = "Commit From Reserved"
ENTRY_COMMIT_FROM_AVAILABLE = "Commit From Available"
ENTRY_RELEASE_COMMITMENT = "Release Commitment"

DIR_IN = "In"
DIR_OUT = "Out"


def _sign(direction: str | None) -> float:
	return -1.0 if (direction or "").strip() == DIR_OUT else 1.0


def aggregate_ledger_buckets(
	budget_line_id: str,
	*,
	as_of_datetime: datetime | str | None = None,
) -> tuple[float, float, float]:
	"""Return (reserved, committed, released) from Posted ledger rows for the line."""
	as_of = get_datetime(as_of_datetime) if as_of_datetime else None
	rows = frappe.db.sql(
		f"""
		select entry_type, entry_direction, amount, posting_datetime
		from `tab{BLE}`
		where budget_line = %s and status = 'Posted'
		order by posting_datetime asc, creation asc
		""",
		(budget_line_id,),
		as_dict=False,
	)
	reserved = 0.0
	committed = 0.0
	released = 0.0
	for entry_type, entry_direction, amount, posting_dt in rows:
		if as_of and get_datetime(posting_dt) > as_of:
			continue
		a = flt(amount) * _sign(entry_direction)
		et = (entry_type or "").strip()
		if et == ENTRY_RESERVE:
			reserved += a
		elif et == ENTRY_RELEASE_RESERVATION:
			reserved -= a
			released += a
		elif et == ENTRY_COMMIT_FROM_RESERVED:
			reserved -= a
			committed += a
		elif et == ENTRY_COMMIT_FROM_AVAILABLE:
			committed += a
		elif et == ENTRY_RELEASE_COMMITMENT:
			committed -= a
			released += a
	return reserved, committed, released


def _line_allocated_and_consumed(budget_line_id: str) -> tuple[float, float]:
	row = frappe.db.get_value(
		BL,
		budget_line_id,
		["allocated_amount", "consumed_actual_amount"],
		as_dict=True,
	)
	if not row:
		return 0.0, 0.0
	return flt(row.allocated_amount), flt(row.consumed_actual_amount)


@dataclass(frozen=True)
class BudgetAvailability:
	allocated: float
	reserved: float
	committed: float
	released: float
	available: float


def get_budget_availability(
	budget_line_id: str,
	as_of_datetime: datetime | str | None = None,
) -> BudgetAvailability:
	"""Full availability breakdown for a budget line from ledger + envelope.

	:param as_of_datetime: Only ledger rows with ``posting_datetime`` at or before this instant
	    are included (exclusive upper bound on later rows). ``None`` means all Posted rows.
	"""
	allocated, consumed = _line_allocated_and_consumed(budget_line_id)
	r, c, rel = aggregate_ledger_buckets(budget_line_id, as_of_datetime=as_of_datetime)
	avail = compute_available_amount(allocated, r, c, rel, consumed)
	return BudgetAvailability(
		allocated=allocated,
		reserved=r,
		committed=c,
		released=rel,
		available=avail,
	)


def availability_headroom(
	budget_line_id: str,
	*,
	as_of_datetime: datetime | str | None = None,
) -> float:
	"""Same as ``get_budget_availability(...).available`` (convenience for posting)."""
	return get_budget_availability(budget_line_id, as_of_datetime=as_of_datetime).available


def minimum_allocated_envelope(budget_line_id: str) -> float:
	"""Minimum ``allocated_amount`` so availability stays non-negative for current ledger + consumed.

	``available = allocated - reserved - committed + released - consumed`` must be ``>= 0`` implies
	``allocated >= reserved + committed - released + consumed``.
	"""
	av = get_budget_availability(budget_line_id)
	_, consumed = _line_allocated_and_consumed(budget_line_id)
	return flt(av.reserved) + flt(av.committed) - flt(av.released) + flt(consumed)
