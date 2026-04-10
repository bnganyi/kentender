# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

C = "Complaint"
CD = "Complaint Decision"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ComplaintAction(Document):
	def validate(self):
		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if not self.decision or not frappe.db.exists(CD, self.decision):
			frappe.throw(_("Complaint Decision not found."), frappe.ValidationError)
		dc = frappe.db.get_value(CD, self.decision, "complaint")
		if dc != self.complaint:
			frappe.throw(_("Complaint Decision must belong to this complaint."), frappe.ValidationError)
		if self.executed_by_user and not frappe.db.exists("User", self.executed_by_user):
			frappe.throw(_("Executed By user not found."), frappe.ValidationError)

		tdt = _strip(self.target_doctype)
		tdn = _strip(self.target_docname)
		if tdt or tdn:
			if not tdt or not tdn:
				frappe.throw(_("Target DocType and Target Document must both be set."), frappe.ValidationError)
			if not frappe.db.exists("DocType", tdt):
				frappe.throw(_("Target DocType is not valid."), frappe.ValidationError)
			if not frappe.db.exists(tdt, tdn):
				frappe.throw(_("Target document does not exist."), frappe.ValidationError)

		self.display_label = code_title_label(_strip(self.action_type) or "—", _strip(self.status) or "—")
