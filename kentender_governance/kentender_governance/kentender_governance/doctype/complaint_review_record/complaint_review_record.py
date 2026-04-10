# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

C = "Complaint"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ComplaintReviewRecord(Document):
	def validate(self):
		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if not self.reviewer_user or not frappe.db.exists("User", self.reviewer_user):
			frappe.throw(_("Reviewer user not found."), frappe.ValidationError)
		self.display_label = code_title_label(_strip(self.status) or "—", (_strip(self.review_summary) or "")[:40])
