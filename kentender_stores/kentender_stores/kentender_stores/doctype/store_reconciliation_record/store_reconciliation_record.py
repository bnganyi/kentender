# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-008: physical count vs book on hand (lines carry variance)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

S = "Store"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class StoreReconciliationRecord(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		self.display_label = code_title_label(_strip(self.business_id), "Reconciliation")

		if not frappe.db.exists(S, self.store):
			frappe.throw(_("Store not found."), frappe.ValidationError)
		if self.counted_by_user and not frappe.db.exists("User", self.counted_by_user):
			frappe.throw(_("Counted By user not found."), frappe.ValidationError)

		if not self.get("items"):
			frappe.throw(_("At least one line item is required."), frappe.ValidationError)

		for row in self.items:
			if not _strip(row.item_code):
				frappe.throw(_("Item Code is required on each line."), frappe.ValidationError)
			row.variance_quantity = flt(row.counted_quantity) - flt(row.book_quantity)
