# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Opening Event Log — append-only opening ceremony audit trail (PROC-STORY-051)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import format_datetime

from kentender.utils.display_label import code_title_label

SESSION = "Bid Opening Session"
BS = "Bid Submission"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _short_snippet(text: str, max_len: int = 60) -> str:
	t = (text or "").strip()
	if len(t) <= max_len:
		return t
	return t[: max_len - 1] + "…"


class BidOpeningEventLog(Document):
	def validate(self):
		self._normalize_text()
		self._set_display_label()
		if not self.is_new():
			frappe.throw(
				_("Bid Opening Event Log cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)
		self._validate_session()
		self._validate_actor_user()
		self._validate_related_bid()
		self._validate_event_hash()

	def _normalize_text(self) -> None:
		self.event_summary = _strip(self.event_summary)
		self.event_hash = _strip(self.event_hash)

	def _set_display_label(self) -> None:
		summary_part = _short_snippet(self.event_summary)
		if self.event_datetime:
			dt = format_datetime(self.event_datetime)
			summary_part = f"{summary_part} · {dt}" if summary_part else dt
		self.display_label = code_title_label(_strip(self.event_type), summary_part)

	def _validate_session(self) -> None:
		sn = _strip(self.bid_opening_session)
		if not sn:
			return
		if not frappe.db.exists(SESSION, sn):
			frappe.throw(
				_("Bid Opening Session {0} does not exist.").format(frappe.bold(sn)),
				frappe.ValidationError,
				title=_("Invalid session"),
			)

	def _validate_actor_user(self) -> None:
		un = _strip(self.actor_user)
		if not un:
			return
		if not frappe.db.exists("User", un):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(un)),
				frappe.ValidationError,
				title=_("Invalid user"),
			)

	def _validate_related_bid(self) -> None:
		bn = _strip(self.related_bid_submission)
		if not bn:
			return
		if not frappe.db.exists(BS, bn):
			frappe.throw(
				_("Bid Submission {0} does not exist.").format(frappe.bold(bn)),
				frappe.ValidationError,
				title=_("Invalid bid submission"),
			)

	def _validate_event_hash(self) -> None:
		if not _strip(self.event_hash):
			frappe.throw(
				_("Event Hash is required."),
				frappe.ValidationError,
				title=_("Invalid event hash"),
			)

	def on_trash(self):
		frappe.throw(
			_("Bid Opening Event Log cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
