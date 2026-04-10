# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Requisition Amendment Record — auditable change intent (PROC-STORY-007)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class RequisitionAmendmentRecord(Document):
	def validate(self):
		self.display_label = code_title_label(
			(self.purchase_requisition or "").strip(),
			(self.amendment_type or "").strip(),
		)
		st = (self.status or "").strip()
		if st in ("Approved", "Applied"):
			if not (self.approved_by or "").strip():
				frappe.throw(
					_("Approved By is required when status is {0}.").format(frappe.bold(st)),
					frappe.ValidationError,
					title=_("Missing approver"),
				)
			if not self.approved_on:
				frappe.throw(
					_("Approved On is required when status is {0}.").format(frappe.bold(st)),
					frappe.ValidationError,
					title=_("Missing approval time"),
				)
