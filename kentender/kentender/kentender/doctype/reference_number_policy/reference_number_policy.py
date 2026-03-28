# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class ReferenceNumberPolicy(Document):
	def validate(self):
		self._validate_unique_policy_code()

	def _validate_unique_policy_code(self):
		if not self.policy_code:
			return
		filters = {"policy_code": self.policy_code}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Reference Number Policy", filters, "name")
		if duplicate:
			frappe.throw(
				_("Policy Code {0} is already used by {1}.").format(
					frappe.bold(self.policy_code),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Policy Code"),
			)
