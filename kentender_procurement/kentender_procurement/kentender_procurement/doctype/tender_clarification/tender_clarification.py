# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender Clarification — Q&A lifecycle scaffold (PROC-STORY-029)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.utils.display_label import code_title_label

TENDER_DOCTYPE = "Tender"
STATUS_ANSWERED = "Answered"
QUESTION_SNIPPET_LEN = 80


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _snippet(text: str | None, max_len: int = QUESTION_SNIPPET_LEN) -> str:
	t = _strip(text)
	if len(t) > max_len:
		return t[:max_len] + "…"
	return t


class TenderClarification(Document):
	def validate(self):
		self._normalize_text()
		self._set_question_datetime_default()
		self._validate_tender_exists()
		self._validate_question_text()
		self._validate_answered_state()
		bid = _strip(self.business_id)
		qsnip = _snippet(self.question_text)
		self.display_label = code_title_label(bid, qsnip or _strip(self.status))

	def _normalize_text(self) -> None:
		for fn in ("business_id", "supplier", "question_text", "response_text", "related_amendment"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _set_question_datetime_default(self) -> None:
		if self.is_new() and not self.question_datetime:
			self.question_datetime = now_datetime()

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

	def _validate_question_text(self) -> None:
		if not _strip(self.question_text):
			frappe.throw(
				_("Question Text is required."),
				frappe.ValidationError,
				title=_("Invalid question"),
			)

	def _validate_answered_state(self) -> None:
		if _strip(self.status) != STATUS_ANSWERED:
			return
		if not _strip(self.response_text):
			frappe.throw(
				_("Response Text is required when status is Answered."),
				frappe.ValidationError,
				title=_("Incomplete response"),
			)
		if not self.response_datetime:
			frappe.throw(
				_("Response Datetime is required when status is Answered."),
				frappe.ValidationError,
				title=_("Incomplete response"),
			)
		if not _strip(self.responded_by_user):
			frappe.throw(
				_("Responded By User is required when status is Answered."),
				frappe.ValidationError,
				title=_("Incomplete response"),
			)
