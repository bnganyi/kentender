# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Global append-only approval audit row (WF-003)."""

import frappe
from frappe import _
from frappe.model.document import Document


class KenTenderApprovalAction(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(
				_("KenTender Approval Action is append-only; existing rows cannot be changed."),
				frappe.ValidationError,
			)
