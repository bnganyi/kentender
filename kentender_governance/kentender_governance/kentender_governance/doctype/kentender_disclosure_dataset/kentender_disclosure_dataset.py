# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-034: dataset definition for safe field exports."""

import json

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderDisclosureDataset(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.dataset_title is not None:
			self.dataset_title = self.dataset_title.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.dataset_title))

		if self.source_doctype and not frappe.db.exists("DocType", self.source_doctype):
			frappe.throw(_("Source DocType is not valid."), frappe.ValidationError)

		raw = self.field_allowlist_json or "[]"
		try:
			parsed = json.loads(raw)
		except json.JSONDecodeError:
			frappe.throw(_("Field allowlist must be valid JSON."), frappe.ValidationError)
		if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
			frappe.throw(_("Field allowlist JSON must be an array of strings."), frappe.ValidationError)
