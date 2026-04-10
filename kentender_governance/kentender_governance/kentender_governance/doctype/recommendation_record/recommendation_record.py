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


class RecommendationRecord(Document):
	def validate(self):
		if not self.deliberation_session or not frappe.db.exists(DS, self.deliberation_session):
			frappe.throw(_("Deliberation Session not found."), frappe.ValidationError)

		if not self.agenda_item or not frappe.db.exists(DAI, self.agenda_item):
			frappe.throw(_("Agenda Item not found."), frappe.ValidationError)

		ai_session = frappe.db.get_value(DAI, self.agenda_item, "deliberation_session")
		if ai_session != self.deliberation_session:
			frappe.throw(_("Agenda Item must belong to this Deliberation Session."), frappe.ValidationError)

		if self.recommended_by_user and not frappe.db.exists("User", self.recommended_by_user):
			frappe.throw(_("Recommended By user not found."), frappe.ValidationError)

		rdt = _strip(self.related_doctype)
		rdn = _strip(self.related_docname)
		if rdt or rdn:
			if not rdt or not rdn:
				frappe.throw(_("Related DocType and Related Document must both be set."), frappe.ValidationError)
			if not frappe.db.exists("DocType", rdt):
				frappe.throw(_("Related DocType is not valid."), frappe.ValidationError)
			if not frappe.db.exists(rdt, rdn):
				frappe.throw(_("Related document does not exist."), frappe.ValidationError)

		self.display_label = code_title_label(_strip(self.recommendation_type) or "—", _strip(self.status) or "—")
