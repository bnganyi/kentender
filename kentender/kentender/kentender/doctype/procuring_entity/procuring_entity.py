# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class ProcuringEntity(Document):
	def validate(self):
		self._validate_unique_entity_code()
		self._validate_parent_entity()

	def _identity(self) -> str:
		"""Stable identity for hierarchy checks (name equals entity_code after save)."""
		return (self.name or self.entity_code or "").strip()

	def _validate_unique_entity_code(self):
		if not self.entity_code:
			return
		filters = {"entity_code": self.entity_code}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Procuring Entity", filters, "name")
		if duplicate:
			frappe.throw(
				_("Entity Code {0} is already used by {1}.").format(
					frappe.bold(self.entity_code), frappe.bold(duplicate)
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Entity Code"),
			)

	def _validate_parent_entity(self):
		if not self.parent_entity:
			return

		identity = self._identity()
		if self.parent_entity == identity:
			frappe.throw(
				_("An entity cannot be its own parent."),
				frappe.ValidationError,
				title=_("Invalid Parent"),
			)

		visited = set()
		current = self.parent_entity
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
			current = frappe.db.get_value("Procuring Entity", current, "parent_entity")
