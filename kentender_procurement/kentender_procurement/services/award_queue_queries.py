# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for award desk queues and script reports (PROC-STORY-085)."""

from __future__ import annotations

from typing import Any

import frappe

AD = "Award Decision"
ADR = "Award Deviation Record"
AN = "Award Notification"
SSP = "Standstill Period"
TENDER = "Tender"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _tender_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	ent = _norm(procuring_entity)
	if not ent:
		return None
	tns = frappe.get_all(TENDER, filters={"procuring_entity": ent}, pluck="name") or []
	return tns


def get_awards_pending_approval(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	"""Awards in early workflow states awaiting approver action."""
	filters: dict[str, Any] = {
		"status": ("not in", ("Approved", "Rejected", "Cancelled", "Locked")),
		"approval_status": ("in", ("Draft", "Pending")),
		"workflow_state": ("in", ("Draft", "In Progress")),
	}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		AD,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"evaluation_session",
			"status",
			"workflow_state",
			"approval_status",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_awards_pending_final_approval(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	"""Awards in pending final approval state."""
	filters: dict[str, Any] = {
		"workflow_state": "Pending Approval",
		"approval_status": "Pending",
		"status": ("not in", ("Rejected", "Cancelled")),
	}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		AD,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"evaluation_session",
			"status",
			"workflow_state",
			"approval_status",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_standstill_active_awards(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		SSP,
		filters={"status": "Active"},
		fields=["name", "award_decision", "start_datetime", "end_datetime", "complaint_hold_flag", "modified"],
		order_by="modified desc",
		limit=500,
	)
	if not rows:
		return []
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None and not tns:
		return []
	out: list[dict[str, Any]] = []
	for r in rows:
		ad_name = _norm(r.get("award_decision"))
		if not ad_name:
			continue
		tn = _norm(frappe.db.get_value(AD, ad_name, "tender"))
		if tns is not None and tn not in tns:
			continue
		out.append({**r, "tender": tn})
	return out


def get_awards_ready_for_contract(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"ready_for_contract_creation": 1, "status": "Approved", "approval_status": "Approved"}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		AD,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"tender",
			"evaluation_session",
			"standstill_required",
			"standstill_period",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_award_deviation_register(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		ad_names = frappe.get_all(AD, filters={"tender": ("in", tns)}, pluck="name") or []
		if not ad_names:
			return []
		filters["award_decision"] = ("in", ad_names)
	return frappe.get_all(
		ADR,
		filters=filters,
		fields=[
			"name",
			"award_decision",
			"deviation_type",
			"status",
			"recommended_supplier",
			"approved_supplier",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_award_notification_status(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		AN,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"award_decision",
			"tender",
			"notification_type",
			"status",
			"delivery_status",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def award_queue_report_columns(keys: list[str]) -> list[dict[str, Any]]:
	return [{"fieldname": k, "label": k.replace("_", " ").title(), "fieldtype": "Data", "width": 120} for k in keys]


def award_queue_row_values(row: dict[str, Any], keys: list[str]) -> list[Any]:
	return [row.get(k) for k in keys]


def award_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": "Procuring Entity",
			"fieldtype": "Link",
			"options": "Procuring Entity",
			"default": "",
		}
	]
