# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Budget Line: entity scope (CORE-008) + strategy linkage (shared services). Server-side only."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender.services.entity_scope_service import record_belongs_to_entity
from kentender_strategy.services.strategic_linkage_validation import (
	assert_procuring_department_scoped,
	validate_strategic_linkage_set,
)


def _strip(v: str | None) -> str:
	return (v or "").strip()


def _assert_record_belongs_to_procuring_entity(
	doctype: str,
	name: str,
	procuring_entity: str,
	*,
	error_title: str,
	error_message: str,
) -> None:
	row = frappe.db.get_value(doctype, name, ["name", "procuring_entity"], as_dict=True)
	if not row:
		return
	row["doctype"] = doctype
	if not record_belongs_to_entity(row, procuring_entity):
		frappe.throw(_(error_message), frappe.ValidationError, title=_(error_title))


def assert_budget_and_control_period_belong_to_procuring_entity(doc: Document) -> None:
	"""Ensure linked Budget and Budget Control Period rows match the line's procuring entity (CORE-008)."""
	ent = _strip(doc.get("procuring_entity"))
	if not ent:
		return
	bud = _strip(doc.get("budget"))
	if bud:
		_assert_record_belongs_to_procuring_entity(
			"Budget",
			bud,
			ent,
			error_title=_("Budget scope"),
			error_message=_("Budget must belong to the same Procuring Entity as this budget line."),
		)
	period = _strip(doc.get("budget_control_period"))
	if period:
		_assert_record_belongs_to_procuring_entity(
			"Budget Control Period",
			period,
			ent,
			error_title=_("Period scope"),
			error_message=_(
				"Budget Control Period must belong to the same Procuring Entity as this budget line."
			),
		)


def validate_strategic_plan_program_sub_chain(doc: Document) -> None:
	"""Plan / program / sub-program field consistency and plan entity scope (no duplicate of indicator/target checks)."""
	ent = _strip(doc.get("procuring_entity"))
	plan = _strip(doc.get("entity_strategic_plan"))
	if plan:
		if not frappe.db.exists("Entity Strategic Plan", plan):
			frappe.throw(
				_("Entity Strategic Plan {0} does not exist.").format(frappe.bold(plan)),
				frappe.ValidationError,
				title=_("Invalid plan"),
			)
		if ent:
			_assert_record_belongs_to_procuring_entity(
				"Entity Strategic Plan",
				plan,
				ent,
				error_title=_("Entity mismatch"),
				error_message=_("Entity Strategic Plan must belong to the same procuring entity as this line."),
			)
	prg = _strip(doc.get("program"))
	if prg and plan:
		exp_plan = frappe.db.get_value("Strategic Program", prg, "entity_strategic_plan")
		if exp_plan and exp_plan != plan:
			frappe.throw(
				_("Program does not belong to the selected Entity Strategic Plan."),
				frappe.ValidationError,
				title=_("Plan mismatch"),
			)
	sub = _strip(doc.get("sub_program"))
	if sub and prg:
		exp_prg = frappe.db.get_value("Strategic Sub Program", sub, "program")
		if exp_prg and exp_prg != prg:
			frappe.throw(
				_("Sub Program does not belong to the selected Program."),
				frappe.ValidationError,
				title=_("Program mismatch"),
			)
	if sub and plan:
		exp_plan = frappe.db.get_value("Strategic Sub Program", sub, "entity_strategic_plan")
		if exp_plan and exp_plan != plan:
			frappe.throw(
				_("Sub Program does not belong to the selected Entity Strategic Plan."),
				frappe.ValidationError,
				title=_("Plan mismatch"),
			)


def validate_strategy_linkage_via_service(doc: Document) -> None:
	"""Delegate program / sub / indicator / target checks to strategic_linkage_validation."""
	p = _strip(doc.get("program"))
	s = _strip(doc.get("sub_program"))
	i = _strip(doc.get("output_indicator"))
	t = _strip(doc.get("performance_target"))
	if not any((p, s, i, t)):
		return
	ent = _strip(doc.get("procuring_entity"))
	validate_strategic_linkage_set(
		program=p or None,
		sub_program=s or None,
		output_indicator=i or None,
		performance_target=t or None,
		entity=ent,
		as_of_date=None,
	)


def validate_departments_for_budget_line(doc: Document) -> None:
	ent = _strip(doc.get("procuring_entity"))
	assert_procuring_department_scoped(
		doc.get("department"),
		procuring_entity=ent,
		message=_("Department must belong to the same procuring entity as this budget line."),
	)
	assert_procuring_department_scoped(
		doc.get("responsible_department"),
		procuring_entity=ent,
		message=_(
			"Responsible Department must belong to the same procuring entity as this budget line."
		),
	)


def validate_budget_line_scope_and_strategy(doc: Document) -> None:
	"""Single entry point: header entity scope, strategy chain, shared linkage service, departments."""
	assert_budget_and_control_period_belong_to_procuring_entity(doc)
	validate_strategic_plan_program_sub_chain(doc)
	validate_strategy_linkage_via_service(doc)
	validate_departments_for_budget_line(doc)
