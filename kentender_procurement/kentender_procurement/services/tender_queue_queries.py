# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for tender desk queues and script reports (PROC-STORY-035).

These functions return lightweight row dicts for reporting; they do not mutate data.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, cint, now_datetime

TENDER = "Tender"
TENDER_AMENDMENT = "Tender Amendment"
TENDER_CLARIFICATION = "Tender Clarification"

WS_DRAFT = "Draft"
WS_SUBMITTED = "Submitted"
WS_UNDER_REVIEW = "Under Review"
WS_PUBLISHED = "Published"

ST_CANCELLED = "Cancelled"
SUB_OPEN = "Open"

_TENDER_LIST_FIELDS = [
	"name",
	"business_id",
	"title",
	"workflow_state",
	"status",
	"procuring_entity",
	"approval_status",
	"submission_status",
	"submission_deadline",
	"modified",
]

_AMEND_FIELDS = [
	"name",
	"business_id",
	"tender",
	"amendment_no",
	"amendment_type",
	"status",
	"effective_datetime",
	"modified",
]

_CLAR_FIELDS = [
	"name",
	"business_id",
	"tender",
	"supplier",
	"status",
	"question_datetime",
	"modified",
]


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _entity_filter(procuring_entity: str | None) -> dict[str, Any]:
	ent = _norm(procuring_entity)
	if not ent:
		return {}
	return {"procuring_entity": ent}


def _tender_names_for_entity(procuring_entity: str | None) -> list[str] | None:
	ent = _norm(procuring_entity)
	if not ent:
		return None
	names = frappe.get_all(TENDER, filters={"procuring_entity": ent}, pluck="name") or []
	return names


def get_draft_tenders(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Tenders in **Draft** workflow (excludes cancelled tender status)."""
	filters: dict[str, Any] = {
		"workflow_state": WS_DRAFT,
		"status": ("!=", ST_CANCELLED),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		TENDER,
		filters=filters,
		fields=_TENDER_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_tenders_under_review(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Tenders **Submitted** or **Under Review**."""
	filters: dict[str, Any] = {
		"workflow_state": ("in", [WS_SUBMITTED, WS_UNDER_REVIEW]),
		"status": ("!=", ST_CANCELLED),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		TENDER,
		filters=filters,
		fields=_TENDER_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_published_tenders(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Tenders with workflow **Published**."""
	filters: dict[str, Any] = {
		"workflow_state": WS_PUBLISHED,
		"status": ("!=", ST_CANCELLED),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		TENDER,
		filters=filters,
		fields=_TENDER_LIST_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_tenders_closing_soon(
	*,
	procuring_entity: str | None = None,
	days_ahead: int = 14,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Published tenders with submission **Open** and deadline within the next *days_ahead* days."""
	n = max(1, cint(days_ahead) or 14)
	now = now_datetime()
	end = add_days(now, n)
	filters: dict[str, Any] = {
		"workflow_state": WS_PUBLISHED,
		"submission_status": SUB_OPEN,
		"submission_deadline": ("between", [now, end]),
		"status": ("!=", ST_CANCELLED),
	}
	filters.update(_entity_filter(procuring_entity))
	return frappe.get_all(
		TENDER,
		filters=filters,
		fields=_TENDER_LIST_FIELDS,
		order_by="submission_deadline asc",
		limit=limit,
	)


def get_tender_amendments_for_queue(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Tender Amendment rows; optional procuring entity via parent Tender."""
	tn = _tender_names_for_entity(procuring_entity)
	if tn is not None and not tn:
		return []
	filters: dict[str, Any] = {}
	if tn is not None:
		filters["tender"] = ("in", tn)
	return frappe.get_all(
		TENDER_AMENDMENT,
		filters=filters,
		fields=_AMEND_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def get_tender_clarifications_for_queue(
	*,
	procuring_entity: str | None = None,
	limit: int = 500,
) -> list[dict[str, Any]]:
	"""Tender Clarification rows excluding terminal **Closed** / **Withdrawn** (UAT queue)."""
	tn = _tender_names_for_entity(procuring_entity)
	if tn is not None and not tn:
		return []
	filters: dict[str, Any] = {"status": ("not in", ["Closed", "Withdrawn"])}
	if tn is not None:
		filters["tender"] = ("in", tn)
	return frappe.get_all(
		TENDER_CLARIFICATION,
		filters=filters,
		fields=_CLAR_FIELDS,
		order_by="modified desc",
		limit=limit,
	)


def tender_queue_report_columns() -> list[str]:
	return [
		_("Tender") + ":Link/Tender:160",
		_("Business ID") + ":Data:140",
		_("Title") + ":Data:200",
		_("Workflow Stage") + ":Data:120",
		_("Status") + ":Data:100",
		_("Procuring Entity") + ":Link/Procuring Entity:160",
		_("Approval Status") + ":Data:120",
		_("Submission Status") + ":Data:130",
		_("Submission Deadline") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def tender_queue_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("title"),
		r.get("workflow_state"),
		r.get("status"),
		r.get("procuring_entity"),
		r.get("approval_status"),
		r.get("submission_status"),
		r.get("submission_deadline"),
		r.get("modified"),
	]


def tender_amendment_queue_columns() -> list[str]:
	return [
		_("Amendment") + ":Link/Tender Amendment:180",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Amendment No") + ":Int:100",
		_("Type") + ":Data:120",
		_("Status") + ":Data:100",
		_("Effective") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def tender_amendment_queue_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("tender"),
		r.get("amendment_no"),
		r.get("amendment_type"),
		r.get("status"),
		r.get("effective_datetime"),
		r.get("modified"),
	]


def tender_clarification_queue_columns() -> list[str]:
	return [
		_("Clarification") + ":Link/Tender Clarification:180",
		_("Business ID") + ":Data:140",
		_("Tender") + ":Link/Tender:160",
		_("Supplier") + ":Data:120",
		_("Status") + ":Data:110",
		_("Question Time") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def tender_clarification_queue_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("tender"),
		r.get("supplier"),
		r.get("status"),
		r.get("question_datetime"),
		r.get("modified"),
	]


def tender_report_entity_filter() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "procuring_entity",
			"label": _("Procuring Entity"),
			"fieldtype": "Link",
			"options": "Procuring Entity",
		},
	]


def tender_closing_soon_extra_filters() -> list[dict[str, Any]]:
	return [
		{
			"fieldname": "days_ahead",
			"label": _("Days Ahead"),
			"fieldtype": "Int",
			"default": 14,
		},
	]


__all__ = [
	"get_draft_tenders",
	"get_published_tenders",
	"get_tender_amendments_for_queue",
	"get_tender_clarifications_for_queue",
	"get_tenders_closing_soon",
	"get_tenders_under_review",
	"tender_amendment_queue_columns",
	"tender_amendment_queue_row_values",
	"tender_clarification_queue_columns",
	"tender_clarification_queue_row_values",
	"tender_closing_soon_extra_filters",
	"tender_queue_report_columns",
	"tender_queue_row_values",
	"tender_report_entity_filter",
]
