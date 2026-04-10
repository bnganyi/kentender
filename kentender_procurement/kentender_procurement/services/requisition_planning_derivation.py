# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Derive Purchase Requisition planning totals and status from Requisition Planning Link (PROC-STORY-009).

Only **Active** links contribute to ``planned_amount``. ``Released`` and ``Superseded`` are ignored.

Status rules (``requested_amount`` from the requisition):

- **Unplanned:** no qualifying linked amount (or zero). (Pack “Not Planned”.)
- **Partially Planned:** active linked sum ``> 0`` and ``< requested_amount``.
- **Planned:** active linked sum ``>= requested_amount`` (within float tolerance).
- **Linked:** same as full coverage, and at least one active link has a non-empty
  ``procurement_plan`` or ``procurement_plan_item`` (converted-to-plan signal).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import flt

LINK_DOCTYPE = "Requisition Planning Link"
PR_DOCTYPE = "Purchase Requisition"

STATUS_UNPLANNED = "Unplanned"
STATUS_PARTIAL = "Partially Planned"
STATUS_PLANNED = "Planned"
STATUS_LINKED = "Linked"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def compute_requisition_planning_derivation(
	pr_name: str,
	*,
	requested_amount: float | None = None,
	exclude_planning_link: str | None = None,
) -> dict[str, Any]:
	if requested_amount is None:
		requested_amount = flt(frappe.db.get_value(PR_DOCTYPE, pr_name, "requested_amount"))
	else:
		requested_amount = flt(requested_amount)

	links = frappe.get_all(
		LINK_DOCTYPE,
		filters={"purchase_requisition": pr_name, "status": "Active"},
		fields=[
			"name",
			"linked_amount",
			"procurement_plan",
			"procurement_plan_item",
			"linked_on",
		],
		order_by="linked_on desc",
	)
	ex = _norm(exclude_planning_link)
	if ex:
		links = [row for row in links if row.name != ex]

	planned = sum(flt(row.get("linked_amount")) for row in links)
	unplanned = max(0.0, requested_amount - planned)

	if planned <= 1e-9:
		ps = STATUS_UNPLANNED
	elif planned + 1e-9 < requested_amount:
		ps = STATUS_PARTIAL
	else:
		has_plan_ref = any(
			_norm(row.get("procurement_plan")) or _norm(row.get("procurement_plan_item"))
			for row in links
		)
		ps = STATUS_LINKED if has_plan_ref else STATUS_PLANNED

	latest_plan = ""
	latest_item = ""
	if links:
		top = links[0]
		latest_plan = _norm(top.get("procurement_plan"))
		latest_item = _norm(top.get("procurement_plan_item"))

	return {
		"planned_amount": planned,
		"unplanned_amount": unplanned,
		"planning_status": ps,
		"latest_procurement_plan": latest_plan or None,
		"latest_procurement_plan_item": latest_item or None,
	}


def refresh_requisition_planning_derived_fields(
	pr_name: str,
	*,
	exclude_planning_link: str | None = None,
) -> None:
	"""Persist derived planning fields on the Purchase Requisition (e.g. after link CRUD)."""
	pr_name = _norm(pr_name)
	if not pr_name or not frappe.db.exists(PR_DOCTYPE, pr_name):
		return
	vals = compute_requisition_planning_derivation(pr_name, exclude_planning_link=exclude_planning_link)
	frappe.db.set_value(PR_DOCTYPE, pr_name, vals, update_modified=False)


def apply_requisition_planning_derivation_to_doc(doc: Document) -> None:
	"""Set in-memory planning fields during PR ``validate`` (uses current ``requested_amount``)."""
	vals = compute_requisition_planning_derivation(
		doc.name,
		requested_amount=flt(doc.get("requested_amount")),
	)
	for key, val in vals.items():
		doc.set(key, val)
