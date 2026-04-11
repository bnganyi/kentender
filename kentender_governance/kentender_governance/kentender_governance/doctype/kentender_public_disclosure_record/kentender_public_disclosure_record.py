# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-033: staged public disclosure row."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderPublicDisclosureRecord(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.disclosure_stage) or "—")

		if self.related_doctype and not frappe.db.exists("DocType", self.related_doctype):
			frappe.throw(_("Related DocType is not valid."), frappe.ValidationError)
		if self.related_docname and not frappe.db.exists(self.related_doctype, self.related_docname):
			frappe.throw(_("Related document not found."), frappe.ValidationError)

		if self.published_by_user and not frappe.db.exists("User", self.published_by_user):
			frappe.throw(_("Published By user not found."), frappe.ValidationError)
