# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Append-only audit event logging for KenTender.

Call :func:`log_audit_event` from server-side code only. Events are stored as
**KenTender Audit Event** and must not be updated or deleted via the document API
(see DocType controller). Test teardown may use ``frappe.db.delete`` where needed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime

AUDIT_EVENT_DOCTYPE = "KenTender Audit Event"


def _dt_iso(value: datetime | str | None) -> str:
	if value is None:
		return ""
	if isinstance(value, datetime):
		return value.isoformat()
	return str(get_datetime(value) or value)


def _compute_event_hash(payload: dict[str, Any], salt: str) -> str:
	canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
	raw = f"{canonical}|{salt}".encode("utf-8")
	return hashlib.sha256(raw).hexdigest()


def log_audit_event(
	*,
	event_type: str,
	actor: str | None = None,
	source_module: str | None = None,
	target_doctype: str | None = None,
	target_docname: str | None = None,
	actor_role: str | None = None,
	procuring_entity: str | None = None,
	old_state: str | None = None,
	new_state: str | None = None,
	changed_fields_summary: str | None = None,
	reason: str | None = None,
	event_datetime: datetime | str | None = None,
) -> Document:
	"""Insert one **KenTender Audit Event** with a content hash over the payload.

	:param event_type: Required logical event name (e.g. ``payment.submitted``).
	:param actor: Defaults to current session user, or ``Administrator`` when no session user.
	"""
	if not (event_type or "").strip():
		frappe.throw(_("event_type is required."), frappe.ValidationError)

	resolved_actor = (actor or "").strip()
	if not resolved_actor:
		resolved_actor = getattr(frappe.session, "user", None) or "Administrator"

	resolved_dt = event_datetime or now_datetime()
	dt_iso = _dt_iso(resolved_dt)

	hash_payload = {
		"actor": resolved_actor,
		"actor_role": actor_role or "",
		"changed_fields_summary": changed_fields_summary or "",
		"event_datetime": dt_iso,
		"event_type": event_type.strip(),
		"new_state": new_state or "",
		"old_state": old_state or "",
		"procuring_entity": procuring_entity or "",
		"reason": reason or "",
		"source_module": source_module or "",
		"target_docname": target_docname or "",
		"target_doctype": target_doctype or "",
	}
	salt = str(frappe.get_site_config().get("audit_event_salt") or "")
	event_hash = _compute_event_hash(hash_payload, salt)

	doc = frappe.get_doc(
		{
			"doctype": AUDIT_EVENT_DOCTYPE,
			"actor": resolved_actor,
			"actor_role": actor_role,
			"changed_fields_summary": changed_fields_summary,
			"event_datetime": resolved_dt,
			"event_hash": event_hash,
			"event_type": event_type.strip(),
			"new_state": new_state,
			"old_state": old_state,
			"procuring_entity": procuring_entity,
			"reason": reason,
			"source_module": source_module,
			"target_docname": target_docname,
			"target_doctype": target_doctype,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc
