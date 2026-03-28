# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.services.sensitivity_classification import (
	CANONICAL_SENSITIVITY_CLASSES,
	normalize_sensitivity_class,
)

# Hash at most this many bytes of file content (memory bound). Full-file hashing for
# large binaries should use streaming in a dedicated service (e.g. CORE-020).
FILE_HASH_MAX_BYTES = 2 * 1024 * 1024


class KenTenderTypedAttachment(Document):
	def validate(self):
		self._set_upload_defaults()
		self._validate_sensitivity_class()
		self._validate_owning_reference()
		self._validate_document_type()
		self._validate_attached_file()
		self._refresh_file_hash()

	def _set_upload_defaults(self):
		if self.is_new():
			if not self.uploaded_at:
				self.uploaded_at = now_datetime()
			if not (self.uploaded_by or "").strip():
				self.uploaded_by = getattr(frappe.session, "user", None) or "Administrator"

	def _validate_sensitivity_class(self):
		normalized = normalize_sensitivity_class(self.sensitivity_class)
		if not normalized:
			allowed = ", ".join(CANONICAL_SENSITIVITY_CLASSES)
			frappe.throw(
				_("Sensitivity Class must be one of: {0}").format(allowed),
				frappe.ValidationError,
				title=_("Invalid sensitivity class"),
			)
		self.sensitivity_class = normalized

	def _validate_owning_reference(self):
		if not (self.owning_doctype or "").strip() or not (self.owning_docname or "").strip():
			frappe.throw(
				_("Owning DocType and Owning Document are required."),
				frappe.ValidationError,
				title=_("Invalid ownership"),
			)
		if not frappe.db.exists(self.owning_doctype, self.owning_docname):
			frappe.throw(
				_("Owning document {0} {1} does not exist.").format(
					frappe.bold(self.owning_doctype),
					frappe.bold(self.owning_docname),
				),
				frappe.ValidationError,
				title=_("Invalid ownership"),
			)

	def _validate_document_type(self):
		if not self.document_type:
			return
		if not frappe.db.exists("Document Type Registry", self.document_type):
			frappe.throw(
				_("Document Type {0} does not exist.").format(frappe.bold(self.document_type)),
				frappe.ValidationError,
				title=_("Invalid document type"),
			)

	def _validate_attached_file(self):
		if not self.attached_file:
			return
		if not frappe.db.exists("File", self.attached_file):
			frappe.throw(
				_("File {0} does not exist.").format(frappe.bold(self.attached_file)),
				frappe.ValidationError,
				title=_("Invalid file"),
			)

	def _refresh_file_hash(self):
		if not self.attached_file:
			self.file_hash = None
			return
		try:
			file_doc = frappe.get_doc("File", self.attached_file)
			content = file_doc.get_content()
			if isinstance(content, str):
				content = content.encode("utf-8")
			if not isinstance(content, (bytes, bytearray)):
				self.file_hash = None
				return
			chunk = bytes(content[:FILE_HASH_MAX_BYTES])
			self.file_hash = hashlib.sha256(chunk).hexdigest()
		except Exception as e:
			frappe.log_error(
				title="KenTender Typed Attachment file hash",
				message=frappe.get_traceback(),
			)
			frappe.throw(
				_("Could not compute file hash: {0}").format(str(e)),
				frappe.ValidationError,
				title=_("File hash error"),
			)
