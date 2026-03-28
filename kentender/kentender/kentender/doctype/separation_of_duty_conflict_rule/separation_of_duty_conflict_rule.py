# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


# Class name must match DocType with spaces removed only (Frappe get_controller).
class SeparationofDutyConflictRule(Document):
	def validate(self):
		self._validate_rule_code()
		self._validate_action_tokens()

	def _validate_rule_code(self):
		code = (self.rule_code or "").strip()
		if not code:
			return
		if code != self.rule_code:
			self.rule_code = code
		filters = {"rule_code": code}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Separation of Duty Conflict Rule", filters, "name")
		if existing:
			frappe.throw(
				_("Rule Code {0} is already used by {1}.").format(
					frappe.bold(code),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate rule code"),
			)

	def _validate_action_tokens(self):
		for field in ("source_action", "target_action"):
			val = (self.get(field) or "").strip()
			if not val:
				continue
			self.set(field, val)
