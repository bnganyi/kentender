# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Document — file attached to a bid envelope section (PROC-STORY-038).

File content hash uses the same bounded read + SHA-256 approach as Tender Document /
KenTender Typed Attachment (kentender_typed_attachment.py).
"""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.services.sensitivity_classification import (
	CANONICAL_SENSITIVITY_CLASSES,
	normalize_sensitivity_class,
)

BID_SUBMISSION = "Bid Submission"
BID_ENVELOPE_SECTION = "Bid Envelope Section"
DOCUMENT_TYPE_REGISTRY = "Document Type Registry"
FILE_DOCTYPE = "File"

# Same bound as KenTender Typed Attachment (kentender_typed_attachment.py).
FILE_HASH_MAX_BYTES = 2 * 1024 * 1024


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidDocument(Document):
	def validate(self):
		self._normalize_text()
		self._set_upload_defaults()
		self._validate_bid_submission()
		self._validate_bid_envelope_section()
		self._validate_document_type()
		self._validate_attached_file()
		self._validate_sensitivity_class()
		self._refresh_hash_value()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("document_title", "validation_notes"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _set_upload_defaults(self) -> None:
		if self.is_new():
			if not self.uploaded_at:
				self.uploaded_at = now_datetime()
			if not _strip(self.uploaded_by):
				self.uploaded_by = getattr(frappe.session, "user", None) or "Administrator"

	def _validate_bid_submission(self) -> None:
		bs = _strip(self.bid_submission)
		if not bs:
			return
		if not frappe.db.exists(BID_SUBMISSION, bs):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bs)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)

	def _validate_bid_envelope_section(self) -> None:
		sec = _strip(self.bid_envelope_section)
		bs = _strip(self.bid_submission)
		if not sec:
			return
		if not frappe.db.exists(BID_ENVELOPE_SECTION, sec):
			frappe.throw(
				_("Bid Envelope Section {0} does not exist.").format(frappe.bold(sec)),
				frappe.ValidationError,
				title=_("Invalid section"),
			)
		sec_bs = _strip(frappe.db.get_value(BID_ENVELOPE_SECTION, sec, "bid_submission"))
		if bs and sec_bs != bs:
			frappe.throw(
				_("Bid Envelope Section must belong to the selected Bid Submission."),
				frappe.ValidationError,
				title=_("Section mismatch"),
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
				title="Bid Document file hash",
				message=frappe.get_traceback(),
			)
			frappe.throw(
				_("Could not compute file hash: {0}").format(str(e)),
				frappe.ValidationError,
				title=_("File hash error"),
			)

	def _set_display_label(self) -> None:
		title = _strip(self.document_title) or _("Untitled")
		self.display_label = title
