# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Validation Issue — recorded validation finding on a bid (PROC-STORY-042)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

from kentender.utils.display_label import code_title_label

BS = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _short_snippet(text: str, max_len: int = 60) -> str:
	t = (text or "").strip()
	if len(t) <= max_len:
		return t
	return t[: max_len - 1] + "…"


class BidValidationIssue(Document):
	def validate(self):
		self._normalize_text_fields()
		self._apply_resolution_rules()
		self._set_display_label()
		self._validate_bid_submission_exists()
		self._validate_issue_message()

	def _normalize_text_fields(self) -> None:
		self.issue_message = _strip(self.issue_message)
		self.resolved_notes = _strip(self.resolved_notes)

	def _apply_resolution_rules(self) -> None:
		if cint(self.resolved_flag):
			if not self.resolved_on:
				self.resolved_on = now_datetime()
		else:
			self.resolved_on = None
			self.resolved_notes = None

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.severity), _short_snippet(self.issue_message))

	def _validate_bid_submission_exists(self) -> None:
		bn = _strip(self.bid_submission)
		if not bn:
			return
		if not frappe.db.exists(BS, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)

	def _validate_issue_message(self) -> None:
		if not _strip(self.issue_message):
			frappe.throw(
				_("Issue Message is required."),
				frappe.ValidationError,
				title=_("Missing issue message"),
			)
