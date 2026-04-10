# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class InspectionMethodTemplate(Document):
	def validate(self):
		if self.template_code is not None:
			self.template_code = self.template_code.strip()
		if self.template_name is not None:
			self.template_name = self.template_name.strip()
		self.display_label = code_title_label(self.template_code, self.template_name)
