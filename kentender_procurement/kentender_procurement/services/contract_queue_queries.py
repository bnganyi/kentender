# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for contract queues and script reports (PROC-STORY-099)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_days, getdate, nowdate

PC = "Procurement Contract"
PCV = "Procurement Contract Variation"
TENDER = "Tender"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _tender_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	ent = _norm(procuring_entity)
	if not ent:
		return None
	return frappe.get_all(TENDER, filters={"procuring_entity": ent}, pluck="name") or []


def get_draft_contracts(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": "Draft"}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		PC,
		filters=filters,
		fields=["name", "business_id", "contract_title", "tender", "status", "workflow_state", "modified"],
		order_by="modified desc",
		limit=500,
	)


def get_contracts_pending_signature(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": "Pending Signature"}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		PC,
		filters=filters,
		fields=["name", "business_id", "contract_title", "tender", "approval_status", "modified"],
		order_by="modified desc",
		limit=500,
	)


def get_active_contracts(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": "Active"}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		PC,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"contract_title",
			"tender",
			"contract_end_date",
			"contract_value",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_variations_awaiting_action(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": ("in", ["Draft", "Submitted", "Approved"])}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		cns = frappe.get_all(PC, filters={"tender": ("in", tns)}, pluck="name") or []
		if not cns:
			return []
		filters["procurement_contract"] = ("in", cns)
	return frappe.get_all(
		PCV,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"procurement_contract",
			"variation_no",
			"status",
			"variation_type",
			"modified",
		],
		order_by="modified desc",
		limit=500,
	)


def get_contracts_near_end_date(
	procuring_entity: str | None = None,
	*,
	days_ahead: int = 90,
) -> list[dict[str, Any]]:
	end_limit = add_days(getdate(nowdate()), days=int(days_ahead))
	base_filters: dict[str, Any] = {"status": ("in", ["Active", "Suspended"])}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		base_filters["tender"] = ("in", tns)

	rows = (
		frappe.get_all(
			PC,
			filters=base_filters,
			fields=[
				"name",
				"business_id",
				"contract_title",
				"tender",
				"contract_end_date",
				"status",
				"modified",
			],
			order_by="contract_end_date asc",
			limit=500,
		)
		or []
	)
	today = getdate(nowdate())
	out = []
	for r in rows:
		ed = r.get("contract_end_date")
		if not ed:
			continue
		ed_dt = getdate(ed)
		if ed_dt < today or ed_dt > end_limit:
			continue
		out.append(r)
	return out


def get_suspended_terminated_contracts(procuring_entity: str | None = None) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"status": ("in", ["Suspended", "Terminated"])}
	tns = _tender_names_for_entity(procuring_entity)
	if tns is not None:
		if not tns:
			return []
		filters["tender"] = ("in", tns)
	return frappe.get_all(
		PC,
		filters=filters,
		fields=["name", "business_id", "contract_title", "tender", "status", "modified"],
		order_by="modified desc",
		limit=500,
	)


def contract_queue_report_columns(keys: list[str]) -> list[dict[str, Any]]:
	return [{"fieldname": k, "label": k.replace("_", " ").title(), "fieldtype": "Data", "width": 120} for k in keys]


def contract_queue_row_values(row: dict[str, Any], keys: list[str]) -> list[Any]:
	return [row.get(k) for k in keys]


def contract_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": "Procuring Entity",
			"fieldtype": "Link",
			"options": "Procuring Entity",
			"default": "",
		}
	]


def contracts_near_end_date_filter() -> list[dict[str, Any]]:
	return contract_entity_filter() + [
		{
			"fieldname": "days_ahead",
			"label": "Days Ahead",
			"fieldtype": "Int",
			"default": 90,
		}
	]
