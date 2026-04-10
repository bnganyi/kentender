# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Procurement Plan Item validation (PROC-STORY-012)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from kentender_budget.services.budget_downstream import validate_budget_line
from kentender_budget.services.budget_line_scope_validation import (
	assert_budget_and_control_period_belong_to_procuring_entity,
	validate_strategic_plan_program_sub_chain,
	validate_strategy_linkage_via_service,
)
from kentender_strategy.services.strategic_linkage_validation import assert_procuring_department_scoped


def _strip(v: str | None) -> str:
	return (v or "").strip()


DATE_CHAIN_FIELDS: tuple[str, ...] = (
	"planned_start_date",
	"planned_preparation_start_date",
	"planned_publication_date",
	"planned_submission_deadline",
	"planned_award_date",
	"planned_contract_start_date",
	"planned_completion_date",
)


def _budget_context_for_scope_checks(doc: Document) -> frappe._dict:
	"""Merge Budget Line header fields so entity scope checks see period/budget when only line is set."""
	row = frappe._dict(doc.as_dict())
	bl = _strip(doc.get("budget_line"))
	if bl and frappe.db.exists("Budget Line", bl):
		line = frappe.db.get_value(
			"Budget Line",
			bl,
			["budget", "budget_control_period"],
			as_dict=True,
		)
		if line:
			if line.get("budget"):
				row["budget"] = line["budget"]
			if line.get("budget_control_period"):
				row["budget_control_period"] = line["budget_control_period"]
	return row


def validate_procurement_plan_item(doc: Document) -> None:
	_validate_non_negative_amounts(doc)
	_validate_procurement_plan_parent(doc)
	_validate_manual_origin(doc)
	_validate_planned_schedule(doc)

	ent = _strip(doc.get("procuring_entity"))

	check_doc = _budget_context_for_scope_checks(doc)
	assert_budget_and_control_period_belong_to_procuring_entity(check_doc)
	validate_strategic_plan_program_sub_chain(doc)
	validate_strategy_linkage_via_service(doc)

	if _strip(doc.get("requesting_department")):
		assert_procuring_department_scoped(
			doc.get("requesting_department"),
			procuring_entity=ent or None,
			message=_(
				"Requesting Department must belong to the same procuring entity as this plan item."
			),
		)
	if _strip(doc.get("responsible_department")):
		assert_procuring_department_scoped(
			doc.get("responsible_department"),
			procuring_entity=ent or None,
			message=_(
				"Responsible Department must belong to the same procuring entity as this plan item."
			),
		)

	_validate_national_objective_vs_program(doc)

	bl = _strip(doc.get("budget_line"))
	if bl:
		if not ent:
			frappe.throw(
				_("Procuring Entity is required when Budget Line is set."),
				frappe.ValidationError,
			)
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


def _validate_non_negative_amounts(doc: Document) -> None:
	meta = frappe.get_meta(doc.doctype)
	for fn in (
		"estimated_amount",
		"planned_budget_amount",
		"reserved_source_amount",
		"unbacked_amount",
	):
		if flt(doc.get(fn)) < 0:
			label = meta.get_label(fn) if meta else fn
			frappe.throw(
				_("{0} cannot be negative.").format(_(label)),
				frappe.ValidationError,
				title=_("Invalid amount"),
			)


def _validate_procurement_plan_parent(doc: Document) -> None:
	pn = _strip(doc.get("procurement_plan"))
	if not pn:
		return
	if not frappe.db.exists("Procurement Plan", pn):
		frappe.throw(
			_("Procurement Plan {0} does not exist.").format(frappe.bold(pn)),
			frappe.ValidationError,
			title=_("Invalid plan"),
		)
	plan = frappe.db.get_value(
		"Procurement Plan",
		pn,
		["procuring_entity", "currency", "name"],
		as_dict=True,
	)
	if not plan:
		return
	ent = _strip(doc.get("procuring_entity"))
	plan_ent = _strip(plan.get("procuring_entity"))
	if ent and plan_ent and ent != plan_ent:
		frappe.throw(
			_("Procuring Entity must match the parent Procurement Plan."),
			frappe.ValidationError,
			title=_("Entity mismatch"),
		)
	cur = _strip(doc.get("currency"))
	plan_cur = _strip(plan.get("currency"))
	if cur and plan_cur and cur != plan_cur:
		frappe.throw(
			_("Currency must match the parent Procurement Plan."),
			frappe.ValidationError,
			title=_("Currency mismatch"),
		)


def _validate_manual_origin(doc: Document) -> None:
	if _strip(doc.get("origin_type")) != "Manual":
		return
	pn = _strip(doc.get("procurement_plan"))
	if not pn:
		return
	allowed = frappe.db.get_value("Procurement Plan", pn, "allow_manual_items")
	if not allowed:
		frappe.throw(
			_("This procurement plan does not allow manual plan items."),
			frappe.ValidationError,
			title=_("Manual items not allowed"),
		)
	if not _strip(doc.get("manual_entry_justification")):
		frappe.throw(
			_("Manual Entry Justification is required when Origin Type is Manual."),
			frappe.ValidationError,
			title=_("Justification required"),
		)


def _validate_planned_schedule(doc: Document) -> None:
	for i in range(len(DATE_CHAIN_FIELDS) - 1):
		a = doc.get(DATE_CHAIN_FIELDS[i])
		b = doc.get(DATE_CHAIN_FIELDS[i + 1])
		if not a or not b:
			continue
		if getdate(a) > getdate(b):
			frappe.throw(
				_("Planned schedule dates must run in order ({0} cannot be after {1}).").format(
					DATE_CHAIN_FIELDS[i].replace("_", " "),
					DATE_CHAIN_FIELDS[i + 1].replace("_", " "),
				),
				frappe.ValidationError,
				title=_("Invalid schedule"),
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
