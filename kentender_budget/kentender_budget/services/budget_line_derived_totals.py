# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget Line denormalized totals (BUD-006).

**Ledger is authoritative** (BUD-007 Budget Ledger Entry onward). Fields on Budget Line such as
``reserved_amount`` / ``committed_amount`` / ``consumed_actual_amount`` are convenience copies
maintained by posting services or migration jobs—not a second source of truth.

``available_amount`` is **always derived** on save from the stored components using
``compute_available_amount`` so the UI/API cannot persist a stale or hand-edited “available” figure.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import flt


def compute_available_amount(
	allocated: Any,
	reserved: Any,
	committed: Any,
	released: Any,
	consumed_actual: Any,
) -> float:
	"""Preview availability from denormalized components (non-authoritative).

	Formula::

	    available = allocated − reserved − committed − consumed_actual + released

	``released`` represents capacity returned to the line (e.g. reservation release), so it
	increases availability. When the ledger is introduced, component fields should be written
	only from posting logic; this function remains the single definition of how *available*
	is derived from those copies for the line document.
	"""
	a = flt(allocated)
	r = flt(reserved)
	c = flt(committed)
	rel = flt(released)
	con = flt(consumed_actual)
	return a - r - c - con + rel


def recalculate_budget_line_derived_totals(doc: Document) -> None:
	"""Set ``available_amount`` on *doc* from other amount fields (idempotent).

	Safe to call from ``validate``, hooks, or future ledger workers (BUD-008).
	"""
	doc.available_amount = compute_available_amount(
		doc.get("allocated_amount"),
		doc.get("reserved_amount"),
		doc.get("committed_amount"),
		doc.get("released_amount"),
		doc.get("consumed_actual_amount"),
	)


def run_validate_recalculate_derived_totals(doc: Document, method: str | None = None) -> None:
	"""``doc_events`` entry for Budget Line ``validate`` (runs after controller ``validate``)."""
	recalculate_budget_line_derived_totals(doc)


def on_budget_ledger_post_recalculate_line(budget_line_name: str) -> None:
	"""Hook target for BUD-008: reload line and refresh derived totals after ledger posting.

	Posting services should aggregate ledger entries first, update component fields on the
	Budget Line via their own APIs, then call this so ``available_amount`` stays consistent.
	"""
	if not budget_line_name or not frappe.db.exists("Budget Line", budget_line_name):
		return
	line = frappe.get_doc("Budget Line", budget_line_name)
	recalculate_budget_line_derived_totals(line)
	line.db_set("available_amount", line.available_amount, update_modified=False)
