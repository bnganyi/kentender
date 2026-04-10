# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

IR = "Inspection Record"


class ReinspectionRecord(Document):
	def validate(self):
		self.display_label = code_title_label(
			self.inspection_record or "",
			(self.trigger_reason or "").replace("\n", " ")[:80],
		)

		if self.inspection_record and self.contract:
			ir_contract = frappe.db.get_value(IR, self.inspection_record, "contract")
			if ir_contract and self.contract != ir_contract:
				frappe.throw(_("Contract must match the Inspection Record contract."), frappe.ValidationError)

		if self.linked_followup_inspection:
			fc = frappe.db.get_value(IR, self.linked_followup_inspection, "contract")
			if fc and fc != self.contract:
				frappe.throw(_("Linked follow-up inspection must belong to the same Contract."), frappe.ValidationError)
