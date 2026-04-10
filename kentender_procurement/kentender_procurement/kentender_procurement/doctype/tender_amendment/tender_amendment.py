# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Amendment — post-publication change record (PROC-STORY-030).

Does not apply changes to Tender automatically (pack constraint).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"
TENDER_DOCUMENT_DOCTYPE = "Tender Document"
DOCTYPE = "Tender Amendment"

STATUS_PUBLISHED = "Published"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class TenderAmendment(Document):
	def validate(self):
		self._normalize_text()
		self._validate_tender_exists()
		self._validate_amendment_no()
		self._validate_amendment_no_unique()
		self._validate_related_document()
		self._validate_deadline_coherence()
		self._validate_published_coherence()
		bid = _strip(self.business_id)
		no = cint(self.amendment_no)
		self.display_label = code_title_label(bid, f"Amendment {no}")

	def _normalize_text(self) -> None:
		for fn in ("business_id", "change_summary", "reason"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

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

	def _validate_amendment_no(self) -> None:
		n = cint(self.amendment_no)
		if n < 1:
			frappe.throw(
				_("Amendment No must be at least 1."),
				frappe.ValidationError,
				title=_("Invalid amendment number"),
			)

	def _validate_amendment_no_unique(self) -> None:
		tn = _strip(self.tender)
		n = cint(self.amendment_no)
		if not tn:
			return
		rows = frappe.get_all(
			DOCTYPE,
			filters={"tender": tn, "amendment_no": n},
			fields=["name"],
		)
		for row in rows:
			if _strip(row.get("name") or "") == _strip(self.name or ""):
				continue
			frappe.throw(
				_("Amendment No {0} already exists for this tender.").format(frappe.bold(str(n))),
				frappe.ValidationError,
				title=_("Duplicate amendment"),
			)

	def _validate_related_document(self) -> None:
		rd = _strip(self.related_document)
		if not rd:
			return
		if not frappe.db.exists(TENDER_DOCUMENT_DOCTYPE, rd):
			frappe.throw(
				_("Related Document {0} does not exist.").format(frappe.bold(rd)),
				frappe.ValidationError,
				title=_("Invalid related document"),
			)
		doc_tender = _strip(frappe.db.get_value(TENDER_DOCUMENT_DOCTYPE, rd, "tender"))
		tn = _strip(self.tender)
		if doc_tender != tn:
			frappe.throw(
				_("Related Document must belong to the same tender."),
				frappe.ValidationError,
				title=_("Related document mismatch"),
			)

	def _validate_deadline_coherence(self) -> None:
		ext = bool(self.requires_deadline_extension)
		nsd = self.new_submission_deadline
		nod = self.new_opening_datetime
		if ext:
			if not nsd:
				frappe.throw(
					_("New Submission Deadline is required when deadline extension is required."),
					frappe.ValidationError,
					title=_("Deadline extension"),
				)
			return
		if nsd or nod:
			frappe.throw(
				_("New deadline fields must be empty unless deadline extension is required."),
				frappe.ValidationError,
				title=_("Deadline extension"),
			)

	def _validate_published_coherence(self) -> None:
		if _strip(self.status) != STATUS_PUBLISHED:
			return
		if not _strip(self.published_by):
			frappe.throw(
				_("Published By is required when status is Published."),
				frappe.ValidationError,
				title=_("Incomplete publication"),
			)
		if not self.published_at:
			frappe.throw(
				_("Published At is required when status is Published."),
				frappe.ValidationError,
				title=_("Incomplete publication"),
			)
