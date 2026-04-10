# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""GOV-STORY-024: complete **Complaint Action** rows for a decision + integration signal."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_governance.services.complaint_service_utils import append_complaint_event, get_complaint_doc, norm, save_complaint

CD = "Complaint Decision"
CA = "Complaint Action"


def _emit_action_bridge(complaint: str, decision: str) -> None:
	from kentender.api.complaint_integration import emit_complaint_action_signal

	emit_complaint_action_signal(complaint=complaint, decision=decision, action="execute_complete")


def _decision_doc(name: str) -> Document:
	n = norm(name)
	if not n or not frappe.db.exists(CD, n):
		frappe.throw(_("Complaint Decision not found."), frappe.DoesNotExistError)
	return frappe.get_doc(CD, n)


@frappe.whitelist()
def execute_complaint_decision(decision: str, actor_user: str | None = None) -> Document:
	"""Mark non-terminal **Complaint Action** rows for this decision **Completed** and notify integration.

	Does not create new actions; preparers should add **Complaint Action** rows before calling.
	"""
	d = _decision_doc(decision)
	complaint = norm(d.complaint)
	if not complaint:
		frappe.throw(_("Complaint Decision has no complaint."), frappe.ValidationError)

	cdoc = get_complaint_doc(complaint)
	if int(cdoc.get("complaint_locked") or 0):
		frappe.throw(_("This complaint is locked."), frappe.ValidationError)
	if norm(d.status) != "Final":
		frappe.throw(_("Only a Final decision can be executed."), frappe.ValidationError)

	names = frappe.get_all(
		CA,
		filters={"decision": d.name, "status": ("not in", ("Completed", "Cancelled"))},
		pluck="name",
	) or []
	if not names:
		frappe.throw(
			_("No open Complaint Action rows exist for this decision. Add actions before executing."),
			frappe.ValidationError,
		)

	now = now_datetime()
	exec_user = norm(actor_user) or frappe.session.user
	for aname in names:
		a = frappe.get_doc(CA, aname)
		a.status = "Completed"
		if not a.executed_on:
			a.executed_on = now
		if exec_user and frappe.db.exists("User", exec_user):
			a.executed_by_user = exec_user
		a.save(ignore_permissions=True)

	d.decision_locked = 1
	d.save(ignore_permissions=True)

	cdoc.workflow_state = "Action"
	save_complaint(cdoc)

	_emit_action_bridge(complaint, d.name)
	append_complaint_event(
		complaint,
		"ActionCompleted",
		_("Complaint decision executed; actions completed."),
		actor_user=actor_user or exec_user,
	)
	return d
