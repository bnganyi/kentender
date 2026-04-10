# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Requisition Planning Link allocation rules: no over-planning vs PR header or line quantities."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender_procurement.services.requisition_planning_derivation import LINK_DOCTYPE, PR_DOCTYPE

# Match tolerance used in requisition_planning_derivation (partial vs full coverage).
PLANNING_AMOUNT_TOLERANCE = 1e-9

PRI_DOCTYPE = "Purchase Requisition Item"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def sum_active_linked_amount_for_pr(pr_name: str, *, exclude_planning_link: str | None = None) -> float:
	"""Sum ``linked_amount`` for Active links on this requisition (optionally excluding one row)."""
	pr_name = _norm(pr_name)
	if not pr_name:
		return 0.0
	rows = frappe.get_all(
		LINK_DOCTYPE,
		filters={"purchase_requisition": pr_name, "status": "Active"},
		fields=["name", "linked_amount"],
	)
	ex = _norm(exclude_planning_link)
	total = 0.0
	for row in rows:
		if ex and row.name == ex:
			continue
		total += flt(row.get("linked_amount"))
	return total


def validate_active_link_within_requested_amount(doc: Document) -> None:
	"""Reject if this Active link would make total Active ``linked_amount`` exceed PR ``requested_amount``."""
	if _norm(doc.get("status")) != "Active":
		return
	pr_name = _norm(doc.get("purchase_requisition"))
	if not pr_name:
		return
	requested = flt(frappe.db.get_value(PR_DOCTYPE, pr_name, "requested_amount"))
	exclude = doc.name if not doc.is_new() else None
	other = sum_active_linked_amount_for_pr(pr_name, exclude_planning_link=exclude)
	total = other + flt(doc.get("linked_amount"))
	if total > requested + PLANNING_AMOUNT_TOLERANCE:
		frappe.throw(
			_(
				"Total active linked amount ({0}) would exceed the requisition requested amount ({1}). "
				"Reduce this link or other active links."
			).format(total, requested),
			frappe.ValidationError,
			title=_("Over-planning not allowed"),
		)


def _apply_line_linked_amount_from_quantity(doc: Document) -> None:
	"""When line-level planning is used, derive ``linked_amount`` from quantity × unit cost (single source of truth)."""
	line_name = _norm(doc.get("purchase_requisition_item"))
	qty = flt(doc.get("linked_quantity"))
	if not line_name and qty <= PLANNING_AMOUNT_TOLERANCE:
		return
	if line_name and qty <= PLANNING_AMOUNT_TOLERANCE:
		frappe.throw(
			_("Linked Quantity must be greater than zero when a requisition line is selected."),
			frappe.ValidationError,
			title=_("Invalid quantity"),
		)
	if qty > PLANNING_AMOUNT_TOLERANCE and not line_name:
		frappe.throw(
			_("Purchase Requisition Item is required when Linked Quantity is set."),
			frappe.ValidationError,
			title=_("Missing line"),
		)
	parent = frappe.db.get_value(PRI_DOCTYPE, line_name, "parent")
	if _norm(parent) != _norm(doc.get("purchase_requisition")):
		frappe.throw(
			_("Purchase Requisition Item must belong to the same Purchase Requisition as this link."),
			frappe.ValidationError,
			title=_("Invalid line"),
		)
	unit = flt(frappe.db.get_value(PRI_DOCTYPE, line_name, "estimated_unit_cost"))
	doc.linked_amount = qty * unit


def sum_active_linked_quantity_for_line(
	requisition_line_name: str, *, exclude_planning_link: str | None = None
) -> float:
	total = 0.0
	rows = frappe.get_all(
		LINK_DOCTYPE,
		filters={
			"purchase_requisition_item": requisition_line_name,
			"status": "Active",
		},
		fields=["name", "linked_quantity"],
	)
	ex = _norm(exclude_planning_link)
	for row in rows:
		if ex and row.name == ex:
			continue
		total += flt(row.get("linked_quantity"))
	return total


def validate_active_link_within_line_quantity(doc: Document) -> None:
	"""If line fields are used, ensure sum Active ``linked_quantity`` ≤ line ``quantity``."""
	if _norm(doc.get("status")) != "Active":
		return
	line_name = _norm(doc.get("purchase_requisition_item"))
	if not line_name:
		return
	qty_line = flt(frappe.db.get_value(PRI_DOCTYPE, line_name, "quantity"))
	exclude = doc.name if not doc.is_new() else None
	other = sum_active_linked_quantity_for_line(line_name, exclude_planning_link=exclude)
	total_q = other + flt(doc.get("linked_quantity"))
	if total_q > qty_line + PLANNING_AMOUNT_TOLERANCE:
		frappe.throw(
			_(
				"Total active linked quantity for this line ({0}) would exceed the line quantity ({1})."
			).format(total_q, qty_line),
			frappe.ValidationError,
			title=_("Over-allocation on line"),
		)


def validate_requisition_planning_link_allocation(doc: Document) -> None:
	"""Full allocation validation for Requisition Planning Link (header + optional line mode)."""
	_apply_line_linked_amount_from_quantity(doc)
	validate_active_link_within_requested_amount(doc)
	validate_active_link_within_line_quantity(doc)


def refresh_purchase_requisition_item_planning_quantities(pr_name: str) -> None:
	"""Persist ``planned_quantity`` / ``remaining_quantity`` on PR lines from Active RPL aggregates."""
	pr_name = _norm(pr_name)
	if not pr_name or not frappe.db.exists(PR_DOCTYPE, pr_name):
		return
	items = frappe.get_all(
		PRI_DOCTYPE,
		filters={"parent": pr_name, "parenttype": PR_DOCTYPE},
		fields=["name", "quantity"],
	)
	if not items:
		return
	planned_by_line: dict[str, float] = {}
	for row in frappe.get_all(
		LINK_DOCTYPE,
		filters={"purchase_requisition": pr_name, "status": "Active"},
		fields=["purchase_requisition_item", "linked_quantity"],
	):
		ln = _norm(row.get("purchase_requisition_item"))
		if not ln:
			continue
		planned_by_line[ln] = planned_by_line.get(ln, 0.0) + flt(row.get("linked_quantity"))

	for it in items:
		name = it.name
		qty = flt(it.quantity)
		planned = planned_by_line.get(name, 0.0)
		remaining = max(0.0, qty - planned)
		frappe.db.set_value(
			PRI_DOCTYPE,
			name,
			{"planned_quantity": planned, "remaining_quantity": remaining},
			update_modified=False,
		)
