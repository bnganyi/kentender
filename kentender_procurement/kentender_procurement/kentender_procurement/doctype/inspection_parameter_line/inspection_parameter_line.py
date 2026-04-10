# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class InspectionParameterLine(Document):
	def validate(self):
		self.parameter_code = (self.parameter_code or "").strip()
		self.parameter_name = (self.parameter_name or "").strip()
		self.display_label = code_title_label(self.parameter_code, self.parameter_name)

		tt = (self.tolerance_type or "").strip() or "None"
		if tt == "MinMax":
			if self.expected_min_value is not None and self.expected_max_value is not None:
				if float(self.expected_min_value) > float(self.expected_max_value):
					frappe.throw(_("Expected Min Value cannot be greater than Expected Max Value."), frappe.ValidationError)
		elif tt == "None":
			pass
