# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

DS = "Deliberation Session"
RES = "Resolution Record"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class FollowUpAction(Document):
	def validate(self):
		if self.action_title is not None:
			self.action_title = self.action_title.strip()

		if not self.deliberation_session or not frappe.db.exists(DS, self.deliberation_session):
			frappe.throw(_("Deliberation Session not found."), frappe.ValidationError)

		if not self.resolution_record or not frappe.db.exists(RES, self.resolution_record):
			frappe.throw(_("Resolution Record not found."), frappe.ValidationError)

		res_session = frappe.db.get_value(RES, self.resolution_record, "deliberation_session")
		if res_session != self.deliberation_session:
			frappe.throw(_("Resolution Record must belong to this Deliberation Session."), frappe.ValidationError)

		if self.assigned_to_user and not frappe.db.exists("User", self.assigned_to_user):
			frappe.throw(_("Assigned user not found."), frappe.ValidationError)

		self.display_label = code_title_label(_strip(self.action_title) or "—", _strip(self.status) or "—")
