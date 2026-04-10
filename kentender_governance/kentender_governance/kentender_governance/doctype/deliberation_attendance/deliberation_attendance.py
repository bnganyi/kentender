# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

DS = "Deliberation Session"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class DeliberationAttendance(Document):
	def validate(self):
		self.attendee_name = _strip(self.attendee_name)
		if not self.attendee_name:
			frappe.throw(_("Attendee Name is required."), frappe.ValidationError)

		if not self.deliberation_session or not frappe.db.exists(DS, self.deliberation_session):
			frappe.throw(_("Deliberation Session not found."), frappe.ValidationError)

		if self.user and not frappe.db.exists("User", self.user):
			frappe.throw(_("User not found."), frappe.ValidationError)

		self.display_label = code_title_label(_strip(self.attendee_name)[:80], _strip(self.role_type) or "—")
