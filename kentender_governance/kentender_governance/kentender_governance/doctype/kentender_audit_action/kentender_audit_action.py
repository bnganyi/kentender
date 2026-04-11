# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-029: corrective action tied to query, finding, and optional response."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

AQ = "KenTender Audit Query"
AF = "KenTender Audit Finding"
AR = "KenTender Audit Response"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAuditAction(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.action_title is not None:
			self.action_title = self.action_title.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.action_title))

		if not self.audit_query or not frappe.db.exists(AQ, self.audit_query):
			frappe.throw(_("Audit Query not found."), frappe.ValidationError)

		if not self.audit_finding or not frappe.db.exists(AF, self.audit_finding):
			frappe.throw(_("Audit Finding not found."), frappe.ValidationError)

		fq = frappe.db.get_value(AF, self.audit_finding, "audit_query")
		if fq != self.audit_query:
			frappe.throw(_("Audit Finding must belong to the selected Audit Query."), frappe.ValidationError)

		if self.audit_response:
			if not frappe.db.exists(AR, self.audit_response):
				frappe.throw(_("Audit Response not found."), frappe.ValidationError)
			rq = frappe.db.get_value(AR, self.audit_response, "audit_query")
			if rq != self.audit_query:
				frappe.throw(_("Audit Response must belong to the same Audit Query."), frappe.ValidationError)

		if self.assigned_to_user and not frappe.db.exists("User", self.assigned_to_user):
			frappe.throw(_("Assigned user not found."), frappe.ValidationError)
