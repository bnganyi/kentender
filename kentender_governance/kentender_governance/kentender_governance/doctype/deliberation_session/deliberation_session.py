# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime

from kentender.utils.display_label import code_title_label

PE = "Procuring Entity"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class DeliberationSession(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.session_title is not None:
			self.session_title = self.session_title.strip()
		if self.location is not None and isinstance(self.location, str):
			self.location = self.location.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.session_title))

		if self.procuring_entity and not frappe.db.exists(PE, self.procuring_entity):
			frappe.throw(_("Procuring Entity not found."), frappe.ValidationError)

		ldt = _strip(self.linked_doctype)
		ldn = _strip(self.linked_docname)
		if ldt or ldn:
			if not ldt or not ldn:
				frappe.throw(_("Linked DocType and Linked Document must both be set."), frappe.ValidationError)
			if not frappe.db.exists("DocType", ldt):
				frappe.throw(_("Linked DocType is not valid."), frappe.ValidationError)
			if not frappe.db.exists(ldt, ldn):
				frappe.throw(_("Linked document does not exist."), frappe.ValidationError)

		ast = self.actual_start_datetime
		aen = self.actual_end_datetime
		if ast and aen and get_datetime(aen) < get_datetime(ast):
			frappe.throw(_("Actual End cannot be before Actual Start."), frappe.ValidationError)
