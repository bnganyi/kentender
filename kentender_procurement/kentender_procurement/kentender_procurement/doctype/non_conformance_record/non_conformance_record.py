# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

IR = "Inspection Record"
PC = "Procurement Contract"
PCM = "Procurement Contract Milestone"
PCD = "Procurement Contract Deliverable"


class NonConformanceRecord(Document):
	def validate(self):
		self.business_id = (self.business_id or "").strip()
		self.issue_title = (self.issue_title or "").strip()
		self.display_label = code_title_label(self.business_id, self.issue_title)

		if not self.inspection_record or not self.contract:
			return

		ir_contract = frappe.db.get_value(IR, self.inspection_record, "contract")
		if ir_contract and self.contract != ir_contract:
			frappe.throw(_("Contract must match the Inspection Record contract."), frappe.ValidationError)

		if self.contract_milestone:
			ms = frappe.db.get_value(PCM, self.contract_milestone, ("procurement_contract",), as_dict=True)
			if ms and ms.procurement_contract != self.contract:
				frappe.throw(_("Contract Milestone must belong to the selected Contract."), frappe.ValidationError)

		if self.contract_deliverable:
			dd = frappe.db.get_value(
				PCD,
				self.contract_deliverable,
				("procurement_contract", "contract_milestone"),
				as_dict=True,
			)
			if dd:
				if dd.procurement_contract != self.contract:
					frappe.throw(_("Contract Deliverable must belong to the selected Contract."), frappe.ValidationError)
				if self.contract_milestone and dd.contract_milestone and dd.contract_milestone != self.contract_milestone:
					frappe.throw(
						_("Contract Deliverable must align with the selected Contract Milestone when both are set."),
						frappe.ValidationError,
					)
