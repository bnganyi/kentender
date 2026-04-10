# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget header rollups: ``total_allocated_amount`` is the sum of line ``allocated_amount`` values."""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt


def sum_allocated_amount_for_budget(budget_name: str, *, exclude_line_name: str | None = None) -> float:
	"""Sum ``allocated_amount`` on Budget Lines for this budget (optionally excluding one row, e.g. on trash)."""
	if not budget_name:
		return 0.0
	q = "SELECT COALESCE(SUM(`allocated_amount`), 0) FROM `tabBudget Line` WHERE `budget` = %s"
	params: list = [budget_name]
	if exclude_line_name:
		q += " AND `name` != %s"
		params.append(exclude_line_name)
	row = frappe.db.sql(q, tuple(params))
	return flt(row[0][0] if row else 0)


def refresh_budget_total_allocated_from_lines(
	budget_name: str, *, exclude_line_name: str | None = None
) -> None:
	"""Persist header total from lines (``update_modified=False``: derived field)."""
	if not budget_name or not frappe.db.exists("Budget", budget_name):
		return
	total = sum_allocated_amount_for_budget(budget_name, exclude_line_name=exclude_line_name)
	frappe.db.set_value(
		"Budget",
		budget_name,
		"total_allocated_amount",
		total,
		update_modified=False,
	)


def run_refresh_parent_budget_total_after_line_save(doc: Document, method: str | None = None) -> None:
	b = (doc.get("budget") or "").strip()
	if b:
		refresh_budget_total_allocated_from_lines(b)


def run_refresh_parent_budget_total_after_line_trash(doc: Document, method: str | None = None) -> None:
	b = (doc.get("budget") or "").strip()
	if b and doc.name:
		refresh_budget_total_allocated_from_lines(b, exclude_line_name=doc.name)
