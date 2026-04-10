# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan Approval Record — append-only audit of plan decisions (PROC-STORY-015)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label


class ProcurementPlanApprovalRecord(Document):
	def validate(self):
		self.display_label = code_title_label(
			(self.procurement_plan or "").strip(),
			(self.workflow_step or "").strip(),
		)
		if not self.is_new():
			frappe.throw(
				_("Procurement Plan Approval Record cannot be modified."),
				frappe.ValidationError,
				title=_("Append-only record"),
			)

	def on_trash(self):
		frappe.throw(
			_("Procurement Plan Approval Record cannot be deleted."),
			frappe.ValidationError,
			title=_("Append-only record"),
		)
