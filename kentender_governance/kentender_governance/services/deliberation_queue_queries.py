# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for deliberation desk queues and script reports (GOV-STORY-011)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

DS = "Deliberation Session"
FUA = "Follow Up Action"
RR = "Resolution Record"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _pe_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def _session_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	"""Return session names for filter, or None if no entity filter."""
	ent = _norm(procuring_entity)
	if not ent:
		return None
	return frappe.get_all(DS, filters={"procuring_entity": ent}, pluck="name") or []


def get_scheduled_deliberations(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Sessions in **Scheduled** status (desk queue)."""
	filters: dict[str, Any] = {"status": "Scheduled"}
	filters.update(_pe_filter(procuring_entity))
	return frappe.get_all(
		DS,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"session_title",
			"session_type",
			"procuring_entity",
			"status",
			"scheduled_datetime",
			"chair_user",
			"modified",
		],
		order_by="scheduled_datetime asc",
		limit=limit,
	)


def get_open_follow_up_actions(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Follow-up actions not completed or cancelled."""
	filters: dict[str, Any] = {"status": ("in", ("Open", "In Progress"))}
	sns = _session_names_for_entity(procuring_entity)
	if sns is not None:
		if not sns:
			return []
		filters["deliberation_session"] = ("in", sns)
	return frappe.get_all(
		FUA,
		filters=filters,
		fields=[
			"name",
			"deliberation_session",
			"resolution_record",
			"action_title",
			"assigned_to_user",
			"due_date",
			"status",
			"modified",
		],
		order_by="due_date asc",
		limit=limit,
	)


def get_resolution_register_rows(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Issued resolutions (**Effective** or **Superseded**)."""
	filters: dict[str, Any] = {"effective_status": ("in", ("Effective", "Superseded"))}
	sns = _session_names_for_entity(procuring_entity)
	if sns is not None:
		if not sns:
			return []
		filters["deliberation_session"] = ("in", sns)
	return frappe.get_all(
		RR,
		filters=filters,
		fields=[
			"name",
			"deliberation_session",
			"agenda_item",
			"resolution_date",
			"effective_status",
			"related_doctype",
			"related_docname",
			"modified",
		],
		order_by="resolution_date desc",
		limit=limit,
	)


def get_deliberations_by_linked_object(
	*,
	linked_doctype: str,
	linked_docname: str,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Deliberation sessions linked to a document via dynamic link."""
	ldt = _norm(linked_doctype)
	ldn = _norm(linked_docname)
	if not ldt or not ldn:
		return []
	filters: dict[str, Any] = {"linked_doctype": ldt, "linked_docname": ldn}
	filters.update(_pe_filter(procuring_entity))
	return frappe.get_all(
		DS,
		filters=filters,
		fields=[
			"name",
			"business_id",
			"session_title",
			"procuring_entity",
			"status",
			"linked_doctype",
			"linked_docname",
			"scheduled_datetime",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


# --- Script report helpers ---


def deliberation_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]


def scheduled_deliberations_report_columns() -> list[str]:
	return [
		_("Session") + ":Link/Deliberation Session:160",
		_("Business ID") + ":Data:130",
		_("Title") + ":Data:180",
		_("Type") + ":Data:100",
		_("Entity") + ":Link/Procuring Entity:140",
		_("Status") + ":Data:100",
		_("Scheduled") + ":Datetime:150",
		_("Chair") + ":Link/User:140",
		_("Modified") + ":Datetime:150",
	]


def scheduled_deliberation_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("session_title"),
		r.get("session_type"),
		r.get("procuring_entity"),
		r.get("status"),
		r.get("scheduled_datetime"),
		r.get("chair_user"),
		r.get("modified"),
	]


def open_follow_up_actions_report_columns() -> list[str]:
	return [
		_("Follow Up") + ":Link/Follow Up Action:160",
		_("Session") + ":Link/Deliberation Session:160",
		_("Resolution") + ":Link/Resolution Record:160",
		_("Title") + ":Data:180",
		_("Assigned To") + ":Link/User:140",
		_("Due") + ":Date:120",
		_("Status") + ":Data:100",
		_("Modified") + ":Datetime:150",
	]


def open_follow_up_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("deliberation_session"),
		r.get("resolution_record"),
		r.get("action_title"),
		r.get("assigned_to_user"),
		r.get("due_date"),
		r.get("status"),
		r.get("modified"),
	]


def resolution_register_report_columns() -> list[str]:
	return [
		_("Resolution") + ":Link/Resolution Record:160",
		_("Session") + ":Link/Deliberation Session:160",
		_("Agenda Item") + ":Link/Deliberation Agenda Item:160",
		_("Resolution Date") + ":Date:120",
		_("Effective Status") + ":Data:120",
		_("Related DocType") + ":Data:120",
		_("Related Document") + ":Data:160",
		_("Modified") + ":Datetime:150",
	]


def resolution_register_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("deliberation_session"),
		r.get("agenda_item"),
		r.get("resolution_date"),
		r.get("effective_status"),
		r.get("related_doctype"),
		r.get("related_docname"),
		r.get("modified"),
	]


def deliberations_linked_report_columns() -> list[str]:
	return [
		_("Session") + ":Link/Deliberation Session:160",
		_("Business ID") + ":Data:130",
		_("Title") + ":Data:180",
		_("Entity") + ":Link/Procuring Entity:140",
		_("Status") + ":Data:100",
		_("Linked DocType") + ":Data:120",
		_("Linked Document") + ":Data:160",
		_("Scheduled") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def deliberations_linked_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("session_title"),
		r.get("procuring_entity"),
		r.get("status"),
		r.get("linked_doctype"),
		r.get("linked_docname"),
		r.get("scheduled_datetime"),
		r.get("modified"),
	]


def deliberations_linked_extra_filters() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "linked_doctype",
			"label": _("Linked DocType"),
			"fieldtype": "Link",
			"options": "DocType",
			"reqd": 1,
		},
		{
			"fieldname": "linked_docname",
			"label": _("Linked Document"),
			"fieldtype": "Dynamic Link",
			"options": "linked_doctype",
			"reqd": 1,
		},
	]
