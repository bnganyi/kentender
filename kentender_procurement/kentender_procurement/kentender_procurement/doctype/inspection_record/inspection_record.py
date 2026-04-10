# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class InspectionRecord(Document):
	def validate(self):
		self.business_id = (self.business_id or "").strip()
		if self.inspection_title is not None:
			self.inspection_title = self.inspection_title.strip()
		self.display_label = code_title_label(self.business_id, self.inspection_title)

		if self.contract:
			pc_entity = frappe.db.get_value("Procurement Contract", self.contract, "procuring_entity")
			if pc_entity and self.procuring_entity and self.procuring_entity != pc_entity:
				frappe.throw(
					_("Procuring Entity must match the selected Contract."),
					frappe.ValidationError,
				)

		if self.contract_milestone:
			ms_pc = frappe.db.get_value("Procurement Contract Milestone", self.contract_milestone, "procurement_contract")
			if ms_pc and self.contract and ms_pc != self.contract:
				frappe.throw(
					_("Contract Milestone must belong to the selected Contract."),
					frappe.ValidationError,
				)

		if self.contract_deliverable:
			dd = frappe.db.get_value(
				"Procurement Contract Deliverable",
				self.contract_deliverable,
				("procurement_contract", "contract_milestone"),
				as_dict=True,
			)
			if dd:
				if self.contract and dd.procurement_contract != self.contract:
					frappe.throw(
						_("Contract Deliverable must belong to the selected Contract."),
						frappe.ValidationError,
					)
				if self.contract_milestone and dd.contract_milestone and dd.contract_milestone != self.contract_milestone:
					frappe.throw(
						_("Contract Deliverable must align with the selected Contract Milestone when both are set."),
						frappe.ValidationError,
					)

		st = self.inspection_scope_type or ""
		if st == "Milestone" and not self.contract_milestone:
			frappe.throw(_("Contract Milestone is required for this inspection scope."), frappe.ValidationError)
		if st == "Deliverable" and not self.contract_deliverable:
			frappe.throw(_("Contract Deliverable is required for this inspection scope."), frappe.ValidationError)
		if st == "Milestone and Deliverable":
			if not self.contract_milestone or not self.contract_deliverable:
				frappe.throw(
					_("Both Contract Milestone and Contract Deliverable are required for this inspection scope."),
					frappe.ValidationError,
				)

		for row in self.get("checklist_lines") or []:
			self._validate_checklist_line_row(row)

	def _validate_checklist_line_row(self, row):
		if not self.contract:
			return
		if row.related_milestone:
			ms_pc = frappe.db.get_value("Procurement Contract Milestone", row.related_milestone, "procurement_contract")
			if ms_pc != self.contract:
				frappe.throw(
					_("Checklist line {0}: Related Milestone must belong to the inspection contract.").format(
						row.idx or row.check_item_no
					),
					frappe.ValidationError,
				)
		if row.related_deliverable:
			dd_pc = frappe.db.get_value(
				"Procurement Contract Deliverable", row.related_deliverable, "procurement_contract"
			)
			if dd_pc != self.contract:
				frappe.throw(
					_("Checklist line {0}: Related Deliverable must belong to the inspection contract.").format(
						row.idx or row.check_item_no
					),
					frappe.ValidationError,
				)
