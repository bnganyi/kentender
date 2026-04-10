# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""GOV-STORY-010: resolution issuance, follow-up creation, and completion with deliberation status events."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

from kentender_governance.services.deliberation_lifecycle_services import (
	_append_event,
	_ensure_not_cancelled,
	_ensure_not_locked,
	_session_doc,
)

DAI = "Deliberation Agenda Item"
RR = "Resolution Record"
FUA = "Follow Up Action"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _ensure_session_mutable(deliberation_session: str) -> Document:
	"""Cancelled and session-locked deliberation sessions cannot receive new resolutions or follow-ups."""
	doc = _session_doc(deliberation_session)
	_ensure_not_cancelled(doc)
	_ensure_not_locked(doc)
	return doc


def _agenda_belongs_to_session(agenda_item: str, deliberation_session: str) -> None:
	sess = frappe.db.get_value(DAI, agenda_item, "deliberation_session")
	if not sess or sess != deliberation_session:
		frappe.throw(_("Agenda Item must belong to the deliberation session."), frappe.ValidationError)


def _resolution_belongs_to_session(resolution_record: str, deliberation_session: str) -> None:
	sess = frappe.db.get_value(RR, resolution_record, "deliberation_session")
	if not sess or sess != deliberation_session:
		frappe.throw(_("Resolution Record must belong to the deliberation session."), frappe.ValidationError)


@frappe.whitelist()
def issue_resolution(
	deliberation_session: str,
	agenda_item: str,
	resolution_text: str,
	resolution_date: str | None = None,
	related_doctype: str | None = None,
	related_docname: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Create a **Resolution Record** with **effective_status** **Effective** and emit **ResolutionIssued**."""
	ds = _norm(deliberation_session)
	_ensure_session_mutable(ds)
	ai = _norm(agenda_item)
	if not ai or not frappe.db.exists(DAI, ai):
		frappe.throw(_("Agenda Item not found."), frappe.DoesNotExistError)
	_agenda_belongs_to_session(ai, ds)

	rd = getdate(resolution_date) if resolution_date else today()
	rdt = _norm(related_doctype)
	rdn = _norm(related_docname)
	if rdt or rdn:
		if not rdt or not rdn:
			frappe.throw(_("Related DocType and Related Document must both be set."), frappe.ValidationError)
	row = {
		"doctype": RR,
		"deliberation_session": ds,
		"agenda_item": ai,
		"resolution_text": resolution_text,
		"resolution_date": rd,
		"effective_status": "Effective",
	}
	if rdt:
		row["related_doctype"] = rdt
		row["related_docname"] = rdn
	doc = frappe.get_doc(row).insert(ignore_permissions=True)
	_append_event(
		ds,
		"ResolutionIssued",
		_("Resolution issued ({0}) for agenda item {1}.").format(doc.name[:14] + "...", ai),
		actor_user=actor_user,
	)
	return doc


@frappe.whitelist()
def create_follow_up_action(
	deliberation_session: str,
	resolution_record: str,
	action_title: str,
	assigned_to_user: str,
	due_date: str,
	action_description: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Create a **Follow Up Action** (status **Open**) and emit a governance status event."""
	ds = _norm(deliberation_session)
	_ensure_session_mutable(ds)
	rr = _norm(resolution_record)
	if not rr or not frappe.db.exists(RR, rr):
		frappe.throw(_("Resolution Record not found."), frappe.DoesNotExistError)
	_resolution_belongs_to_session(rr, ds)

	if not _norm(assigned_to_user) or not frappe.db.exists("User", assigned_to_user):
		frappe.throw(_("Assigned user not found."), frappe.ValidationError)

	dd = getdate(due_date)
	row = {
		"doctype": FUA,
		"deliberation_session": ds,
		"resolution_record": rr,
		"action_title": _norm(action_title),
		"assigned_to_user": assigned_to_user,
		"due_date": dd,
		"status": "Open",
	}
	if action_description is not None and _norm(action_description):
		row["action_description"] = action_description
	doc = frappe.get_doc(row).insert(ignore_permissions=True)
	_append_event(
		ds,
		"Other",
		_("Follow-up action created: {0} ({1}).").format(_norm(action_title), doc.name[:14] + "..."),
		actor_user=actor_user,
	)
	return doc


@frappe.whitelist()
def complete_follow_up_action(
	follow_up_action: str,
	completion_notes: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Set follow-up status to **Completed**, optional notes. Emits a status event. Idempotent if already completed."""
	name = _norm(follow_up_action)
	if not name or not frappe.db.exists(FUA, name):
		frappe.throw(_("Follow Up Action not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc(FUA, name)
	st = _norm(doc.status)
	if st == "Completed":
		return doc
	if st == "Cancelled":
		frappe.throw(_("Cannot complete a cancelled follow-up action."), frappe.ValidationError)

	ds = _norm(doc.deliberation_session)
	sdoc = _session_doc(ds)
	_ensure_not_cancelled(sdoc)

	doc.status = "Completed"
	if completion_notes is not None and _norm(completion_notes):
		doc.completion_notes = completion_notes
	doc.save(ignore_permissions=True)
	_append_event(
		ds,
		"Other",
		_("Follow-up action completed: {0}.").format(_norm(doc.action_title)),
		actor_user=actor_user,
	)
	return doc
