# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan structural validation (PROC-STORY-011)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_budget.services.budget_line_scope_validation import (
	assert_budget_and_control_period_belong_to_procuring_entity,
)


def _strip(v: str | None) -> str:
	return (v or "").strip()


def validate_procurement_plan(doc: Document) -> None:
	"""Entity/BCP scope, fiscal year alignment, basic supersession rules."""
	assert_budget_and_control_period_belong_to_procuring_entity(doc)

	ent = _strip(doc.get("procuring_entity"))
	bcp = _strip(doc.get("budget_control_period"))
	fy = _strip(doc.get("fiscal_year"))

	if bcp and fy:
		bcp_fy = frappe.db.get_value("Budget Control Period", bcp, "fiscal_year")
		if bcp_fy and _strip(bcp_fy) != fy:
			frappe.throw(
				_("Fiscal Year must match the selected Budget Control Period."),
				frappe.ValidationError,
				title=_("Fiscal year mismatch"),
			)

	name = _strip(doc.get("name"))
	sup = _strip(doc.get("supersedes_plan"))
	if sup:
		if name and sup == name:
			frappe.throw(
				_("A plan cannot supersede itself."),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
		if not frappe.db.exists("Procurement Plan", sup):
			frappe.throw(
				_("Supersedes Plan {0} does not exist.").format(frappe.bold(sup)),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
		prev_ent = _strip(frappe.db.get_value("Procurement Plan", sup, "procuring_entity"))
		prev_fy = _strip(frappe.db.get_value("Procurement Plan", sup, "fiscal_year"))
		if ent and prev_ent and ent != prev_ent:
			frappe.throw(
				_("Supersedes Plan must belong to the same Procuring Entity."),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
		if fy and prev_fy and fy != prev_fy:
			frappe.throw(
				_("Supersedes Plan must share the same Fiscal Year."),
				frappe.ValidationError,
				title=_("Invalid supersession"),
			)
