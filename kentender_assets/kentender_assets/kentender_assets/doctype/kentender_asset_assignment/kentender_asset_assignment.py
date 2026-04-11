# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-015: custody / location assignment for a KenTender Asset."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

A = "KenTender Asset"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class KenTenderAssetAssignment(Document):
	def validate(self):
		if self.business_id is not None:
			self.business_id = self.business_id.strip()
		self.display_label = code_title_label(_strip(self.business_id), "Assignment")

		if not frappe.db.exists(A, self.asset):
			frappe.throw(_("KenTender Asset not found."), frappe.ValidationError)
		if self.assigned_to_user and not frappe.db.exists("User", self.assigned_to_user):
			frappe.throw(_("Assigned To user not found."), frappe.ValidationError)
