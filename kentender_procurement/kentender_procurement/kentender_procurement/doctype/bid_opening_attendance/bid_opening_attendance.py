# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid Opening Session attendance row (PROC-STORY-049)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

SESSION = "Bid Opening Session"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class BidOpeningAttendance(Document):
	def validate(self):
		self._normalize_text()
		self._set_display_label()
		self._validate_session()
		self._validate_user()
		self._validate_internal_or_external()

	def _normalize_text(self) -> None:
		self.attendee_name = _strip(self.attendee_name)
		self.supplier = _strip(self.supplier)
		self.remarks = _strip(self.remarks)

	def _set_display_label(self) -> None:
		who = _strip(self.attendee_user) or self.attendee_name or _("Attendee")
		self.display_label = code_title_label(who, _strip(self.bid_opening_session) or "—")

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

	def _validate_user(self) -> None:
		u = _strip(self.attendee_user)
		if not u:
			return
		if not frappe.db.exists("User", u):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(u)),
				frappe.ValidationError,
				title=_("Invalid user"),
			)

	def _validate_internal_or_external(self) -> None:
		"""Either link an internal user or provide a display name for external/manual attendees."""
		if _strip(self.attendee_user):
			return
		if not self.attendee_name:
			frappe.throw(
				_("Set **Attendee User** for internal attendees, or **Attendee Name** for external/manual attendees."),
				frappe.ValidationError,
				title=_("Attendee identity"),
			)
