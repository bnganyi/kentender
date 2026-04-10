# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan Item — executable planning unit (PROC-STORY-012)."""

import frappe
from frappe.model.document import Document

from kentender.utils.display_label import code_title_label
from kentender_procurement.services.procurement_plan_item_validation import validate_procurement_plan_item
from kentender_procurement.services.procurement_plan_totals import refresh_procurement_plan_totals


def _strip(s: str | None) -> str:
	return (s or "").strip()


class ProcurementPlanItem(Document):
	def after_insert(self):
		pn = _strip(self.procurement_plan)
		if pn:
			refresh_procurement_plan_totals(pn)

	def on_update(self):
		prev = self.get_doc_before_save()
		if prev:
			old_plan = _strip(prev.get("procurement_plan"))
			new_plan = _strip(self.procurement_plan)
			if old_plan and old_plan != new_plan:
				refresh_procurement_plan_totals(old_plan)
		pn = _strip(self.procurement_plan)
		if pn:
			refresh_procurement_plan_totals(pn)

	def on_trash(self):
		pn = _strip(self.procurement_plan)
		if pn:
			refresh_procurement_plan_totals(pn)

	def validate(self):
		self._normalize_text_fields()
		self.display_label = code_title_label(self.name, self.title)
		validate_procurement_plan_item(self)

	def _normalize_text_fields(self):
		for fn in ("title", "source_summary", "beneficiary_summary", "remarks"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())
