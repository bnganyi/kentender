# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-002: item stocked at a store (unique per store + item_code)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

S = "Store"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class StoreItem(Document):
	def validate(self):
		if not self.store or not frappe.db.exists(S, self.store):
			frappe.throw(_("Store not found."), frappe.ValidationError)

		if self.item_code is not None:
			self.item_code = self.item_code.strip()
		if self.item_name is not None:
			self.item_name = self.item_name.strip()
		if self.unit_of_measure is not None:
			self.unit_of_measure = self.unit_of_measure.strip()

		ic = _strip(self.item_code)
		if not ic:
			frappe.throw(_("Item Code is required."), frappe.ValidationError)

		self.display_label = code_title_label(ic, _strip(self.item_name) or "—")

		existing = frappe.db.get_value(
			"Store Item",
			{"store": self.store, "item_code": ic},
			"name",
		)
		if existing and existing != self.name:
			frappe.throw(
				_("Item Code {0} already exists for this store.").format(ic),
				frappe.ValidationError,
			)
