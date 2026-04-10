# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-007: materials issued from a store."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

S = "Store"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class StoreIssue(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		self.display_label = code_title_label(_strip(self.business_id), "Issue")

		if not frappe.db.exists(S, self.store):
			frappe.throw(_("Store not found."), frappe.ValidationError)
		if self.issued_to_user and not frappe.db.exists("User", self.issued_to_user):
			frappe.throw(_("Issued To user not found."), frappe.ValidationError)

		if not self.get("items"):
			frappe.throw(_("At least one line item is required."), frappe.ValidationError)

		for row in self.items:
			if not _strip(row.item_code):
				frappe.throw(_("Item Code is required on each line."), frappe.ValidationError)
			if flt(row.quantity) <= 0:
				frappe.throw(_("Quantity must be greater than zero on each line."), frappe.ValidationError)
