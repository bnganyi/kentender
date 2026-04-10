# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan Revision — controlled change intent without mutating live plans (PROC-STORY-019).

Snapshot references on child rows are opaque in v1; PROC-STORY-020 may define storage.
revision_business_id is supplied by the caller or a future workflow.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

PPI_DOCTYPE = "Procurement Plan Item"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementPlanRevision(Document):
	def validate(self):
		bid = _strip(self.revision_business_id)
		rt = _strip(self.revision_type)
		self.display_label = code_title_label(bid, rt)
		self._validate_revision_lines_belong_to_source_plan()
		self._validate_approved_has_approver_fields()

	def _validate_revision_lines_belong_to_source_plan(self) -> None:
		plan = _strip(self.source_procurement_plan)
		if not plan:
			return
		for row in self.revision_lines or []:
			item = _strip(row.get("affected_plan_item"))
			if not item:
				continue
			if not frappe.db.exists(PPI_DOCTYPE, item):
				frappe.throw(
					_("Affected Plan Item {0} does not exist.").format(frappe.bold(item)),
					frappe.ValidationError,
					title=_("Invalid plan item"),
				)
			item_plan = _strip(frappe.db.get_value(PPI_DOCTYPE, item, "procurement_plan"))
			if item_plan != plan:
				frappe.throw(
					_(
						"Revision line plan item {0} must belong to source procurement plan {1}."
					).format(frappe.bold(item), frappe.bold(plan)),
					frappe.ValidationError,
					title=_("Plan mismatch"),
				)

	def _validate_approved_has_approver_fields(self) -> None:
		if _strip(self.status) != "Approved":
			return
		if not _strip(self.approved_by):
			frappe.throw(
				_("Approved By is required when status is Approved."),
				frappe.ValidationError,
				title=_("Missing approver"),
			)
		if not self.approved_on:
			frappe.throw(
				_("Approved On is required when status is Approved."),
				frappe.ValidationError,
				title=_("Missing approval time"),
			)
