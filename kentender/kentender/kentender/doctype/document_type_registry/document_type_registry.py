# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class DocumentTypeRegistry(Document):
	def validate(self):
		self._validate_unique_document_type_code()

	def _validate_unique_document_type_code(self):
		if not self.document_type_code:
			return
		filters = {"document_type_code": self.document_type_code}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Document Type Registry", filters, "name")
		if duplicate:
			frappe.throw(
				_("Document Type Code {0} is already used by {1}.").format(
					frappe.bold(self.document_type_code),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Document Type Code"),
			)
