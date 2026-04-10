# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""GOV-STORY-009: deliberation session lifecycle (schedule, start, complete, lock) + status events."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

DS = "Deliberation Session"
DSE = "Deliberation Status Event"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _session_doc(deliberation_session: str) -> Document:
	name = _norm(deliberation_session)
	if not name or not frappe.db.exists(DS, name):
		frappe.throw(_("Deliberation Session not found."), frappe.DoesNotExistError)
	return frappe.get_doc(DS, name)


def _ensure_not_cancelled(doc: Document) -> None:
	if _norm(doc.status) == "Cancelled":
		frappe.throw(_("Cannot change a cancelled deliberation session."), frappe.ValidationError)


def _ensure_not_locked(doc: Document) -> None:
	if int(doc.get("session_locked") or 0):
		frappe.throw(_("This deliberation session is locked."), frappe.ValidationError)


def _append_event(
	deliberation_session: str,
	event_type: str,
	summary: str,
	*,
	actor_user: str | None = None,
) -> None:
	frappe.get_doc(
		{
			"doctype": DSE,
			"deliberation_session": deliberation_session,
			"event_type": event_type,
			"event_datetime": now_datetime(),
			"actor_user": actor_user or frappe.session.user,
			"summary": summary,
		}
	).insert(ignore_permissions=True)


def _save_session(doc: Document) -> Document:
	doc.save(ignore_permissions=True)
	return doc


@frappe.whitelist()
def schedule_deliberation_session(
	deliberation_session: str,
	scheduled_datetime: str | None = None,
	actor_user: str | None = None,
) -> Document:
	"""Move session to **Scheduled** (from Draft or reschedule while Scheduled). Emits **Scheduled** status event."""
	doc = _session_doc(deliberation_session)
	_ensure_not_cancelled(doc)
	_ensure_not_locked(doc)
	st = _norm(doc.status)
	if st not in ("Draft", "Scheduled"):
		frappe.throw(
			_("Only Draft or Scheduled sessions can be scheduled (current status: {0}).").format(st),
			frappe.ValidationError,
		)
	if scheduled_datetime:
		doc.scheduled_datetime = get_datetime(scheduled_datetime)
	doc.status = "Scheduled"
	_save_session(doc)
	_append_event(
		doc.name,
		"Scheduled",
		_("Session scheduled."),
		actor_user=actor_user,
	)
	return doc


@frappe.whitelist()
def start_deliberation_session(deliberation_session: str, actor_user: str | None = None) -> Document:
	"""**Scheduled** → **In Progress**. Sets **actual_start_datetime** if empty. Emits **Started**."""
	doc = _session_doc(deliberation_session)
	_ensure_not_cancelled(doc)
	_ensure_not_locked(doc)
	if _norm(doc.status) != "Scheduled":
		frappe.throw(
			_("The session must be Scheduled before it can start (current status: {0}).").format(_norm(doc.status)),
			frappe.ValidationError,
		)
	doc.status = "In Progress"
	if not doc.actual_start_datetime:
		doc.actual_start_datetime = now_datetime()
	_save_session(doc)
	_append_event(doc.name, "Started", _("Session started."), actor_user=actor_user)
	return doc


@frappe.whitelist()
def complete_deliberation_session(deliberation_session: str, actor_user: str | None = None) -> Document:
	"""**In Progress** → **Completed**. Sets **actual_end_datetime** if empty. Emits **Completed**."""
	doc = _session_doc(deliberation_session)
	_ensure_not_cancelled(doc)
	_ensure_not_locked(doc)
	if _norm(doc.status) != "In Progress":
		frappe.throw(
			_("The session must be In Progress before it can complete (current status: {0}).").format(
				_norm(doc.status)
			),
			frappe.ValidationError,
		)
	doc.status = "Completed"
	if not doc.actual_end_datetime:
		doc.actual_end_datetime = now_datetime()
	_save_session(doc)
	_append_event(doc.name, "Completed", _("Session completed."), actor_user=actor_user)
	return doc


@frappe.whitelist()
def lock_deliberation_session(deliberation_session: str, actor_user: str | None = None) -> Document:
	"""Set **session_locked**. Allowed when **In Progress** or **Completed**. Idempotent if already locked. Emits **Locked** once."""
	doc = _session_doc(deliberation_session)
	_ensure_not_cancelled(doc)
	if int(doc.get("session_locked") or 0):
		return doc
	st = _norm(doc.status)
	if st not in ("In Progress", "Completed"):
		frappe.throw(
			_("Only an In Progress or Completed session can be locked (current status: {0}).").format(st),
			frappe.ValidationError,
		)
	doc.session_locked = 1
	_save_session(doc)
	_append_event(doc.name, "Locked", _("Session locked."), actor_user=actor_user)
	return doc
