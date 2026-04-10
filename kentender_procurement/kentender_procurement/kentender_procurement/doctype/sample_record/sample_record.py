# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class SampleRecord(Document):
	def validate(self):
		self.sample_code = (self.sample_code or "").strip()
		st = (self.sample_type or "").strip()
		self.display_label = code_title_label(self.sample_code, st)
