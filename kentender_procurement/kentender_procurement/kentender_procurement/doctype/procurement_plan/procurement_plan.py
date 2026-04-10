# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan — consolidated demand header (PROC-STORY-011)."""

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.status_model import apply_registered_summary_fields
from kentender.utils.display_label import code_title_label
from kentender.services.sensitivity_classification import normalize_sensitivity_class
from kentender_procurement.services.procurement_plan_totals import apply_procurement_plan_totals_to_doc
from kentender_procurement.services.procurement_plan_validation import validate_procurement_plan


class ProcurementPlan(Document):
	def validate(self):
		apply_registered_summary_fields(self)
		self._normalize_text_fields()
		self.display_label = code_title_label(self.name, self.plan_title)
		self._validate_sensitivity_class()
		validate_procurement_plan(self)
		apply_procurement_plan_totals_to_doc(self)

	def _normalize_text_fields(self):
		for fn in ("plan_title", "fiscal_year", "plan_period_label"):
			val = getattr(self, fn, None)
			if val and isinstance(val, str):
				setattr(self, fn, val.strip())

	def _validate_sensitivity_class(self):
		raw = (self.sensitivity_class or "").strip()
		if not raw:
			return
		norm = normalize_sensitivity_class(raw)
		if norm is None:
			frappe.throw(
				_("Invalid Sensitivity Class."),
				frappe.ValidationError,
				title=_("Sensitivity"),
			)
		self.sensitivity_class = norm
