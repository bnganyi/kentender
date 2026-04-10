# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Purchase Requisition totals and structural validation (PROC-STORY-003).

Delegates strategy and budget boundary checks to existing ``kentender_strategy`` /
``kentender_budget`` services — no duplicated linkage rules.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from kentender_budget.services.budget_downstream import validate_budget_line
from kentender_budget.services.budget_line_scope_validation import (
	assert_budget_and_control_period_belong_to_procuring_entity,
	validate_strategic_plan_program_sub_chain,
	validate_strategy_linkage_via_service,
)
from kentender_strategy.services.strategic_linkage_validation import assert_procuring_department_scoped


def _strip(v: str | None) -> str:
	return (v or "").strip()


SUBMISSION_READY_WORKFLOW: frozenset[str] = frozenset(
	{
		"Pending HOD Approval",
		"Pending Finance Approval",
		"Approved",
	},
)


def recompute_requested_amount_from_items(doc: Document) -> None:
	"""Set ``requested_amount`` to the sum of child ``line_total`` (after line validate)."""
	total = 0.0
	for row in doc.get("items") or []:
		total += flt(row.line_total)
	doc.set("requested_amount", total)


def validate_minimum_items_for_submission(doc: Document) -> None:
	"""Require at least one line when moving into submission-ready workflow/status."""
	ws = _strip(doc.get("workflow_state"))
	if ws in SUBMISSION_READY_WORKFLOW:
		if not (doc.get("items") or []):
			frappe.throw(
				_("At least one requisition item is required before submission."),
				frappe.ValidationError,
				title=_("No line items"),
			)


def validate_purchase_requisition_budget_and_strategy(doc: Document) -> None:
	"""Entity-scoped budget/strategy headers + optional budget line boundary."""
	assert_budget_and_control_period_belong_to_procuring_entity(doc)
	validate_strategic_plan_program_sub_chain(doc)
	validate_strategy_linkage_via_service(doc)

	ent = _strip(doc.get("procuring_entity"))
	assert_procuring_department_scoped(
		doc.get("requesting_department"),
		procuring_entity=ent or None,
		message=_("Requesting Department must belong to the same procuring entity as this requisition."),
	)

	_validate_national_objective_vs_program(doc)

	bl = _strip(doc.get("budget_line"))
	if bl:
		if not ent:
			frappe.throw(_("Procuring Entity is required when Budget Line is set."), frappe.ValidationError)
		validate_budget_line(bl, ent)
		bud = _strip(doc.get("budget"))
		if bud:
			line_bud = frappe.db.get_value("Budget Line", bl, "budget")
			if line_bud and line_bud != bud:
				frappe.throw(
					_("Budget Line {0} belongs to Budget {1}, not {2}.").format(
						frappe.bold(bl),
						frappe.bold(line_bud),
						frappe.bold(bud),
					),
					frappe.ValidationError,
					title=_("Budget mismatch"),
				)


def _validate_national_objective_vs_program(doc: Document) -> None:
	prg = _strip(doc.get("program"))
	no = _strip(doc.get("national_objective"))
	if not prg or not no:
		return
	exp = frappe.db.get_value("Strategic Program", prg, "national_objective")
	if exp and exp != no:
		frappe.throw(
			_("National Objective must match the selected Program's National Objective."),
			frappe.ValidationError,
			title=_("Objective mismatch"),
		)
