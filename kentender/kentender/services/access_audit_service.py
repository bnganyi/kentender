# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Security-oriented audit helpers (STORY-CORE-017).

These functions wrap :func:`kentender.services.audit_event_service.log_audit_event`
with stable **event_type** values so permission and file services can log consistently.

**Event types (do not rename without a migration plan):**

- ``kt.security.access_denied`` — attempted action was denied.
- ``kt.security.sensitive_access`` — allowed access to a sensitive resource (e.g. view/download).

Call only from **server-side** code.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.services.audit_event_service import log_audit_event

EVENT_ACCESS_DENIED = "kt.security.access_denied"
EVENT_SENSITIVE_ACCESS = "kt.security.sensitive_access"
SOURCE_MODULE = "kentender.security"


def log_access_denied(
	*,
	resource_doctype: str,
	resource_name: str,
	action: str,
	denial_reason: str,
	actor: str | None = None,
	actor_role: str | None = None,
	procuring_entity: str | None = None,
	business_id: str | None = None,
) -> Document:
	"""Log a denied access attempt against a target document.

	:param resource_doctype: Target DocType name (e.g. ``File``, business DocType).
	:param resource_name: Target document name.
	:param action: Attempted operation (e.g. ``read``, ``view``, ``download``).
	:param denial_reason: Why access was denied (required).
	"""
	if not (denial_reason or "").strip():
		frappe.throw(_("denial_reason is required."), frappe.ValidationError)
	if not (resource_doctype or "").strip() or not (resource_name or "").strip():
		frappe.throw(_("resource_doctype and resource_name are required."), frappe.ValidationError)

	detail: dict[str, Any] = {
		"action": (action or "").strip() or "unknown",
		"denial_reason": denial_reason.strip(),
	}
	reason = _("Access denied: {0} on {1} {2}").format(
		detail["action"],
		resource_doctype.strip(),
		resource_name.strip(),
	)

	return log_audit_event(
		event_type=EVENT_ACCESS_DENIED,
		actor=actor,
		actor_role=actor_role,
		source_module=SOURCE_MODULE,
		target_doctype=resource_doctype.strip(),
		target_docname=resource_name.strip(),
		business_id=business_id,
		procuring_entity=procuring_entity,
		reason=reason,
		new_state=json.dumps(detail, sort_keys=True, ensure_ascii=False),
	)


def log_sensitive_access(
	*,
	resource_doctype: str,
	resource_name: str,
	access_action: str,
	actor: str | None = None,
	actor_role: str | None = None,
	procuring_entity: str | None = None,
	business_id: str | None = None,
	sensitivity_class: str | None = None,
	context: str | None = None,
) -> Document:
	"""Log successful access to content treated as sensitive.

	:param access_action: Operation performed (e.g. ``read``, ``download``).
	:param sensitivity_class: Optional label (e.g. ``Confidential``); product enums may evolve.
	:param context: Optional free-text note (keep short).
	"""
	if not (resource_doctype or "").strip() or not (resource_name or "").strip():
		frappe.throw(_("resource_doctype and resource_name are required."), frappe.ValidationError)

	detail: dict[str, Any] = {
		"access_action": (access_action or "").strip() or "unknown",
	}
	if sensitivity_class:
		detail["sensitivity_class"] = sensitivity_class.strip()
	if context:
		detail["context"] = context.strip()

	reason = _("Sensitive access: {0} on {1} {2}").format(
		detail["access_action"],
		resource_doctype.strip(),
		resource_name.strip(),
	)

	return log_audit_event(
		event_type=EVENT_SENSITIVE_ACCESS,
		actor=actor,
		actor_role=actor_role,
		source_module=SOURCE_MODULE,
		target_doctype=resource_doctype.strip(),
		target_docname=resource_name.strip(),
		business_id=business_id,
		procuring_entity=procuring_entity,
		reason=reason,
		new_state=json.dumps(detail, sort_keys=True, ensure_ascii=False),
		changed_fields_summary=sensitivity_class,
	)
