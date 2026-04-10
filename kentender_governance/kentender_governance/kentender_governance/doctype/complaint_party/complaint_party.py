# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

C = "Complaint"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ComplaintParty(Document):
	def validate(self):
		if self.party_name is not None:
			self.party_name = self.party_name.strip()
		self.display_label = code_title_label(_strip(self.party_role) or "—", _strip(self.party_name) or "—")
		if not self.complaint or not frappe.db.exists(C, self.complaint):
			frappe.throw(_("Complaint not found."), frappe.ValidationError)
		if self.supplier and frappe.db.exists("DocType", "Supplier") and not frappe.db.exists("Supplier", self.supplier):
			frappe.throw(_("Supplier not found."), frappe.ValidationError)
