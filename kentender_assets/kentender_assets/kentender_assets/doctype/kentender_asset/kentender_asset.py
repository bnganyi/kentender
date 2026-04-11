# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-013: KenTender Asset register (procurement origin; name distinct from ERPNext Asset)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

PC = "Procurement Contract"
GRN = "Goods Receipt Note"
CAT = "KenTender Asset Category"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAsset(Document):
	def validate(self):
		if self.asset_code is not None:
			self.asset_code = self.asset_code.strip()
		if self.asset_name is not None:
			self.asset_name = self.asset_name.strip()
		if self.supplier is not None:
			self.supplier = self.supplier.strip()
		if self.current_location is not None:
			self.current_location = self.current_location.strip()

		self.display_label = code_title_label(_strip(self.asset_code), _strip(self.asset_name))

		if not frappe.db.exists(CAT, self.asset_category):
			frappe.throw(_("KenTender Asset Category not found."), frappe.ValidationError)

		if not self.source_contract and not self.source_grn:
			frappe.throw(
				_("Provide at least one of Source Contract or Source GRN to link procurement origin."),
				frappe.ValidationError,
			)

		if self.source_contract and not frappe.db.exists(PC, self.source_contract):
			frappe.throw(_("Source Contract not found."), frappe.ValidationError)

		if self.source_grn:
			if not frappe.db.exists(GRN, self.source_grn):
				frappe.throw(_("Source GRN not found."), frappe.ValidationError)
			grn_pc = frappe.db.get_value(GRN, self.source_grn, "contract")
			if self.source_contract and grn_pc and grn_pc != self.source_contract:
				frappe.throw(_("Source GRN must belong to the same Procurement Contract when both are set."), frappe.ValidationError)

		if self.currency and not frappe.db.exists("Currency", self.currency):
			frappe.throw(_("Currency not found."), frappe.ValidationError)

		if self.assigned_to_user and not frappe.db.exists("User", self.assigned_to_user):
			frappe.throw(_("Assigned To user not found."), frappe.ValidationError)

		if flt(self.acquisition_cost) < 0:
			frappe.throw(_("Acquisition cost cannot be negative."), frappe.ValidationError)
