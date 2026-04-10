# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for requisition desk queues and script reports (PROC-STORY-010).

These functions return lightweight row dicts for reporting; they do not mutate data.

Row scoping follows Roles and Permissions Guidance §§5–7: entity scope from
``merge_entity_scope_filters`` plus role-based filters (HOD / finance / procurement
/ auditor / central operators).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender.permissions.registry import UAT_ROLE
from kentender.services.entity_scope_service import is_central_entity_scope_user
from kentender.services.permission_query_service import merge_entity_scope_filters

PR = "Purchase Requisition"

_LIST_FIELDS = [
	"name",
	"title",
	"workflow_state",
	"status",
	"planning_status",
	"requested_amount",
	"procuring_entity",
	"requested_by_user",
	"modified",
]


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _entity_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def _pending_base_filters() -> dict[str, Any]:
	return {
		"workflow_state": [
			"in",
			["Pending HOD Approval", "Pending Finance Approval"],
		],
		"status": ["!=", "Cancelled"],
	}


def _planning_base_filters() -> dict[str, Any]:
	return {
		"planning_status": ["in", ["Unplanned", "Partially Planned"]],
		"status": ["!=", "Cancelled"],
		"workflow_state": ["not in", ["Cancelled", "Rejected"]],
	}


def _roles(user: str | None) -> frozenset[str]:
	u = _norm(user) or _norm(frappe.session.user)
	return frozenset(frappe.get_roles(u))


def _queue_roles_present(roles: frozenset[str]) -> bool:
	"""Roles that participate in approval-queue row logic (excludes pure requisitioner)."""
	return bool(
		roles
		& {
			UAT_ROLE.HOD.value,
			UAT_ROLE.FINANCE.value,
			UAT_ROLE.PROCUREMENT.value,
			UAT_ROLE.AUDITOR.value,
		}
	)


def _planning_roles_present(roles: frozenset[str]) -> bool:
	return bool(
		roles
		& {
			UAT_ROLE.PROCUREMENT.value,
			UAT_ROLE.FINANCE.value,
			UAT_ROLE.AUDITOR.value,
		}
	)


def get_my_requisitions(
	*,
	user: str | None = None,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Rows where ``requested_by_user`` matches *user* (default: current session user)."""
	u = _norm(user) or _norm(frappe.session.user) or "Guest"
	filters: dict[str, Any] = {"requested_by_user": u}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		PR,
		filters=filters,
		fields=_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_pending_requisition_approvals(
	*,
	user: str | None = None,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Rows awaiting approval action, scoped by role and procuring entity (Guidance §5)."""
	u = _norm(user) or _norm(frappe.session.user) or "Guest"
	roles = _roles(u)
	filters: dict[str, Any] = dict(_pending_base_filters())
	filters = merge_entity_scope_filters(
		filters,
		u,
		active_entity=_norm(procuring_entity) or None,
	)

	if is_central_entity_scope_user(u) or UAT_ROLE.AUDITOR.value in roles:
		return frappe.get_all(
			PR,
			filters=filters,
			fields=_LIST_FIELDS,
			order_by="modified desc",
			limit=limit,
		)

	if UAT_ROLE.REQUISITIONER.value in roles and not _queue_roles_present(roles):
		return []

	if UAT_ROLE.PROCUREMENT.value in roles:
		return frappe.get_all(
			PR,
			filters=filters,
			fields=_LIST_FIELDS,
			order_by="modified desc",
			limit=limit,
		)

	or_clauses: list[list[str]] = []
	if UAT_ROLE.HOD.value in roles:
		or_clauses.append(["hod_user", "=", u])
	if UAT_ROLE.FINANCE.value in roles:
		or_clauses.append(["finance_reviewer_user", "=", u])

	if not or_clauses:
		return []

	if len(or_clauses) == 1:
		filters[or_clauses[0][0]] = or_clauses[0][2]
		return frappe.get_all(
			PR,
			filters=filters,
			fields=_LIST_FIELDS,
			order_by="modified desc",
			limit=limit,
		)

	return frappe.get_all(
		PR,
		filters=filters,
		or_filters=or_clauses,
		fields=_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_planning_ready_requisitions(
	*,
	user: str | None = None,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Planning-coverage queue; restricted to procurement/finance/auditor/central (Guidance §4)."""
	u = _norm(user) or _norm(frappe.session.user) or "Guest"
	roles = _roles(u)

	if not is_central_entity_scope_user(u):
		if UAT_ROLE.REQUISITIONER.value in roles and not _planning_roles_present(roles):
			return []
		if UAT_ROLE.HOD.value in roles and not _planning_roles_present(roles):
			return []
		if not _planning_roles_present(roles):
			return []

	filters: dict[str, Any] = dict(_planning_base_filters())
	filters = merge_entity_scope_filters(
		filters,
		u,
		active_entity=_norm(procuring_entity) or None,
	)
	return frappe.get_all(
		PR,
		filters=filters,
		fields=_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def requisition_report_columns() -> list[str]:
	"""Column definitions shared by PROC-010 script reports."""
	return [
		_("Requisition") + ":Link/Purchase Requisition:160",
		_("Reference") + ":Data:120",
		_("Title") + ":Data:160",
		_("Stage") + ":Data:120",
		_("Overall Status") + ":Data:100",
		_("Planning Status") + ":Data:120",
		_("Requested Amount") + ":Currency:120",
		_("Procuring Entity") + ":Link/Procuring Entity:160",
		_("Requested By") + ":Link/User:140",
		_("Modified") + ":Datetime:150",
	]


def requisition_report_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("name"),
		r.get("title"),
		r.get("workflow_state"),
		r.get("status"),
		r.get("planning_status"),
		r.get("requested_amount"),
		r.get("procuring_entity"),
		r.get("requested_by_user"),
		r.get("modified"),
	]


def requisition_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]
