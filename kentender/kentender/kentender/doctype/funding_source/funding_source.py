# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class FundingSource(Document):
	def validate(self):
		self.display_label = code_title_label(self.funding_source_code, self.funding_source_name)
		self._validate_unique_funding_source_code()

	def _validate_unique_funding_source_code(self):
		if not self.funding_source_code:
			return
		filters = {"funding_source_code": self.funding_source_code}
		if self.name:
			filters["name"] = ("!=", self.name)
		duplicate = frappe.db.get_value("Funding Source", filters, "name")
		if duplicate:
			frappe.throw(
				_("Funding Source Code {0} is already used by {1}.").format(
					frappe.bold(self.funding_source_code),
					frappe.bold(duplicate),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Funding Source Code"),
			)
