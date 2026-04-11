# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-027: audit finding linked to an audit query."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

AQ = "KenTender Audit Query"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAuditFinding(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.finding_title is not None:
			self.finding_title = self.finding_title.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.finding_title))

		if not self.audit_query or not frappe.db.exists(AQ, self.audit_query):
			frappe.throw(_("Audit Query not found."), frappe.ValidationError)

		if self.identified_by_user and not frappe.db.exists("User", self.identified_by_user):
			frappe.throw(_("Identified By user not found."), frappe.ValidationError)
