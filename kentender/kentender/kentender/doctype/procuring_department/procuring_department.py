# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class ProcuringDepartment(Document):
	def validate(self):
		self.display_label = code_title_label(self.department_code, self.department_name)
		self._validate_unique_department_code_per_entity()
		self._validate_parent_department()

	def _identity(self) -> str:
		"""Stable identity for hierarchy checks (name set from autoname before insert completes)."""
		return (self.name or "").strip()

	def _validate_unique_department_code_per_entity(self):
		if not self.department_code or not self.procuring_entity:
			return
		filters = {
			"department_code": self.department_code,
			"procuring_entity": self.procuring_entity,
		}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Procuring Department", filters, "name")
		if duplicate:
			frappe.throw(
				_("Department Code {0} already exists for entity {1} ({2}).").format(
					frappe.bold(self.department_code),
					frappe.bold(self.procuring_entity),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Department Code"),
			)

	def _validate_parent_department(self):
		if not self.parent_department:
			return

		identity = self._identity()
		if self.parent_department == identity:
			frappe.throw(
				_("A department cannot be its own parent."),
				frappe.ValidationError,
				title=_("Invalid Parent"),
			)

		parent_entity = frappe.db.get_value(
			"Procuring Department", self.parent_department, "procuring_entity"
		)
		if not parent_entity:
			frappe.throw(
				_("Parent department not found."),
				frappe.ValidationError,
				title=_("Invalid Parent"),
			)
		if parent_entity != self.procuring_entity:
			frappe.throw(
				_("Parent department must belong to the same procuring entity."),
				frappe.ValidationError,
				title=_("Invalid Parent"),
			)

		visited = set()
		current = self.parent_department
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
				"Procuring Department", current, "parent_department"
			)
