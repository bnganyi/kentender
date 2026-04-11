# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-026: structured audit query (KenTender name avoids generic collisions)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAuditQuery(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.query_title is not None:
			self.query_title = self.query_title.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.query_title))

		if self.raised_by_user and not frappe.db.exists("User", self.raised_by_user):
			frappe.throw(_("Raised By user not found."), frappe.ValidationError)

		if self.related_doctype and not frappe.db.exists("DocType", self.related_doctype):
			frappe.throw(_("Related DocType is not valid."), frappe.ValidationError)

		if self.related_docname and not self.related_doctype:
			frappe.throw(_("Set Related DocType when Related Document is provided."), frappe.ValidationError)

		if self.related_doctype and self.related_docname:
			if not frappe.db.exists(self.related_doctype, self.related_docname):
				frappe.throw(_("Related document not found."), frappe.ValidationError)
