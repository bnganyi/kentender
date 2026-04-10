# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award Return Record — return award for rework (PROC-STORY-079)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

AWARD_DECISION = "Award Decision"
USER = "User"
ROLE = "Role"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class AwardReturnRecord(Document):
	def validate(self):
		self._normalize_text()
		self._validate_award_decision()
		self._validate_returned_by_user()
		self._validate_returned_by_role()
		self._set_display_label()

	def _normalize_text(self) -> None:
		pass

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

	def _validate_returned_by_user(self) -> None:
		un = _strip(self.returned_by_user)
		if not un:
			return
		if not frappe.db.exists(USER, un):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(un)),
				frappe.ValidationError,
				title=_("Invalid user"),
			)

	def _validate_returned_by_role(self) -> None:
		rn = _strip(self.returned_by_role)
		if not rn:
			return
		if not frappe.db.exists(ROLE, rn):
			frappe.throw(
				_("Role {0} does not exist.").format(frappe.bold(rn)),
				frappe.ValidationError,
				title=_("Invalid role"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.return_type) or "—", _strip(self.status) or "—")
