# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Document — attachments linked to a tender/lot (PROC-STORY-026).

File content hash uses the same bounded read + SHA-256 approach as KenTender Typed Attachment.
"""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

from kentender.services.sensitivity_classification import (
	CANONICAL_SENSITIVITY_CLASSES,
	normalize_sensitivity_class,
)

TENDER_DOCTYPE = "Tender"
TENDER_LOT_DOCTYPE = "Tender Lot"
DOCTYPE = "Tender Document"
DOCUMENT_TYPE_REGISTRY = "Document Type Registry"
FILE_DOCTYPE = "File"

# Same bound as KenTender Typed Attachment (kentender_typed_attachment.py).
FILE_HASH_MAX_BYTES = 2 * 1024 * 1024


def _strip(s: str | None) -> str:
	return (s or "").strip()


class TenderDocument(Document):
	def validate(self):
		self._normalize_text()
		self._set_upload_defaults()
		self._validate_version_no()
		self._validate_tender_exists()
		self._validate_lot_alignment()
		self._validate_document_type()
		self._validate_attached_file()
		self._validate_sensitivity_class()
		self._validate_supersedes_document()
		self._refresh_hash_value()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("document_title",):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _set_upload_defaults(self) -> None:
		if self.is_new():
			if not self.uploaded_at:
				self.uploaded_at = now_datetime()
			if not _strip(self.uploaded_by):
				self.uploaded_by = getattr(frappe.session, "user", None) or "Administrator"

	def _validate_version_no(self) -> None:
		v = cint(self.document_version_no)
		if v < 1:
			frappe.throw(
				_("Document Version No must be at least 1."),
				frappe.ValidationError,
				title=_("Invalid version"),
			)

	def _validate_tender_exists(self) -> None:
		tn = _strip(self.tender)
		if not tn:
			return
		if not frappe.db.exists(TENDER_DOCTYPE, tn):
			frappe.throw(
				_("Tender {0} does not exist.").format(frappe.bold(tn)),
				frappe.ValidationError,
				title=_("Invalid tender"),
			)

	def _validate_lot_alignment(self) -> None:
		ln = _strip(self.lot)
		tn = _strip(self.tender)
		if not ln:
			return
		if not frappe.db.exists(TENDER_LOT_DOCTYPE, ln):
			frappe.throw(
				_("Tender Lot {0} does not exist.").format(frappe.bold(ln)),
				frappe.ValidationError,
				title=_("Invalid lot"),
			)
		lot_tender = _strip(frappe.db.get_value(TENDER_LOT_DOCTYPE, ln, "tender"))
		if lot_tender != tn:
			frappe.throw(
				_("Tender Lot must belong to the selected tender."),
				frappe.ValidationError,
				title=_("Lot mismatch"),
			)

	def _validate_document_type(self) -> None:
		dt = _strip(self.document_type)
		if not dt:
			return
		if not frappe.db.exists(DOCUMENT_TYPE_REGISTRY, dt):
			frappe.throw(
				_("Document Type {0} does not exist.").format(frappe.bold(dt)),
				frappe.ValidationError,
				title=_("Invalid document type"),
			)

	def _validate_attached_file(self) -> None:
		fn = _strip(self.attached_file)
		if not fn:
			return
		if not frappe.db.exists(FILE_DOCTYPE, fn):
			frappe.throw(
				_("File {0} does not exist.").format(frappe.bold(fn)),
				frappe.ValidationError,
				title=_("Invalid file"),
			)

	def _validate_sensitivity_class(self) -> None:
		normalized = normalize_sensitivity_class(self.sensitivity_class)
		if not normalized:
			allowed = ", ".join(CANONICAL_SENSITIVITY_CLASSES)
			frappe.throw(
				_("Sensitivity Class must be one of: {0}").format(allowed),
				frappe.ValidationError,
				title=_("Invalid sensitivity class"),
			)
		self.sensitivity_class = normalized

	def _validate_supersedes_document(self) -> None:
		prev = _strip(self.supersedes_document)
		if not prev:
			return
		if not frappe.db.exists(DOCTYPE, prev):
			frappe.throw(
				_("Supersedes Document {0} does not exist.").format(frappe.bold(prev)),
				frappe.ValidationError,
				title=_("Invalid supersedes link"),
			)
		my_name = _strip(self.name or "")
		if my_name and prev == my_name:
			frappe.throw(
				_("A document cannot supersede itself."),
				frappe.ValidationError,
				title=_("Invalid supersedes link"),
			)
		other = frappe.get_doc(DOCTYPE, prev)
		if _strip(other.tender) != _strip(self.tender):
			frappe.throw(
				_("Supersedes Document must belong to the same tender."),
				frappe.ValidationError,
				title=_("Invalid supersedes link"),
			)
		my_lot = _strip(self.lot)
		other_lot = _strip(other.lot or "")
		if my_lot != other_lot:
			frappe.throw(
				_("Supersedes Document must have the same lot scope (both tender-wide or same lot)."),
				frappe.ValidationError,
				title=_("Invalid supersedes link"),
			)

	def _refresh_hash_value(self) -> None:
		fn = _strip(self.attached_file)
		if not fn:
			self.hash_value = None
			return
		try:
			file_doc = frappe.get_doc(FILE_DOCTYPE, fn)
			content = file_doc.get_content()
			if isinstance(content, str):
				content = content.encode("utf-8")
			if not isinstance(content, (bytes, bytearray)):
				self.hash_value = None
				return
			chunk = bytes(content[:FILE_HASH_MAX_BYTES])
			self.hash_value = hashlib.sha256(chunk).hexdigest()
		except Exception as e:
			frappe.log_error(
				title="Tender Document file hash",
				message=frappe.get_traceback(),
			)
			frappe.throw(
				_("Could not compute file hash: {0}").format(str(e)),
				frappe.ValidationError,
				title=_("File hash error"),
			)

	def _set_display_label(self) -> None:
		title = _strip(self.document_title) or _("Untitled")
		v = cint(self.document_version_no) or 1
		self.display_label = f"{title} (v{v})"
