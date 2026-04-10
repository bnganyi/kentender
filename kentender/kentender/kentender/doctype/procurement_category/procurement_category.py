# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class ProcurementCategory(Document):
	def validate(self):
		self.display_label = code_title_label(self.category_code, self.category_name)
		self._validate_unique_category_code()
		self._validate_parent_category()

	def _identity(self) -> str:
		return (self.name or "").strip()

	def _validate_unique_category_code(self):
		if not self.category_code:
			return
		filters = {"category_code": self.category_code}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Procurement Category", filters, "name")
		if duplicate:
			frappe.throw(
				_("Category Code {0} is already used by {1}.").format(
					frappe.bold(self.category_code),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Category Code"),
			)

	def _validate_parent_category(self):
		if not self.parent_category:
			return

		identity = self._identity()
		if self.parent_category == identity:
			frappe.throw(
				_("A category cannot be its own parent."),
				frappe.ValidationError,
				title=_("Invalid Parent"),
			)

		if not frappe.db.exists("Procurement Category", self.parent_category):
			frappe.throw(
				_("Parent category not found."),
				frappe.ValidationError,
				title=_("Invalid Parent"),
			)

		visited = set()
		current = self.parent_category
		while current:
			if current == identity:
				frappe.throw(
					_("Parent hierarchy would create a circular reference."),
					frappe.ValidationError,
					title=_("Circular Hierarchy"),
				)
			if current in visited:
				frappe.throw(
					_("Parent hierarchy contains a cycle."),
					frappe.ValidationError,
					title=_("Circular Hierarchy"),
				)
			visited.add(current)
			current = frappe.db.get_value(
				"Procurement Category", current, "parent_category"
			)
