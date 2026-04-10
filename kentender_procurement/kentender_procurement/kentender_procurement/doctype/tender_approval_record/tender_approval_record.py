# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Approval Record — append-only audit of tender decisions (PROC-STORY-027)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"
EXCEPTION_RECORD_DOCTYPE = "Exception Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class TenderApprovalRecord(Document):
	def validate(self):
		self.display_label = code_title_label(
			_strip(self.tender),
			_strip(self.workflow_step),
		)
		if not self.is_new():
			frappe.throw(
				_("Tender Approval Record cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)
		self._validate_tender_exists()
		self._validate_exception_record()

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

	def _validate_exception_record(self) -> None:
		en = _strip(self.exception_record)
		if not en:
			return
		if not frappe.db.exists(EXCEPTION_RECORD_DOCTYPE, en):
			frappe.throw(
				_("Exception Record {0} does not exist.").format(frappe.bold(en)),
				frappe.ValidationError,
				title=_("Invalid exception record"),
			)

	def on_trash(self):
		frappe.throw(
			_("Tender Approval Record cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
