# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Plan Fragmentation Alert — record model for anti-fragmentation findings (PROC-STORY-016)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label

PPI_DOCTYPE = "Procurement Plan Item"


def _strip(s: str | None) -> str:
	return (s or "").strip()


class PlanFragmentationAlert(Document):
	def validate(self):
		bid = _strip(self.business_id)
		at = _strip(self.alert_type)
		self.display_label = code_title_label(bid, at)
		self._validate_related_plan_item_belongs_to_plan()

	def _validate_related_plan_item_belongs_to_plan(self) -> None:
		item = _strip(self.related_plan_item)
		plan = _strip(self.procurement_plan)
		if not item:
			return
		if not frappe.db.exists(PPI_DOCTYPE, item):
			frappe.throw(
				_("Related Plan Item does not exist."),
				frappe.ValidationError,
				title=_("Invalid plan item"),
			)
		item_plan = _strip(frappe.db.get_value(PPI_DOCTYPE, item, "procurement_plan"))
		if plan and item_plan and item_plan != plan:
			frappe.throw(
				_("Related Plan Item must belong to the same Procurement Plan as this alert."),
				frappe.ValidationError,
				title=_("Plan mismatch"),
			)
