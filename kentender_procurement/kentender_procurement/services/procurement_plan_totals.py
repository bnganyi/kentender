# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan derived totals and consolidation source reconciliation (PROC-STORY-014)."""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt

PP_DOCTYPE = "Procurement Plan"
PPI_DOCTYPE = "Procurement Plan Item"
RPL_DOCTYPE = "Requisition Planning Link"
PCS_DOCTYPE = "Plan Consolidation Source"

EXCLUDED_PPI_STATUSES = ("Cancelled", "Superseded")

AMOUNT_TOLERANCE = 1e-9


def _strip(s: str | None) -> str:
	return (s or "").strip()


def compute_procurement_plan_totals(plan_name: str) -> dict:
	"""Return derived totals for a Procurement Plan (PROC-STORY-014)."""
	plan_name = _strip(plan_name)
	out = {
		"total_estimated_amount": 0.0,
		"total_item_count": 0,
		"planned_requisition_count": 0,
		"manual_item_count": 0,
		"consolidated_item_count": 0,
	}
	if not plan_name:
		return out

	item_rows = frappe.get_all(
		PPI_DOCTYPE,
		filters={
			"procurement_plan": plan_name,
			"status": ("not in", list(EXCLUDED_PPI_STATUSES)),
		},
		fields=["estimated_amount", "origin_type"],
	)

	total_amt = 0.0
	manual = 0
	consol = 0
	n_items = 0
	for row in item_rows or []:
		n_items += 1
		total_amt += flt(row.get("estimated_amount"))
		o = _strip(row.get("origin_type"))
		if o == "Manual":
			manual += 1
		elif o == "Consolidated":
			consol += 1

	item_names = frappe.get_all(
		PPI_DOCTYPE,
		filters={"procurement_plan": plan_name},
		pluck="name",
	) or []

	if item_names:
		placeholders = ", ".join(["%s"] * len(item_names))
		where_clause = (
			f"status = 'Active' and (procurement_plan = %s or procurement_plan_item in ({placeholders}))"
		)
		params: tuple = (plan_name,) + tuple(item_names)
	else:
		where_clause = "status = 'Active' and procurement_plan = %s"
		params = (plan_name,)

	pr_rows = frappe.db.sql(
		f"select distinct purchase_requisition from `tab{RPL_DOCTYPE}` where {where_clause}",
		params,
	)
	pr_count = len([r for r in (pr_rows or []) if _strip(r[0])])

	out["total_estimated_amount"] = total_amt
	out["total_item_count"] = n_items
	out["manual_item_count"] = manual
	out["consolidated_item_count"] = consol
	out["planned_requisition_count"] = pr_count
	return out


def apply_procurement_plan_totals_to_doc(doc: Document) -> None:
	"""Set in-memory totals on Procurement Plan during validate."""
	pn = _strip(doc.get("name"))
	if not pn:
		return
	vals = compute_procurement_plan_totals(pn)
	for k, v in vals.items():
		doc.set(k, v)


def refresh_procurement_plan_totals(plan_name: str) -> None:
	"""Persist totals after child DocType CRUD (update_modified=False)."""
	pn = _strip(plan_name)
	if not pn or not frappe.db.exists(PP_DOCTYPE, pn):
		return
	vals = compute_procurement_plan_totals(pn)
	frappe.db.set_value(PP_DOCTYPE, pn, vals, update_modified=False)


def reconcile_plan_item_consolidation_sources(procurement_plan_item: str) -> dict:
	"""
	Compare Active Plan Consolidation Source linked_amount sum to PPI estimated_amount.

	If there are no Active PCS rows, returns match True (nothing to reconcile yet).
	"""
	ppi = _strip(procurement_plan_item)
	result = {
		"procurement_plan_item": ppi or None,
		"pcs_total": 0.0,
		"estimated_amount": 0.0,
		"sources_count": 0,
		"match": True,
	}
	if not ppi or not frappe.db.exists(PPI_DOCTYPE, ppi):
		return result

	estimated = flt(frappe.db.get_value(PPI_DOCTYPE, ppi, "estimated_amount"))
	result["estimated_amount"] = estimated

	rows = frappe.db.sql(
		f"""
		select count(*), coalesce(sum(linked_amount), 0)
		from `tab{PCS_DOCTYPE}`
		where procurement_plan_item = %s and status = 'Active'
		""",
		(ppi,),
	)
	cnt, ssum = rows[0] if rows else (0, 0)
	cnt = int(cnt or 0)
	ssum = flt(ssum)
	result["sources_count"] = cnt
	result["pcs_total"] = ssum

	if cnt == 0:
		result["match"] = True
	else:
		result["match"] = abs(ssum - estimated) <= AMOUNT_TOLERANCE

	return result


def list_consolidation_mismatches_for_plan(plan_name: str) -> list[dict]:
	"""Items under plan with Active PCS where sum does not match estimated_amount."""
	plan_name = _strip(plan_name)
	if not plan_name:
		return []

	items = frappe.get_all(
		PPI_DOCTYPE,
		filters={
			"procurement_plan": plan_name,
			"status": ("not in", list(EXCLUDED_PPI_STATUSES)),
		},
		pluck="name",
	) or []

	mismatches: list[dict] = []
	for name in items:
		r = reconcile_plan_item_consolidation_sources(name)
		if not r["match"]:
			mismatches.append(r)
	return mismatches


def procurement_plans_affected_by_rpl(doc: Document) -> set[str]:
	"""Plan docnames touched by a Requisition Planning Link row."""
	plans: set[str] = set()
	pn = _strip(doc.get("procurement_plan"))
	if pn:
		plans.add(pn)
	ppi = _strip(doc.get("procurement_plan_item"))
	if ppi:
		parent = frappe.db.get_value(PPI_DOCTYPE, ppi, "procurement_plan")
		if _strip(parent):
			plans.add(_strip(parent))
	return plans
