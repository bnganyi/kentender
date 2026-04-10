# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class InspectionTestResult(Document):
	def validate(self):
		if self.inspection_parameter_line and self.inspection_record:
			pl_ir = frappe.db.get_value(
				"Inspection Parameter Line",
				self.inspection_parameter_line,
				"inspection_record",
			)
			if pl_ir and pl_ir != self.inspection_record:
				frappe.throw(
					_("Inspection Parameter Line belongs to a different Inspection Record."),
					frappe.ValidationError,
				)
		pl_name = self.inspection_parameter_line
		if pl_name:
			pl_row = frappe.db.get_value(
				"Inspection Parameter Line",
				pl_name,
				("parameter_code", "parameter_name"),
				as_dict=True,
			)
			if pl_row:
				self.display_label = code_title_label(pl_row.parameter_code, pl_row.parameter_name)
		else:
			self.display_label = ""
