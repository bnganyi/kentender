# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-031: orchestration helpers for KenTender audit query / response lifecycle."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

AQ = "KenTender Audit Query"
AR = "KenTender Audit Response"


def mark_audit_query_status(audit_query_name: str, status: str) -> dict[str, Any]:
	"""Update **KenTender Audit Query** ``status`` with basic guardrails."""
	allowed = {"Draft", "Open", "Pending Response", "Answered", "Closed", "Cancelled"}
	if status not in allowed:
		frappe.throw(_("Invalid status."), frappe.ValidationError)
	doc = frappe.get_doc(AQ, audit_query_name)
	doc.status = status
	doc.save(ignore_permissions=True)
	return {"audit_query": doc.name, "status": doc.status}


def register_audit_response_submitted(audit_response_name: str) -> dict[str, Any]:
	"""Set response to **Submitted** and move parent query toward **Answered** when appropriate."""
	resp = frappe.get_doc(AR, audit_response_name)
	resp.status = "Submitted"
	resp.save(ignore_permissions=True)

	q = frappe.get_doc(AQ, resp.audit_query)
	if q.status in ("Open", "Pending Response"):
		q.status = "Answered"
		q.save(ignore_permissions=True)

	return {"audit_response": resp.name, "audit_query": q.name, "query_status": q.status}


@frappe.whitelist()
def mark_audit_query_status_api(audit_query_name: str | None = None, status: str | None = None):
	if not audit_query_name or not status:
		frappe.throw(_("audit_query_name and status are required."), frappe.ValidationError)
	return mark_audit_query_status(audit_query_name, status)


@frappe.whitelist()
def register_audit_response_submitted_api(audit_response_name: str | None = None):
	if not audit_response_name:
		frappe.throw(_("audit_response_name is required."), frappe.ValidationError)
	return register_audit_response_submitted(audit_response_name)
