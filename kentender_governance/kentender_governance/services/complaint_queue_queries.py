# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-side helpers for complaint desk queues and script reports (GOV-STORY-025)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

C = "Complaint"
CD = "Complaint Decision"
AR = "Appeal Record"


def get_complaints_awaiting_admissibility(*, limit: int = 500) -> list[dict[str, Any]]:
	"""**Pending** admissibility while still in intake queue."""
	return frappe.get_all(
		C,
		filters={"admissibility_status": "Pending", "status": "Submitted"},
		fields=[
			"name",
			"business_id",
			"complaint_title",
			"status",
			"workflow_state",
			"admissibility_status",
			"submission_datetime",
			"modified",
		],
		order_by="submission_datetime asc",
		limit=limit,
	)


def get_complaints_under_review(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Complaints in active review (post-admissibility)."""
	return frappe.get_all(
		C,
		filters={"status": "Under Review"},
		fields=[
			"name",
			"business_id",
			"complaint_title",
			"workflow_state",
			"admissibility_status",
			"submission_datetime",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_complaints_with_active_hold(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Complaints with **Active** procurement hold."""
	return frappe.get_all(
		C,
		filters={"hold_status": "Active"},
		fields=[
			"name",
			"business_id",
			"complaint_title",
			"hold_status",
			"affects_award_process",
			"affects_contract_execution",
			"hold_scope",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_complaint_decisions_register(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Issued (**Final**) complaint decisions."""
	return frappe.get_all(
		CD,
		filters={"status": "Final"},
		fields=[
			"name",
			"business_id",
			"complaint",
			"decision_result",
			"decision_datetime",
			"decided_by_user",
			"decision_locked",
			"modified",
		],
		order_by="decision_datetime desc",
		limit=limit,
	)


def get_complaint_appeals_register(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Appeal records (any status)."""
	return frappe.get_all(
		AR,
		filters={},
		fields=[
			"name",
			"complaint",
			"complaint_decision",
			"status",
			"appeal_submitted_by",
			"appeal_summary",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


# --- Script report helpers ---


def complaints_awaiting_admissibility_columns() -> list[str]:
	return [
		_("Complaint") + ":Link/Complaint:160",
		_("Business ID") + ":Data:130",
		_("Title") + ":Data:180",
		_("Status") + ":Data:100",
		_("Workflow") + ":Data:120",
		_("Admissibility") + ":Data:120",
		_("Submitted") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def complaints_awaiting_admissibility_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("complaint_title"),
		r.get("status"),
		r.get("workflow_state"),
		r.get("admissibility_status"),
		r.get("submission_datetime"),
		r.get("modified"),
	]


def complaints_under_review_columns() -> list[str]:
	return [
		_("Complaint") + ":Link/Complaint:160",
		_("Business ID") + ":Data:130",
		_("Title") + ":Data:180",
		_("Workflow") + ":Data:120",
		_("Admissibility") + ":Data:120",
		_("Submitted") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def complaints_under_review_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("complaint_title"),
		r.get("workflow_state"),
		r.get("admissibility_status"),
		r.get("submission_datetime"),
		r.get("modified"),
	]


def complaints_active_hold_columns() -> list[str]:
	return [
		_("Complaint") + ":Link/Complaint:160",
		_("Business ID") + ":Data:130",
		_("Title") + ":Data:180",
		_("Hold") + ":Data:100",
		_("Affects Award") + ":Check:90",
		_("Affects Contract") + ":Check:110",
		_("Hold Scope") + ":Data:160",
		_("Modified") + ":Datetime:150",
	]


def complaints_active_hold_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("complaint_title"),
		r.get("hold_status"),
		r.get("affects_award_process"),
		r.get("affects_contract_execution"),
		r.get("hold_scope"),
		r.get("modified"),
	]


def complaint_decisions_report_columns() -> list[str]:
	return [
		_("Decision") + ":Link/Complaint Decision:160",
		_("Business ID") + ":Data:130",
		_("Complaint") + ":Link/Complaint:160",
		_("Result") + ":Data:120",
		_("Decision Datetime") + ":Datetime:150",
		_("Decided By") + ":Link/User:140",
		_("Locked") + ":Check:70",
		_("Modified") + ":Datetime:150",
	]


def complaint_decisions_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("complaint"),
		r.get("decision_result"),
		r.get("decision_datetime"),
		r.get("decided_by_user"),
		r.get("decision_locked"),
		r.get("modified"),
	]


def complaint_appeals_report_columns() -> list[str]:
	return [
		_("Appeal") + ":Link/Appeal Record:160",
		_("Complaint") + ":Link/Complaint:160",
		_("Decision") + ":Link/Complaint Decision:160",
		_("Status") + ":Data:100",
		_("Submitted By") + ":Link/User:140",
		_("Summary") + ":Data:200",
		_("Modified") + ":Datetime:150",
	]


def complaint_appeals_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("complaint"),
		r.get("complaint_decision"),
		r.get("status"),
		r.get("appeal_submitted_by"),
		r.get("appeal_summary"),
		r.get("modified"),
	]
