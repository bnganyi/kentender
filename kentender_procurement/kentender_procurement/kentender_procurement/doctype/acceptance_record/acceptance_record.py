# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

IR = "Inspection Record"


class AcceptanceRecord(Document):
	def validate(self):
		self.business_id = (self.business_id or "").strip()
		self.display_label = code_title_label(self.business_id, self.acceptance_decision or "")

		if self.inspection_record and self.contract:
			ir_contract = frappe.db.get_value(IR, self.inspection_record, "contract")
			if ir_contract and self.contract != ir_contract:
				frappe.throw(_("Contract must match the Inspection Record contract."), frappe.ValidationError)
