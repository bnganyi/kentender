# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for procurement plan desk queues and script reports (PROC-STORY-022).

These functions return lightweight row dicts for reporting; they do not mutate data.

*Plan Items Ready for Tender* uses :func:`get_plan_item_tender_eligibility` as the source
of truth (bounded scan, default *limit* 500 eligible rows).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.services.plan_item_tender_eligibility import (
	ITEM_STATUS_ELIGIBLE,
	get_plan_item_tender_eligibility,
)

PP = "Procurement Plan"
PPI = "Procurement Plan Item"
PFA = "Plan Fragmentation Alert"

_PLAN_LIST_FIELDS = [
	"name",
	"plan_title",
	"workflow_state",
	"status",
	"procuring_entity",
	"modified",
]

_SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _entity_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def get_planning_queue_plans(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Procurement plans in pre-approval workflow (Draft, Submitted, Returned)."""
	filters: dict[str, Any] = {
		"workflow_state": ("in", ["Draft", "Submitted", "Returned"]),
		"status": ("!=", "Cancelled"),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		PP,
		filters=filters,
		fields=_PLAN_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_draft_procurement_plans(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {
		"workflow_state": "Draft",
		"status": ("!=", "Cancelled"),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		PP,
		filters=filters,
		fields=_PLAN_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_active_procurement_plans(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Plans approved or active (aligned with tender eligibility parent states)."""
	filters: dict[str, Any] = {
		"workflow_state": ("in", ["Approved", "Active"]),
		"status": ("!=", "Cancelled"),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		PP,
		filters=filters,
		fields=_PLAN_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_open_fragmentation_alerts(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Open or under-review fragmentation alerts, worst severity first."""
	filters: dict[str, Any] = {"status": ("in", ["Open", "Under Review"])}
	ent = _norm(procuring_entity)
	if ent:
		plan_names = frappe.get_all(PP, filters={"procuring_entity": ent}, pluck="name") or []
		if not plan_names:
			return []
		filters["procurement_plan"] = ("in", plan_names)
	rows = frappe.get_all(
		PFA,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"procurement_plan",
			"related_plan_item",
			"alert_type",
			"severity",
			"status",
			"raised_on",
			"modified",
		],
		limit=limit,
		order_by="modified desc",
	)

	def sort_key(r: dict[str, Any]) -> tuple[int, Any]:
		sev = _norm(r.get("severity"))
		return (_SEVERITY_ORDER.get(sev, 99), r.get("raised_on") or r.get("modified"))

	rows.sort(key=sort_key)
	return rows


def get_plan_items_ready_for_tender(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
	scan_cap: int = 3000,
) -> list[dict[str, Any]]:
	"""Plan items where :func:`get_plan_item_tender_eligibility` is eligible.

	Scans up to *scan_cap* candidate items (pre-filtered by SQL) and returns at most
	*limit* eligible rows.
	"""
	ent = _norm(procuring_entity)
	plan_filters: dict[str, Any] = {"workflow_state": ("in", ["Approved", "Active"])}
	if ent:
		plan_filters["procuring_entity"] = ent
	plan_names = frappe.get_all(PP, filters=plan_filters, pluck="name") or []
	if not plan_names:
		return []

	items = frappe.get_all(
		PPI,
		filters={
			"procurement_plan": ("in", plan_names),
			"status": ("in", list(ITEM_STATUS_ELIGIBLE)),
			"fragmentation_alert_status": ("not in", ["Warning", "Blocked"]),
		},
		fields=["name", "procurement_plan", "procuring_entity", "status", "fragmentation_alert_status"],
		order_by="modified desc",
		limit=scan_cap,
	)
	out: list[dict[str, Any]] = []
	for row in items:
		meta = get_plan_item_tender_eligibility(row["name"])
		if not meta.get("eligible"):
			continue
		out.append(
			{
				"name": meta.get("procurement_plan_item"),
				"procurement_plan": meta.get("procurement_plan"),
				"procuring_entity": row.get("procuring_entity"),
				"status": meta.get("item_status"),
				"plan_workflow_state": meta.get("plan_workflow_state"),
				"fragmentation_alert_status": meta.get("fragmentation_alert_status"),
			}
		)
		if len(out) >= limit:
			break
	return out


def procurement_plan_report_columns() -> list[str]:
	return [
		_("Plan") + ":Link/Procurement Plan:160",
		_("Title") + ":Data:200",
		_("Workflow Stage") + ":Data:120",
		_("Status") + ":Data:100",
		_("Procuring Entity") + ":Link/Procuring Entity:160",
		_("Modified") + ":Datetime:150",
	]


def procurement_plan_report_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("plan_title"),
		r.get("workflow_state"),
		r.get("status"),
		r.get("procuring_entity"),
		r.get("modified"),
	]


def plan_item_tender_ready_columns() -> list[str]:
	return [
		_("Plan Item") + ":Link/Procurement Plan Item:180",
		_("Procurement Plan") + ":Link/Procurement Plan:160",
		_("Procuring Entity") + ":Link/Procuring Entity:160",
		_("Item Status") + ":Data:100",
		_("Plan Workflow") + ":Data:100",
		_("Fragmentation") + ":Data:120",
	]


def plan_item_tender_ready_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("procurement_plan"),
		r.get("procuring_entity"),
		r.get("status"),
		r.get("plan_workflow_state"),
		r.get("fragmentation_alert_status"),
	]


def fragmentation_alert_report_columns() -> list[str]:
	return [
		_("Alert") + ":Link/Plan Fragmentation Alert:160",
		_("Business ID") + ":Data:120",
		_("Procurement Plan") + ":Link/Procurement Plan:160",
		_("Related Plan Item") + ":Link/Procurement Plan Item:160",
		_("Alert Type") + ":Data:180",
		_("Severity") + ":Data:80",
		_("Status") + ":Data:100",
		_("Raised On") + ":Datetime:150",
	]


def fragmentation_alert_report_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("procurement_plan"),
		r.get("related_plan_item"),
		r.get("alert_type"),
		r.get("severity"),
		r.get("status"),
		r.get("raised_on"),
	]


def procurement_plan_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]


__all__ = [
	"fragmentation_alert_report_columns",
	"fragmentation_alert_report_row_values",
	"get_active_procurement_plans",
	"get_draft_procurement_plans",
	"get_open_fragmentation_alerts",
	"get_plan_items_ready_for_tender",
	"get_planning_queue_plans",
	"plan_item_tender_ready_columns",
	"plan_item_tender_ready_row_values",
	"procurement_plan_report_columns",
	"procurement_plan_report_entity_filter",
	"procurement_plan_report_row_values",
]
