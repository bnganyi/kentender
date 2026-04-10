# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-003: Goods Receipt Note — bridge contract / inspection / acceptance to store (no stock posting)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

PC = "Procurement Contract"
IR = "Inspection Record"
AR = "Acceptance Record"
S = "Store"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class GoodsReceiptNote(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		if self.supplier is not None:
			self.supplier = self.supplier.strip()

		self.display_label = code_title_label(_strip(self.business_id), _strip(self.supplier) or "—")

		if not frappe.db.exists(PC, self.contract):
			frappe.throw(_("Procurement Contract not found."), frappe.ValidationError)
		if not frappe.db.exists(S, self.store):
			frappe.throw(_("Store not found."), frappe.ValidationError)
		if self.received_by_user and not frappe.db.exists("User", self.received_by_user):
			frappe.throw(_("Received By user not found."), frappe.ValidationError)
		if self.currency and not frappe.db.exists("Currency", self.currency):
			frappe.throw(_("Currency not found."), frappe.ValidationError)

		if self.inspection_reference:
			if not frappe.db.exists(IR, self.inspection_reference):
				frappe.throw(_("Inspection Record not found."), frappe.ValidationError)
			ir_contract = frappe.db.get_value(IR, self.inspection_reference, "contract")
			if ir_contract != self.contract:
				frappe.throw(
					_("Inspection Record must belong to the same Procurement Contract as this GRN."),
					frappe.ValidationError,
				)

		if self.acceptance_reference:
			if not frappe.db.exists(AR, self.acceptance_reference):
				frappe.throw(_("Acceptance Record not found."), frappe.ValidationError)
			ar_contract = frappe.db.get_value(AR, self.acceptance_reference, "contract")
			if ar_contract != self.contract:
				frappe.throw(
					_("Acceptance Record must belong to the same Procurement Contract as this GRN."),
					frappe.ValidationError,
				)
			ar_ir = frappe.db.get_value(AR, self.acceptance_reference, "inspection_record")
			if self.inspection_reference and ar_ir and ar_ir != self.inspection_reference:
				frappe.throw(
					_("Acceptance Record must reference the same Inspection Record when both are set."),
					frappe.ValidationError,
				)

		if not self.get("items"):
			frappe.throw(_("At least one line item is required."), frappe.ValidationError)

		total = 0.0
		for row in self.items:
			self._validate_grn_line(row)
			qty = flt(row.quantity)
			rate = flt(row.unit_rate)
			amt = flt(row.amount)
			if amt:
				pass
			elif qty and rate:
				amt = qty * rate
				row.amount = amt
			else:
				row.amount = 0.0
				amt = 0.0
			total += flt(row.amount)

		self.total_received_value = total

	def _validate_grn_line(self, row) -> None:
		if not _strip(row.item_code):
			frappe.throw(_("Item Code is required on each line."), frappe.ValidationError)
		if flt(row.quantity) <= 0:
			frappe.throw(_("Quantity must be greater than zero."), frappe.ValidationError)
