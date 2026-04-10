# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class KenTenderApprovalRouteTemplate(Document):
	def validate(self):
		orders = [int(r.step_order or 0) for r in self.get("steps") or []]
		if len(orders) != len(set(orders)):
			frappe.throw(_("Step order must be unique per template."), frappe.ValidationError)
