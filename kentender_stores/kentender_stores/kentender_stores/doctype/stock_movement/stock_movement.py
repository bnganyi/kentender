# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-006: inter-store stock movement."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

S = "Store"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class StockMovement(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		self.display_label = code_title_label(_strip(self.business_id), "Movement")

		if not frappe.db.exists(S, self.from_store):
			frappe.throw(_("From Store not found."), frappe.ValidationError)
		if not frappe.db.exists(S, self.to_store):
			frappe.throw(_("To Store not found."), frappe.ValidationError)
		if self.from_store == self.to_store:
			frappe.throw(_("From Store and To Store must be different."), frappe.ValidationError)
		if self.initiated_by_user and not frappe.db.exists("User", self.initiated_by_user):
			frappe.throw(_("Initiated By user not found."), frappe.ValidationError)

		if not self.get("items"):
			frappe.throw(_("At least one line item is required."), frappe.ValidationError)

		for row in self.items:
			if not _strip(row.item_code):
				frappe.throw(_("Item Code is required on each line."), frappe.ValidationError)
			if flt(row.quantity) <= 0:
				frappe.throw(_("Quantity must be greater than zero on each line."), frappe.ValidationError)
