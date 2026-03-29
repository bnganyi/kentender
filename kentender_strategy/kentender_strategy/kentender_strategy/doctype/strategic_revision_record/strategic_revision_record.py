# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class StrategicRevisionRecord(Document):
	"""Documents a strategic plan supersession without mutating plan rows (STORY-STRAT-006)."""

	def validate(self):
		self._normalize_text_fields()
		self._validate_unique_business_id()
		self._validate_plan_pair()

	def _normalize_text_fields(self):
		bid = getattr(self, "business_id", None)
		if bid and str(bid).strip():
			self.business_id = str(bid).strip()
		for fn in ("revision_reason", "impact_summary"):
			val = getattr(self, fn, None)
			if val and str(val).strip():
				setattr(self, fn, str(val).strip())

	def _validate_unique_business_id(self):
		bid = (self.business_id or "").strip()
		if not bid:
			return
		filters = {"business_id": bid}
		if self.name:
			filters["name"] = ("!=", self.name)
		existing = frappe.db.get_value("Strategic Revision Record", filters, "name")
		if existing:
			frappe.throw(
				_("Business ID {0} is already used by {1}.").format(
					frappe.bold(bid),
					frappe.bold(existing),
				),
				frappe.DuplicateEntryError,
				title=_("Duplicate Business ID"),
			)

	def _validate_plan_pair(self):
		old_p = (self.entity_strategic_plan_old or "").strip()
		new_p = (self.entity_strategic_plan_new or "").strip()
		if not old_p or not new_p:
			return
		if old_p == new_p:
			frappe.throw(
				_("Previous and New Strategic Plan must be different documents."),
				frappe.ValidationError,
				title=_("Invalid revision"),
			)
		for label, plan_name in (
			(_("Previous Strategic Plan"), old_p),
			(_("New Strategic Plan"), new_p),
		):
			if not frappe.db.exists("Entity Strategic Plan", plan_name):
				frappe.throw(
					_("{0} {1} does not exist.").format(label, frappe.bold(plan_name)),
					frappe.ValidationError,
					title=_("Invalid plan"),
				)
		ent_old = frappe.db.get_value("Entity Strategic Plan", old_p, "procuring_entity")
		ent_new = frappe.db.get_value("Entity Strategic Plan", new_p, "procuring_entity")
		if not ent_old or not ent_new:
			frappe.throw(
				_("Both plans must have a Procuring Entity."),
				frappe.ValidationError,
				title=_("Invalid revision"),
			)
		if ent_old != ent_new:
			frappe.throw(
				_(
					"Previous and New Strategic Plan must belong to the same Procuring Entity "
					"(expected {0} for both)."
				).format(frappe.bold(ent_old)),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)
