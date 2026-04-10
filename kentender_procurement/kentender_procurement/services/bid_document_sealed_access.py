# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Controlled read path for **Bid Document** file bytes (PROC-STORY-046).

Do not call :meth:`frappe.core.doctype.file.file.File.get_content` on bid-linked files from
feature code — use :func:`get_bytes_for_bid_document` so permission checks and audit hooks stay
consistent with KenTender protected-access patterns.

**Placeholder permission:** pass ``permission_check`` (``Callable[[Document], bool]``) or rely on
:func:`default_bid_document_permission` (conservative: **System Manager** only until product matrix lands).
"""

from __future__ import annotations

from collections.abc import Callable

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.services.access_audit_service import log_access_denied, log_sensitive_access
from kentender.services.sensitivity_classification import is_sensitive

BD = "Bid Document"
BS = "Bid Submission"
FILE = "File"


def default_bid_document_permission(bid_document: Document) -> bool:
	"""Placeholder (046): allow **System Manager**; extend with supplier portal / PE roles later."""
	user = getattr(frappe.session, "user", None) or "Guest"
	return "System Manager" in frappe.get_roles(user)


def get_bytes_for_bid_document(
	bid_document_name: str,
	*,
	access_action: str = "read",
	permission_check: Callable[[Document], bool] | None = None,
	actor: str | None = None,
	procuring_entity: str | None = None,
) -> bytes:
	"""Return file bytes for a bid document after checks and audit (mirrors typed-attachment pipeline)."""
	bn = (bid_document_name or "").strip()
	if not bn:
		frappe.throw(_("Bid Document name is required."), frappe.ValidationError)

	if not frappe.db.exists(BD, bn):
		log_access_denied(
			resource_doctype=BD,
			resource_name=bn,
			action=access_action,
			denial_reason="Bid Document does not exist.",
			actor=actor,
			procuring_entity=procuring_entity,
		)
		raise frappe.PermissionError(_("Bid Document not found."))

	doc = frappe.get_doc(BD, bn)
	check = permission_check or default_bid_document_permission
	if not check(doc):
		log_access_denied(
			resource_doctype=BD,
			resource_name=bn,
			action=access_action,
			denial_reason="Permission check failed for bid document read.",
			actor=actor,
			procuring_entity=procuring_entity,
		)
		raise frappe.PermissionError(_("Not permitted to access this bid document."))

	bs_name = (doc.bid_submission or "").strip()

	fn = (doc.attached_file or "").strip()
	if not fn or not frappe.db.exists(FILE, fn):
		log_access_denied(
			resource_doctype=BD,
			resource_name=bn,
			action=access_action,
			denial_reason="Linked File is missing or was removed.",
			actor=actor,
			procuring_entity=procuring_entity,
		)
		raise frappe.PermissionError(_("Attachment file is not available."))

	file_doc = frappe.get_doc(FILE, fn)
	try:
		raw = file_doc.get_content()
	except Exception as e:
		log_access_denied(
			resource_doctype=BD,
			resource_name=bn,
			action=access_action,
			denial_reason=f"Could not read file content: {e!s}",
			actor=actor,
			procuring_entity=procuring_entity,
		)
		raise frappe.PermissionError(_("Could not read attachment file.")) from e

	if isinstance(raw, str):
		raw = raw.encode("utf-8")
	if not isinstance(raw, (bytes, bytearray)):
		log_access_denied(
			resource_doctype=BD,
			resource_name=bn,
			action=access_action,
			denial_reason="File content is not available as bytes.",
			actor=actor,
			procuring_entity=procuring_entity,
		)
		raise frappe.PermissionError(_("Attachment file content is invalid."))

	if is_sensitive(doc.sensitivity_class):
		log_sensitive_access(
			resource_doctype=BD,
			resource_name=bn,
			access_action=access_action,
			actor=actor,
			sensitivity_class=doc.sensitivity_class,
			context=f"attached_file={fn}; bid_submission={bs_name}",
			procuring_entity=procuring_entity,
		)

	return bytes(raw)
