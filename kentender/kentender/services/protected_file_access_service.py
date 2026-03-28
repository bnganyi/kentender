# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Protected retrieval for **KenTender Typed Attachment** binaries (STORY-CORE-020).

This module is the **only** supported server-side path in KenTender for reading file
bytes tied to a typed attachment. Callers must not fetch ``File`` content for those
assets via ad-hoc ``get_content()`` in feature code — use
:func:`get_bytes_for_typed_attachment` so permission checks and audit hooks run
consistently.

**Pluggable permission:** pass ``permission_check`` (``Callable[[Document], bool]``).
The default uses ``frappe.has_permission`` on the **KenTender Typed Attachment**
document. Later modules can replace this with entity/role rules without changing
the read pipeline.

**Audit (CORE-017):** denied attempts call :func:`kentender.services.access_audit_service.log_access_denied`;
allowed reads on **sensitive** classifications call :func:`kentender.services.access_audit_service.log_sensitive_access`.
Non-sensitive (e.g. **Public**) successful reads do not emit ``sensitive_access`` events by default.

Call only from **server-side** code.
"""

from __future__ import annotations

from collections.abc import Callable

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.services.access_audit_service import log_access_denied, log_sensitive_access
from kentender.services.sensitivity_classification import is_sensitive

TYPED_ATTACHMENT_DOCTYPE = "KenTender Typed Attachment"


def default_permission_check(typed_attachment: Document) -> bool:
	"""Return whether the current session may read the typed attachment document."""
	return bool(
		frappe.has_permission(
			TYPED_ATTACHMENT_DOCTYPE,
			"read",
			doc=typed_attachment,
		)
	)


def get_bytes_for_typed_attachment(
	typed_attachment_name: str,
	*,
	access_action: str = "read",
	permission_check: Callable[[Document], bool] | None = None,
	actor: str | None = None,
	procuring_entity: str | None = None,
	business_id: str | None = None,
) -> bytes:
	"""Return file bytes for a **KenTender Typed Attachment** after checks and optional audit.

	:param typed_attachment_name: Name (primary key) of the typed attachment.
	:param access_action: Logical operation (e.g. ``read``, ``download``) for audit payloads.
	:param permission_check: If ``None``, uses :func:`default_permission_check`.
	:raises frappe.PermissionError: If the record is missing, permission fails, or file content is unavailable.
	"""
	name = (typed_attachment_name or "").strip()
	if not name:
		frappe.throw(_("Typed attachment name is required."), frappe.ValidationError)

	if not frappe.db.exists(TYPED_ATTACHMENT_DOCTYPE, name):
		log_access_denied(
			resource_doctype=TYPED_ATTACHMENT_DOCTYPE,
			resource_name=name,
			action=access_action,
			denial_reason="KenTender Typed Attachment does not exist.",
			actor=actor,
			procuring_entity=procuring_entity,
			business_id=business_id,
		)
		raise frappe.PermissionError(_("KenTender Typed Attachment not found."))

	doc = frappe.get_doc(TYPED_ATTACHMENT_DOCTYPE, name)
	check = permission_check or default_permission_check
	if not check(doc):
		log_access_denied(
			resource_doctype=TYPED_ATTACHMENT_DOCTYPE,
			resource_name=doc.name,
			action=access_action,
			denial_reason="Permission check failed for typed attachment read.",
			actor=actor,
			procuring_entity=procuring_entity,
			business_id=business_id,
		)
		raise frappe.PermissionError(_("Not permitted to access this attachment."))

	attached = (doc.attached_file or "").strip()
	if not attached or not frappe.db.exists("File", attached):
		log_access_denied(
			resource_doctype=TYPED_ATTACHMENT_DOCTYPE,
			resource_name=doc.name,
			action=access_action,
			denial_reason="Linked File is missing or was removed.",
			actor=actor,
			procuring_entity=procuring_entity,
			business_id=business_id,
		)
		raise frappe.PermissionError(_("Attachment file is not available."))

	file_doc = frappe.get_doc("File", attached)
	try:
		raw = file_doc.get_content()
	except Exception as e:
		log_access_denied(
			resource_doctype=TYPED_ATTACHMENT_DOCTYPE,
			resource_name=doc.name,
			action=access_action,
			denial_reason=f"Could not read file content: {e!s}",
			actor=actor,
			procuring_entity=procuring_entity,
			business_id=business_id,
		)
		raise frappe.PermissionError(_("Could not read attachment file.")) from e

	if isinstance(raw, str):
		raw = raw.encode("utf-8")
	if not isinstance(raw, (bytes, bytearray)):
		log_access_denied(
			resource_doctype=TYPED_ATTACHMENT_DOCTYPE,
			resource_name=doc.name,
			action=access_action,
			denial_reason="File content is not available as bytes.",
			actor=actor,
			procuring_entity=procuring_entity,
			business_id=business_id,
		)
		raise frappe.PermissionError(_("Attachment file content is invalid."))

	if is_sensitive(doc.sensitivity_class):
		log_sensitive_access(
			resource_doctype=TYPED_ATTACHMENT_DOCTYPE,
			resource_name=doc.name,
			access_action=access_action,
			actor=actor,
			sensitivity_class=doc.sensitivity_class,
			context=f"attached_file={attached}",
			procuring_entity=procuring_entity,
			business_id=business_id,
		)

	return bytes(raw)
