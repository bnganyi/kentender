# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-016: condition assessment history for a KenTender Asset."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

A = "KenTender Asset"


class KenTenderAssetConditionLog(Document):
	def validate(self):
		self.display_label = code_title_label(self.asset or "", self.condition_status or "—")

		if not frappe.db.exists(A, self.asset):
			frappe.throw(_("KenTender Asset not found."), frappe.ValidationError)
		if self.assessed_by_user and not frappe.db.exists("User", self.assessed_by_user):
			frappe.throw(_("Assessed By user not found."), frappe.ValidationError)
