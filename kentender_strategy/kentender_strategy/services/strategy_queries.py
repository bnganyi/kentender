# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Read-only query helpers for active strategy structures (STORY-STRAT-010).

Downstream modules should use these helpers instead of re-implementing filters.
No budget or procurement joins (per story constraints).
"""

from __future__ import annotations

import frappe


def _strip_entity(procuring_entity: str | None) -> str:
	return (procuring_entity or "").strip()


def get_active_strategic_plans_for_entity(procuring_entity: str) -> list[dict]:
	"""Return strategic plans for ``procuring_entity`` with ``is_current_active_version`` set.

	Normally at most one row per entity; multiple rows indicate data issues but are returned as-is.
	"""
	ent = _strip_entity(procuring_entity)
	if not ent:
		return []
	return frappe.get_all(
		"Entity Strategic Plan",
		filters={"procuring_entity": ent, "is_current_active_version": 1},
		fields=[
			"name",
			"plan_title",
			"version_no",
			"status",
			"plan_period_label",
			"start_date",
			"end_date",
		],
		order_by="version_no desc",
	)


def get_programs_for_national_objective(national_objective: str) -> list[dict]:
	"""Return **Strategic Program** rows linked to the given **National Objective** name."""
	obj = (national_objective or "").strip()
	if not obj:
		return []
	return frappe.get_all(
		"Strategic Program",
		filters={"national_objective": obj},
		fields=[
			"name",
			"program_code",
			"program_name",
			"entity_strategic_plan",
			"procuring_entity",
			"status",
		],
		order_by="procuring_entity asc, program_code asc",
	)


def _program_names_for_entity(procuring_entity: str) -> list[str]:
	ent = _strip_entity(procuring_entity)
	if not ent:
		return []
	return frappe.get_all("Strategic Program", filters={"procuring_entity": ent}, pluck="name") or []


def get_output_indicators_for_entity(procuring_entity: str) -> list[dict]:
	"""Output indicators whose parent **Strategic Program** belongs to ``procuring_entity``."""
	programs = _program_names_for_entity(procuring_entity)
	if not programs:
		return []
	return frappe.get_all(
		"Output Indicator",
		filters={"program": ["in", programs]},
		fields=[
			"name",
			"indicator_code",
			"indicator_name",
			"sub_program",
			"program",
			"entity_strategic_plan",
			"status",
		],
		order_by="program asc, indicator_code asc",
	)


def get_performance_targets_for_entity(procuring_entity: str) -> list[dict]:
	"""Performance targets whose **program** belongs to ``procuring_entity``."""
	programs = _program_names_for_entity(procuring_entity)
	if not programs:
		return []
	return frappe.get_all(
		"Performance Target",
		filters={"program": ["in", programs]},
		fields=[
			"name",
			"target_title",
			"output_indicator",
			"sub_program",
			"program",
			"entity_strategic_plan",
			"period_start_date",
			"period_end_date",
			"status",
		],
		order_by="program asc, period_start_date desc",
	)


def get_indicators_and_targets_for_entity(procuring_entity: str) -> tuple[list[dict], list[dict]]:
	"""Convenience: indicators and targets for entity (two lists, same filters as single getters)."""
	return (
		get_output_indicators_for_entity(procuring_entity),
		get_performance_targets_for_entity(procuring_entity),
	)
