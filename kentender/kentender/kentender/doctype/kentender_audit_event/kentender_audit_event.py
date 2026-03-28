# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class KenTenderAuditEvent(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(
				_("KenTender Audit Event records cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)

	def on_trash(self):
		frappe.throw(
			_("KenTender Audit Event records cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
