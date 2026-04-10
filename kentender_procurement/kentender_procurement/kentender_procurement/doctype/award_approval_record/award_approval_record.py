# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Award Approval Record — approval trail for award decisions (PROC-STORY-074)."""

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


class AwardApprovalRecord(Document):
	def validate(self):
		if self.comments and isinstance(self.comments, str):
			self.comments = self.comments.strip()
		self._validate_award_decision()
		self._validate_approver_user()
		self._validate_approver_role()
		self._set_display_label()

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

	def _validate_approver_user(self) -> None:
		un = _strip(self.approver_user)
		if not un:
			return
		if not frappe.db.exists(USER, un):
			frappe.throw(
				_("User {0} does not exist.").format(frappe.bold(un)),
				frappe.ValidationError,
				title=_("Invalid approver user"),
			)

	def _validate_approver_role(self) -> None:
		rn = _strip(self.approver_role)
		if not rn:
			return
		if not frappe.db.exists(ROLE, rn):
			frappe.throw(
				_("Role {0} does not exist.").format(frappe.bold(rn)),
				frappe.ValidationError,
				title=_("Invalid approver role"),
			)

	def _set_display_label(self) -> None:
		self.display_label = code_title_label(_strip(self.action_type) or "—", _strip(self.award_decision)[:12] or "—")
