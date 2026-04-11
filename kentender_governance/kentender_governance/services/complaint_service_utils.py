# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Shared helpers for complaint service modules (GOV-021+)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.workflow_engine.safeguards import workflow_mutation_context

C = "Complaint"
CSE = "Complaint Status Event"


def norm(s: str | None) -> str:
	return (s or "").strip()


def get_complaint_doc(complaint: str) -> Document:
	name = norm(complaint)
	if not name or not frappe.db.exists(C, name):
		frappe.throw(_("Complaint not found."), frappe.DoesNotExistError)
	return frappe.get_doc(C, name)


def ensure_complaint_not_locked(doc: Document) -> None:
	if int(doc.get("complaint_locked") or 0):
		frappe.throw(_("This complaint is locked."), frappe.ValidationError)


def append_complaint_event(
	complaint: str,
	event_type: str,
	summary: str,
	*,
	actor_user: str | None = None,
) -> None:
	frappe.get_doc(
		{
			"doctype": CSE,
			"complaint": complaint,
			"event_type": event_type,
			"event_datetime": now_datetime(),
			"actor_user": actor_user or frappe.session.user,
			"summary": summary,
		}
	).insert(ignore_permissions=True)


def save_complaint(doc: Document) -> Document:
	"""Persist complaint; workflow_state is approval-controlled (WF-002 / WF-015)."""
	with workflow_mutation_context():
		doc.save(ignore_permissions=True)
	return doc
