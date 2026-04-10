# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for opening desk queues and script reports (PROC-STORY-056)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

BOS = "Bid Opening Session"
BOR = "Bid Opening Register"

_WS_DONE = ("Completed", "Cancelled")


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _entity_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def get_scheduled_opening_sessions(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Sessions in **Scheduled** workflow (upcoming ceremony)."""
	filters: dict[str, Any] = {"workflow_state": "Scheduled"}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		BOS,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"procuring_entity",
			"workflow_state",
			"status",
			"scheduled_opening_datetime",
			"modified",
		],
		order_by="scheduled_opening_datetime asc",
		limit=limit,
	)


def get_ready_for_opening_sessions(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Active sessions not yet atomically completed (desk \"ready\" queue)."""
	filters: dict[str, Any] = {
		"workflow_state": ("not in", list(_WS_DONE)),
		"is_atomic_opening_complete": 0,
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		BOS,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"procuring_entity",
			"workflow_state",
			"status",
			"scheduled_opening_datetime",
			"precondition_check_status",
			"modified",
		],
		order_by="scheduled_opening_datetime asc",
		limit=limit,
	)


def get_completed_opening_sessions(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Completed opening sessions."""
	filters: dict[str, Any] = {"workflow_state": "Completed"}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		BOS,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"procuring_entity",
			"workflow_state",
			"status",
			"actual_opening_datetime",
			"opened_bid_count",
			"excluded_bid_count",
			"modified",
		],
		order_by="actual_opening_datetime desc",
		limit=limit,
	)


def get_opening_registers(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Opening registers (via linked tender procuring entity)."""
	ent = _norm(procuring_entity)
	if ent:
		tenders = frappe.get_all("Tender", filters={"procuring_entity": ent}, pluck="name") or []
		if not tenders:
			return []
		filters: dict[str, Any] = {"tender": ("in", tenders)}
	else:
		filters = {}
	return frappe.get_all(
		BOR,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"bid_opening_session",
			"status",
			"is_locked",
			"total_opened_bids",
			"total_excluded_bids",
			"generated_on",
			"modified",
		],
		order_by="generated_on desc",
		limit=limit,
	)


def get_opening_exclusion_rows(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Register lines marked excluded (opening exceptions)."""
	ent = _norm(procuring_entity)
	filters: dict[str, Any] = {"was_excluded": 1}
	if ent:
		tenders = frappe.get_all("Tender", filters={"procuring_entity": ent}, pluck="name") or []
		if not tenders:
			return []
		reg_names = frappe.get_all(BOR, filters={"tender": ("in", tenders)}, pluck="name") or []
		if not reg_names:
			return []
		filters["parent"] = ("in", reg_names)
	rows = frappe.get_all(
		"Bid Opening Register Line",
		filters=filters,
		fields=[
			"name",
			"parent",
			"bid_submission",
			"supplier",
			"exclusion_reason",
			"was_opened",
		],
		order_by="modified desc",
		limit=limit,
	)
	return rows


def opening_session_report_columns() -> list[str]:
	return [
		_("Session") + ":Link/Bid Opening Session:180",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Workflow") + ":Data:130",
		_("Status") + ":Data:100",
		_("Scheduled") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def opening_session_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("tender"),
		r.get("workflow_state"),
		r.get("status"),
		r.get("scheduled_opening_datetime"),
		r.get("modified"),
	]


def opening_register_report_columns() -> list[str]:
	return [
		_("Register") + ":Link/Bid Opening Register:180",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Session") + ":Link/Bid Opening Session:180",
		_("Status") + ":Data:100",
		_("Locked") + ":Check:70",
		_("Opened") + ":Int:80",
		_("Excluded") + ":Int:80",
		_("Generated On") + ":Datetime:150",
	]


def opening_register_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("tender"),
		r.get("bid_opening_session"),
		r.get("status"),
		r.get("is_locked"),
		r.get("total_opened_bids"),
		r.get("total_excluded_bids"),
		r.get("generated_on"),
	]


def opening_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]
