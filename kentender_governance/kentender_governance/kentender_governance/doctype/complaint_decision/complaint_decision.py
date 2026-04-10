# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

C = "Complaint"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ComplaintDecision(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if not self.decided_by_user or not frappe.db.exists("User", self.decided_by_user):
			frappe.throw(_("Decided By user not found."), frappe.ValidationError)
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.decision_result) or "—")
