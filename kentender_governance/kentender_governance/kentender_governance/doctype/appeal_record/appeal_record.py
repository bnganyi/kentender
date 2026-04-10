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


class AppealRecord(Document):
	def validate(self):
		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if not self.complaint_decision or not frappe.db.exists(CD, self.complaint_decision):
			frappe.throw(_("Complaint Decision not found."), frappe.ValidationError)
		dcc = frappe.db.get_value(CD, self.complaint_decision, "complaint")
		if dcc != self.complaint:
			frappe.throw(_("Complaint Decision must belong to this complaint."), frappe.ValidationError)
		if not self.appeal_submitted_by or not frappe.db.exists("User", self.appeal_submitted_by):
			frappe.throw(_("Appeal Submitted By user not found."), frappe.ValidationError)
		self.display_label = code_title_label(_strip(self.status) or "—", (_strip(self.appeal_summary) or "")[:50])
