# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

DS = "Deliberation Session"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class DeliberationAgendaItem(Document):
	def validate(self):
		if self.title is not None:
			self.title = self.title.strip()

		self.display_label = code_title_label(str(self.item_no or ""), _strip(self.title) or "—")

		if not self.deliberation_session or not frappe.db.exists(DS, self.deliberation_session):
			frappe.throw(_("Deliberation Session not found."), frappe.ValidationError)

		existing = frappe.db.get_value(
			"Deliberation Agenda Item",
			{"deliberation_session": self.deliberation_session, "item_no": self.item_no},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(_("Item No must be unique within the deliberation session."), frappe.ValidationError)

		ldt = _strip(self.linked_doctype)
		ldn = _strip(self.linked_docname)
		if ldt or ldn:
			if not ldt or not ldn:
				frappe.throw(_("Linked DocType and Linked Document must both be set."), frappe.ValidationError)
			if not frappe.db.exists("DocType", ldt):
				frappe.throw(_("Linked DocType is not valid."), frappe.ValidationError)
			if not frappe.db.exists(ldt, ldn):
				frappe.throw(_("Linked document does not exist."), frappe.ValidationError)
