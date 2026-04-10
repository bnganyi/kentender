# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

DS = "Deliberation Session"
DAI = "Deliberation Agenda Item"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class DeliberationMinute(Document):
	def validate(self):
		if not self.deliberation_session or not frappe.db.exists(DS, self.deliberation_session):
			frappe.throw(_("Deliberation Session not found."), frappe.ValidationError)

		if not self.agenda_item or not frappe.db.exists(DAI, self.agenda_item):
			frappe.throw(_("Agenda Item not found."), frappe.ValidationError)

		ai_session = frappe.db.get_value(DAI, self.agenda_item, "deliberation_session")
		if ai_session != self.deliberation_session:
			frappe.throw(_("Agenda Item must belong to this Deliberation Session."), frappe.ValidationError)

		if self.recorded_by_user and not frappe.db.exists("User", self.recorded_by_user):
			frappe.throw(_("Recorded By user not found."), frappe.ValidationError)

		self.display_label = code_title_label(
			_strip(self.status) or "—",
			(_strip(self.minute_text) or "—")[:60],
		)
