# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-017: maintenance work order / history for a KenTender Asset."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender.utils.display_label import code_title_label

A = "KenTender Asset"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAssetMaintenanceRecord(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		self.display_label = code_title_label(_strip(self.business_id), _strip(self.maintenance_type) or "—")

		if not frappe.db.exists(A, self.asset):
			frappe.throw(_("KenTender Asset not found."), frappe.ValidationError)
		if self.performed_by_user and not frappe.db.exists("User", self.performed_by_user):
			frappe.throw(_("Performed By user not found."), frappe.ValidationError)
		if self.currency and not frappe.db.exists("Currency", self.currency):
			frappe.throw(_("Currency not found."), frappe.ValidationError)
		if self.maintenance_cost is not None and flt(self.maintenance_cost) < 0:
			frappe.throw(_("Maintenance cost cannot be negative."), frappe.ValidationError)
