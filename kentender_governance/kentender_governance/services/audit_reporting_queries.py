# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-032: audit desk queues and script report helpers."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

AQ = "KenTender Audit Query"
AR = "KenTender Audit Response"
AA = "KenTender Audit Action"


def get_open_audit_queries(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Queries awaiting closure (not Answered / Closed / Cancelled)."""
	return frappe.get_all(
		AQ,
		filters={"status": ["in", ["Draft", "Open", "Pending Response"]]},
		fields=[
			"name",
			"business_id",
			"query_title",
			"status",
			"raised_on",
			"response_due_date",
			"modified",
		],
		order_by="response_due_date asc",
		limit=limit,
	)


def get_draft_audit_responses(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Responses still in **Draft**."""
	return frappe.get_all(
		AR,
		filters={"status": "Draft"},
		fields=[
			"name",
			"business_id",
			"audit_query",
			"audit_finding",
			"responded_on",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


def get_open_audit_actions(*, limit: int = 500) -> list[dict[str, Any]]:
	"""Corrective actions not **Completed** / **Cancelled**."""
	return frappe.get_all(
		AA,
		filters={"status": ["in", ["Open", "In Progress", "Overdue"]]},
		fields=[
			"name",
			"business_id",
			"audit_query",
			"audit_finding",
			"action_title",
			"due_date",
			"status",
			"modified",
		],
		order_by="due_date asc",
		limit=limit,
	)


def open_audit_queries_columns() -> list[str]:
	return [
		_("KenTender Audit Query") + ":Link/KenTender Audit Query:180",
		_("Business ID") + ":Data:140",
		_("Query Title") + ":Data:200",
		_("Status") + ":Data:120",
		_("Raised On") + ":Date:120",
		_("Response Due") + ":Date:120",
		_("Modified") + ":Datetime:150",
	]


def open_audit_queries_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("query_title"),
		r.get("status"),
		r.get("raised_on"),
		r.get("response_due_date"),
		r.get("modified"),
	]


def draft_audit_responses_columns() -> list[str]:
	return [
		_("KenTender Audit Response") + ":Link/KenTender Audit Response:200",
		_("Business ID") + ":Data:140",
		_("Audit Query") + ":Link/KenTender Audit Query:160",
		_("Audit Finding") + ":Link/KenTender Audit Finding:160",
		_("Responded On") + ":Datetime:150",
		_("Modified") + ":Datetime:150",
	]


def draft_audit_responses_row_values(r: dict[str, Any]) -> list[Any]:
	return [
		r.get("name"),
		r.get("business_id"),
		r.get("audit_query"),
		r.get("audit_finding"),
		r.get("responded_on"),
		r.get("modified"),
	]
