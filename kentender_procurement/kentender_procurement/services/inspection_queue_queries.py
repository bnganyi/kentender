# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for inspection desk queues and script reports (PROC-STORY-116)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

AR = "Acceptance Record"
IR = "Inspection Record"
NC = "Non Conformance Record"
PC = "Procurement Contract"
RR = "Reinspection Record"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _contract_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	ent = _norm(procuring_entity)
	if not ent:
		return None
	names = frappe.get_all(PC, filters={"procuring_entity": ent}, pluck="name") or []
	return names


def _ir_entity_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def get_scheduled_inspections(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Inspections with a scheduled time that are not finished (desk queue)."""
	filters: dict[str, Any] = {
		"status": ("not in", ("Completed", "Cancelled")),
		"scheduled_inspection_datetime": ("is", "set"),
	}
	filters.update(_ir_entity_filter(procuring_entity))
	return frappe.get_all(
		IR,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"contract",
			"inspection_title",
			"inspection_scope_type",
			"procuring_entity",
			"status",
			"workflow_state",
			"scheduled_inspection_datetime",
			"inspection_result",
			"modified",
		],
		order_by="scheduled_inspection_datetime asc",
		limit=limit,
	)


def get_inspections_awaiting_acceptance(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Completed inspections with no **Acceptance Record** linked yet."""
	filters: dict[str, Any] = {
		"status": "Completed",
		"acceptance_record": ("is", "not set"),
	}
	filters.update(_ir_entity_filter(procuring_entity))
	return frappe.get_all(
		IR,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"contract",
			"inspection_title",
			"procuring_entity",
			"inspection_result",
			"acceptance_status",
			"actual_inspection_datetime",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_non_conformance_register_rows(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Open / in-progress non-conformances (register view)."""
	filters: dict[str, Any] = {"status": ("in", ("Open", "In Progress"))}
	cns = _contract_names_for_entity(procuring_entity)
	if cns is not None:
		if not cns:
			return []
		filters["contract"] = ("in", cns)
	return frappe.get_all(
		NC,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"inspection_record",
			"contract",
			"issue_type",
			"issue_title",
			"severity",
			"status",
			"corrective_action_due_date",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_reinspections_due_rows(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Reinspection records not yet completed."""
	filters: dict[str, Any] = {"status": ("in", ("Planned", "In Progress"))}
	cns = _contract_names_for_entity(procuring_entity)
	if cns is not None:
		if not cns:
			return []
		filters["contract"] = ("in", cns)
	return frappe.get_all(
		RR,
		filters=filters,
		fields=[
			"name",
			"inspection_record",
			"contract",
			"trigger_reason",
			"status",
			"scheduled_datetime",
			"linked_followup_inspection",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_partial_or_rejected_acceptance_rows(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Acceptance records with **Conditional** or **Rejected** decisions (summary queue)."""
	filters: dict[str, Any] = {
		"acceptance_decision": ("in", ("Conditional", "Rejected")),
		"status": ("not in", ("Cancelled", "Superseded")),
	}
	cns = _contract_names_for_entity(procuring_entity)
	if cns is not None:
		if not cns:
			return []
		filters["contract"] = ("in", cns)
	return frappe.get_all(
		AR,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"inspection_record",
			"contract",
			"acceptance_decision",
			"status",
			"workflow_state",
			"decision_datetime",
			"payment_eligibility_signal_status",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


# --- Script report helpers ---


def inspection_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]


def scheduled_inspections_report_columns() -> list[str]:
	return [
		_("Inspection") + ":Link/Inspection Record:160",
		_("Business ID") + ":Data:130",
		_("Contract") + ":Link/Procurement Contract:160",
		_("Title") + ":Data:180",
		_("Scope") + ":Data:120",
		_("Entity") + ":Link/Procuring Entity:140",
		_("Status") + ":Data:100",
		_("Workflow") + ":Data:100",
		_("Scheduled") + ":Datetime:150",
		_("Result") + ":Data:110",
		_("Modified") + ":Datetime:150",
	]


def scheduled_inspection_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("contract"),
		r.get("inspection_title"),
		r.get("inspection_scope_type"),
		r.get("procuring_entity"),
		r.get("status"),
		r.get("workflow_state"),
		r.get("scheduled_inspection_datetime"),
		r.get("inspection_result"),
		r.get("modified"),
	]


def awaiting_acceptance_report_columns() -> list[str]:
	return [
		_("Inspection") + ":Link/Inspection Record:160",
		_("Business ID") + ":Data:130",
		_("Contract") + ":Link/Procurement Contract:160",
		_("Title") + ":Data:180",
		_("Entity") + ":Link/Procuring Entity:140",
		_("Result") + ":Data:110",
		_("Acceptance Status") + ":Data:120",
		_("Actual Inspection") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def awaiting_acceptance_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("contract"),
		r.get("inspection_title"),
		r.get("procuring_entity"),
		r.get("inspection_result"),
		r.get("acceptance_status"),
		r.get("actual_inspection_datetime"),
		r.get("modified"),
	]


def non_conformance_register_report_columns() -> list[str]:
	return [
		_("Non Conformance") + ":Link/Non Conformance Record:180",
		_("Business ID") + ":Data:130",
		_("Inspection") + ":Link/Inspection Record:160",
		_("Contract") + ":Link/Procurement Contract:160",
		_("Type") + ":Data:110",
		_("Title") + ":Data:160",
		_("Severity") + ":Data:80",
		_("Status") + ":Data:100",
		_("Due") + ":Date:100",
		_("Modified") + ":Datetime:150",
	]


def non_conformance_register_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("inspection_record"),
		r.get("contract"),
		r.get("issue_type"),
		r.get("issue_title"),
		r.get("severity"),
		r.get("status"),
		r.get("corrective_action_due_date"),
		r.get("modified"),
	]


def reinspections_due_report_columns() -> list[str]:
	return [
		_("Reinspection") + ":Link/Reinspection Record:180",
		_("Inspection") + ":Link/Inspection Record:160",
		_("Contract") + ":Link/Procurement Contract:160",
		_("Trigger") + ":Data:120",
		_("Status") + ":Data:100",
		_("Scheduled") + ":Datetime:150",
		_("Follow-up Inspection") + ":Link/Inspection Record:160",
		_("Modified") + ":Datetime:150",
	]


def reinspections_due_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("inspection_record"),
		r.get("contract"),
		r.get("trigger_reason"),
		r.get("status"),
		r.get("scheduled_datetime"),
		r.get("linked_followup_inspection"),
		r.get("modified"),
	]


def partial_rejection_report_columns() -> list[str]:
	return [
		_("Acceptance") + ":Link/Acceptance Record:180",
		_("Business ID") + ":Data:130",
		_("Inspection") + ":Link/Inspection Record:160",
		_("Contract") + ":Link/Procurement Contract:160",
		_("Decision") + ":Data:100",
		_("Status") + ":Data:100",
		_("Workflow") + ":Data:110",
		_("Decision Datetime") + ":Datetime:150",
		_("Payment Signal") + ":Data:120",
		_("Modified") + ":Datetime:150",
	]


def partial_rejection_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("inspection_record"),
		r.get("contract"),
		r.get("acceptance_decision"),
		r.get("status"),
		r.get("workflow_state"),
		r.get("decision_datetime"),
		r.get("payment_eligibility_signal_status"),
		r.get("modified"),
	]
