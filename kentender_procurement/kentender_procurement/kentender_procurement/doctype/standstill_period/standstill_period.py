# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Standstill Period — post-award waiting period (PROC-STORY-077)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from kentender.utils.display_label import code_title_label

AWARD_DECISION = "Award Decision"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class StandstillPeriod(Document):
	def validate(self):
		self._normalize_text()
		self._validate_award_decision()
		self._validate_datetimes()
		self._set_display_label()

	def _normalize_text(self) -> None:
		for fn in ("hold_reason", "remarks"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_award_decision(self) -> None:
		an = _strip(self.award_decision)
		if not an:
			return
		if not frappe.db.exists(AWARD_DECISION, an):
			frappe.throw(
				_("Award Decision {0} does not exist.").format(frappe.bold(an)),
				frappe.ValidationError,
				title=_("Invalid award decision"),
			)

	def _validate_datetimes(self) -> None:
		s = self.start_datetime
		e = self.end_datetime
		if not s or not e:
			return
		ds = get_datetime(s)
		de = get_datetime(e)
		if de < ds:
			frappe.throw(
				_("End Datetime cannot be before Start Datetime."),
				frappe.ValidationError,
				title=_("Invalid dates"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.award_decision)[:12] or "—", _strip(self.status) or "—")
