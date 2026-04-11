# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-028: formal response to an audit query (optional finding context)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

AQ = "KenTender Audit Query"
AF = "KenTender Audit Finding"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAuditResponse(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.status) or "—")

		if not self.audit_query or not frappe.db.exists(AQ, self.audit_query):
			frappe.throw(_("Audit Query not found."), frappe.ValidationError)

		if self.responded_by_user and not frappe.db.exists("User", self.responded_by_user):
			frappe.throw(_("Responded By user not found."), frappe.ValidationError)

		if self.audit_finding:
			if not frappe.db.exists(AF, self.audit_finding):
				frappe.throw(_("Audit Finding not found."), frappe.ValidationError)
			fq = frappe.db.get_value(AF, self.audit_finding, "audit_query")
			if fq != self.audit_query:
				frappe.throw(_("Audit Finding must belong to the same Audit Query."), frappe.ValidationError)
