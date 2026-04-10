# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Requisition Approval Record — append-only audit of requisition decisions (PROC-STORY-004)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class RequisitionApprovalRecord(Document):
	def validate(self):
		self.display_label = code_title_label(
			(self.purchase_requisition or "").strip(),
			(self.workflow_step or "").strip(),
		)
		if not self.is_new():
			frappe.throw(
				_("Requisition Approval Record cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)

	def on_trash(self):
		frappe.throw(
			_("Requisition Approval Record cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
