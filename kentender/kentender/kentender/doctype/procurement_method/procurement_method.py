# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class ProcurementMethod(Document):
	def validate(self):
		self.display_label = code_title_label(self.method_code, self.method_name)
		self._validate_unique_method_code()

	def _validate_unique_method_code(self):
		if not self.method_code:
			return
		filters = {"method_code": self.method_code}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Procurement Method", filters, "name")
		if duplicate:
			frappe.throw(
				_("Method Code {0} is already used by {1}.").format(
					frappe.bold(self.method_code),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Method Code"),
			)
