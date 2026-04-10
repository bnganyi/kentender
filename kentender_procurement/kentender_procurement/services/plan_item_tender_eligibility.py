# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender eligibility for **Procurement Plan Item** (PROC-STORY-021).

Read-only helper used by **Plan to Tender Link** validation and services.

Rules (v1):

- Item must exist and not be **Cancelled** or **Superseded** (same spirit as
  ``EXCLUDED_PPI_STATUSES`` in procurement totals).
- Parent **Procurement Plan** ``workflow_state`` must be **Approved** or **Active**
  (not Draft / Rejected / Returned).
- Item ``status`` must be **Approved** or **Active** (not Draft / Planned / terminal).
- **Fragmentation:** ``fragmentation_alert_status`` **Warning** or **Blocked**
  makes the item ineligible (conservative gate until fragmentation is cleared).
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.services.procurement_plan_totals import EXCLUDED_PPI_STATUSES

PP_DOCTYPE = "Procurement Plan"
PPI_DOCTYPE = "Procurement Plan Item"

PLAN_WORKFLOW_ELIGIBLE = frozenset({"Approved", "Active"})
ITEM_STATUS_ELIGIBLE = frozenset({"Approved", "Active"})
FRAGMENTATION_BLOCKING = frozenset({"Warning", "Blocked"})


def _strip(s: str | None) -> str:
	return (s or "").strip()


def get_plan_item_tender_eligibility(procurement_plan_item: str) -> dict[str, Any]:
	"""Return eligibility for tender creation / active plan-to-tender links.

	:returns: ``eligible`` (bool), ``reasons`` (list of human-readable strings),
	  plus ``procurement_plan_item``, ``procurement_plan``, ``item_status``,
	  ``plan_workflow_state``, ``fragmentation_alert_status`` for diagnostics.
	"""
	name = _strip(procurement_plan_item)
	empty_meta: dict[str, Any] = {
		"eligible": False,
		"reasons": [],
		"procurement_plan_item": name or None,
		"procurement_plan": None,
		"item_status": None,
		"plan_workflow_state": None,
		"fragmentation_alert_status": None,
	}
	if not name:
		empty_meta["reasons"] = ["Procurement Plan Item is required."]
		return empty_meta

	ppi = frappe.db.get_value(
		PPI_DOCTYPE,
		name,
		[
			"name",
			"procurement_plan",
			"status",
			"fragmentation_alert_status",
		],
		as_dict=True,
	)
	if not ppi:
		empty_meta["reasons"] = [f"Procurement Plan Item {name!r} does not exist."]
		return empty_meta

	reasons: list[str] = []
	st = _strip(ppi.get("status"))
	plan_name = _strip(ppi.get("procurement_plan"))
	fas = _strip(ppi.get("fragmentation_alert_status")) or "Not Assessed"

	if st in EXCLUDED_PPI_STATUSES:
		reasons.append(f"Plan item status {st!r} is not eligible for tender linkage.")

	plan_ws = ""
	if plan_name:
		row = frappe.db.get_value(
			PP_DOCTYPE,
			plan_name,
			["name", "workflow_state"],
			as_dict=True,
		)
		if row:
			plan_ws = _strip(row.get("workflow_state"))
		else:
			reasons.append("Parent procurement plan is missing.")
	else:
		reasons.append("Procurement Plan Item has no procurement plan.")

	if plan_ws and plan_ws not in PLAN_WORKFLOW_ELIGIBLE:
		reasons.append(
			f"Procurement plan workflow stage must be Approved or Active (currently {plan_ws!r})."
		)

	if st and st not in ITEM_STATUS_ELIGIBLE and st not in EXCLUDED_PPI_STATUSES:
		reasons.append(
			f"Plan item must be Approved or Active for tender linkage (currently {st!r})."
		)

	if fas in FRAGMENTATION_BLOCKING:
		reasons.append(
			f"Fragmentation alert status is {fas!r}; resolve fragmentation before linking a tender."
		)

	return {
		"eligible": len(reasons) == 0,
		"reasons": reasons,
		"procurement_plan_item": name,
		"procurement_plan": plan_name or None,
		"item_status": st or None,
		"plan_workflow_state": plan_ws or None,
		"fragmentation_alert_status": fas,
	}


__all__ = ["get_plan_item_tender_eligibility", "PLAN_WORKFLOW_ELIGIBLE", "ITEM_STATUS_ELIGIBLE"]
