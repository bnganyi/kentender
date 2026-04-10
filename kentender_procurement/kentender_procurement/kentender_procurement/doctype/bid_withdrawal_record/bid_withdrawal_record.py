# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Withdrawal Record — append-only withdrawal history (PROC-STORY-041)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import format_datetime

from kentender.utils.display_label import code_title_label

BS = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidWithdrawalRecord(Document):
	def validate(self):
		self._normalize_text_fields()
		self._set_display_label()
		if not self.is_new():
			frappe.throw(
				_("Bid Withdrawal Record cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)
		self._validate_bid_submission_exists()
		self._validate_withdrawn_by_user_exists()
		self._validate_reason()

	def _normalize_text_fields(self) -> None:
		self.reason = _strip(self.reason)

	def _set_display_label(self) -> None:
		dt = self.withdrawal_datetime
		part = format_datetime(dt) if dt else ""
		self.display_label = code_title_label(_strip(self.status), part)

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

	def _validate_withdrawn_by_user_exists(self) -> None:
		un = _strip(self.withdrawn_by_user)
		if not un:
			return
		if not frappe.db.exists("User", un):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(un)),
				frappe.ValidationError,
				title=_("Invalid user"),
			)

	def _validate_reason(self) -> None:
		if not _strip(self.reason):
			frappe.throw(
				_("Reason is required."),
				frappe.ValidationError,
				title=_("Missing reason"),
			)

	def on_trash(self):
		frappe.throw(
			_("Bid Withdrawal Record cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
