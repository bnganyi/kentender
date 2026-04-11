# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-014: KenTender Asset Category master (distinct from ERPNext Asset Category)."""

import frappe
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAssetCategory(Document):
	def validate(self):
		if self.category_code is not None:
			self.category_code = self.category_code.strip()
		if self.category_name is not None:
			self.category_name = self.category_name.strip()
		self.display_label = code_title_label(_strip(self.category_code), _strip(self.category_name))
