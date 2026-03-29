# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Reusable strategy hierarchy and entity checks for budget, procurement, and DocType validators."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


def _strip(v: str | None) -> str:
	return (v or "").strip()


def _require_procuring_entity(entity: str | None) -> str:
	ent = _strip(entity)
	if not ent:
		frappe.throw(_("Procuring Entity is required."), frappe.ValidationError, title=_("Missing entity"))
	if not frappe.db.exists("Procuring Entity", ent):
		frappe.throw(
			_("Procuring Entity {0} does not exist.").format(frappe.bold(ent)),
			frappe.ValidationError,
			title=_("Invalid entity"),
		)
	return ent


def assert_procuring_department_scoped(
	responsible_department: str | None,
	*,
	program_id: str | None = None,
	procuring_entity: str | None = None,
	message: str | None = None,
) -> None:
	"""Department must belong to the same procuring entity as the program (or explicit entity on Strategic Program)."""
	dept = _strip(responsible_department)
	if not dept:
		return
	ent: str | None = None
	if program_id:
		ent = frappe.db.get_value("Strategic Program", _strip(program_id), "procuring_entity")
	elif procuring_entity:
		ent = _strip(procuring_entity)
	if not ent:
		return
	dept_entity = frappe.db.get_value("Procuring Department", dept, "procuring_entity")
	if dept_entity and ent and dept_entity != ent:
		frappe.throw(
			message
			or _("Responsible Department must belong to the same procuring entity as the program."),
			frappe.ValidationError,
			title=_("Department scope"),
		)


def sync_strategic_sub_program_plan(doc: Document) -> None:
	"""Set `entity_strategic_plan` from parent program when missing; validate when set."""
	prg = _strip(doc.get("program"))
	if not prg:
		return
	if not frappe.db.exists("Strategic Program", prg):
		frappe.throw(
			_("Strategic Program {0} does not exist.").format(frappe.bold(prg)),
			frappe.ValidationError,
			title=_("Invalid program"),
		)
	plan_from_program = frappe.db.get_value("Strategic Program", prg, "entity_strategic_plan")
	if not plan_from_program:
		frappe.throw(
			_("Strategic Program {0} has no Entity Strategic Plan.").format(frappe.bold(prg)),
			frappe.ValidationError,
			title=_("Invalid program"),
		)
	plan = _strip(doc.get("entity_strategic_plan"))
	if not plan:
		doc.entity_strategic_plan = plan_from_program
		return
	if plan != plan_from_program:
		frappe.throw(
			_(
				"Entity Strategic Plan must match the selected program's plan "
				"(expected {0}, got {1})."
			).format(frappe.bold(plan_from_program), frappe.bold(plan)),
			frappe.ValidationError,
			title=_("Plan mismatch"),
		)


def sync_output_indicator_hierarchy(doc: Document) -> None:
	"""Align program and plan from `sub_program`; mutate doc when fields are empty."""
	sub = _strip(doc.get("sub_program"))
	if not sub:
		return
	if not frappe.db.exists("Strategic Sub Program", sub):
		frappe.throw(
			_("Strategic Sub Program {0} does not exist.").format(frappe.bold(sub)),
			frappe.ValidationError,
			title=_("Invalid sub program"),
		)
	expected_program = frappe.db.get_value("Strategic Sub Program", sub, "program")
	expected_plan = frappe.db.get_value("Strategic Sub Program", sub, "entity_strategic_plan")
	if not expected_program:
		frappe.throw(
			_("Strategic Sub Program {0} has no parent Program.").format(frappe.bold(sub)),
			frappe.ValidationError,
			title=_("Invalid sub program"),
		)
	if not expected_plan:
		frappe.throw(
			_("Strategic Sub Program {0} has no Entity Strategic Plan.").format(frappe.bold(sub)),
			frappe.ValidationError,
			title=_("Invalid sub program"),
		)

	prog = _strip(doc.get("program"))
	if not prog:
		doc.program = expected_program
	elif prog != expected_program:
		frappe.throw(
			_(
				"Program must match the selected Sub Program's program "
				"(expected {0}, got {1})."
			).format(frappe.bold(expected_program), frappe.bold(prog)),
			frappe.ValidationError,
			title=_("Program mismatch"),
		)

	plan = _strip(doc.get("entity_strategic_plan"))
	if not plan:
		doc.entity_strategic_plan = expected_plan
	elif plan != expected_plan:
		frappe.throw(
			_(
				"Entity Strategic Plan must match the selected Sub Program's plan "
				"(expected {0}, got {1})."
			).format(frappe.bold(expected_plan), frappe.bold(plan)),
			frappe.ValidationError,
			title=_("Plan mismatch"),
		)


def sync_performance_target_hierarchy(doc: Document) -> None:
	"""Align sub-program, program, and plan from `output_indicator`; mutate doc when empty."""
	ind_name = _strip(doc.get("output_indicator"))
	if not ind_name:
		return
	if not frappe.db.exists("Output Indicator", ind_name):
		frappe.throw(
			_("Output Indicator {0} does not exist.").format(frappe.bold(ind_name)),
			frappe.ValidationError,
			title=_("Invalid indicator"),
		)
	row = frappe.db.get_value(
		"Output Indicator",
		ind_name,
		["sub_program", "program", "entity_strategic_plan"],
		as_dict=True,
	)
	if not row or not row.sub_program or not row.program or not row.entity_strategic_plan:
		frappe.throw(
			_("Output Indicator {0} is missing program hierarchy.").format(frappe.bold(ind_name)),
			frappe.ValidationError,
			title=_("Invalid indicator"),
		)

	labels = {
		"sub_program": _("Sub Program"),
		"program": _("Program"),
		"entity_strategic_plan": _("Entity Strategic Plan"),
	}
	for field, expected in (
		("sub_program", row.sub_program),
		("program", row.program),
		("entity_strategic_plan", row.entity_strategic_plan),
	):
		current = _strip(doc.get(field))
		if not current:
			doc.set(field, expected)
		elif current != expected:
			frappe.throw(
				_(
					"{0} must match the selected Output Indicator "
					"(expected {1}, got {2})."
				).format(
					labels[field],
					frappe.bold(expected),
					frappe.bold(current),
				),
				frappe.ValidationError,
				title=_("Hierarchy mismatch"),
			)


def validate_program(program_id: str, entity: str) -> None:
	"""Ensure the strategic program exists and belongs to ``entity`` (Procuring Entity name)."""
	pid = _strip(program_id)
	ent = _require_procuring_entity(entity)
	if not pid:
		frappe.throw(_("Strategic Program is required."), frappe.ValidationError, title=_("Missing program"))
	if not frappe.db.exists("Strategic Program", pid):
		frappe.throw(
			_("Strategic Program {0} does not exist.").format(frappe.bold(pid)),
			frappe.ValidationError,
			title=_("Invalid program"),
		)
	prog_ent = frappe.db.get_value("Strategic Program", pid, "procuring_entity")
	if not prog_ent or prog_ent != ent:
		frappe.throw(
			_("Strategic Program {0} does not belong to Procuring Entity {1}.").format(
				frappe.bold(pid),
				frappe.bold(ent),
			),
			frappe.ValidationError,
			title=_("Entity mismatch"),
		)
	plan = frappe.db.get_value("Strategic Program", pid, "entity_strategic_plan")
	if plan:
		plan_ent = frappe.db.get_value("Entity Strategic Plan", plan, "procuring_entity")
		if plan_ent and plan_ent != ent:
			frappe.throw(
				_(
					"Entity Strategic Plan {0} for this program does not belong to Procuring Entity {1}."
				).format(frappe.bold(plan), frappe.bold(ent)),
				frappe.ValidationError,
				title=_("Entity mismatch"),
			)


def validate_sub_program(sub_program_id: str, entity: str) -> None:
	"""Ensure sub-program exists, parent program belongs to ``entity``, and plan/program row is aligned."""
	sid = _strip(sub_program_id)
	ent = _require_procuring_entity(entity)
	if not sid:
		frappe.throw(_("Strategic Sub Program is required."), frappe.ValidationError, title=_("Missing sub program"))
	if not frappe.db.exists("Strategic Sub Program", sid):
		frappe.throw(
			_("Strategic Sub Program {0} does not exist.").format(frappe.bold(sid)),
			frappe.ValidationError,
			title=_("Invalid sub program"),
		)
	program_id = frappe.db.get_value("Strategic Sub Program", sid, "program")
	if not program_id:
		frappe.throw(
			_("Strategic Sub Program {0} has no parent Program.").format(frappe.bold(sid)),
			frappe.ValidationError,
			title=_("Invalid sub program"),
		)
	validate_program(program_id, ent)
	plan_on_sub = frappe.db.get_value("Strategic Sub Program", sid, "entity_strategic_plan")
	plan_on_program = frappe.db.get_value("Strategic Program", program_id, "entity_strategic_plan")
	if plan_on_sub and plan_on_program and plan_on_sub != plan_on_program:
		frappe.throw(
			_("Strategic Sub Program {0} is not aligned with its program's strategic plan.").format(
				frappe.bold(sid)
			),
			frappe.ValidationError,
			title=_("Plan mismatch"),
		)


def validate_indicator(indicator_id: str, entity: str) -> None:
	"""Ensure indicator exists, program belongs to ``entity``, and indicator matches its sub-program chain."""
	iid = _strip(indicator_id)
	ent = _require_procuring_entity(entity)
	if not iid:
		frappe.throw(_("Output Indicator is required."), frappe.ValidationError, title=_("Missing indicator"))
	if not frappe.db.exists("Output Indicator", iid):
		frappe.throw(
			_("Output Indicator {0} does not exist.").format(frappe.bold(iid)),
			frappe.ValidationError,
			title=_("Invalid indicator"),
		)
	sub = frappe.db.get_value("Output Indicator", iid, "sub_program")
	program_id = frappe.db.get_value("Output Indicator", iid, "program")
	plan_ind = frappe.db.get_value("Output Indicator", iid, "entity_strategic_plan")
	if not sub or not program_id or not plan_ind:
		frappe.throw(
			_("Output Indicator {0} is missing program hierarchy.").format(frappe.bold(iid)),
			frappe.ValidationError,
			title=_("Invalid indicator"),
		)
	validate_program(program_id, ent)
	exp_prog = frappe.db.get_value("Strategic Sub Program", sub, "program")
	exp_plan = frappe.db.get_value("Strategic Sub Program", sub, "entity_strategic_plan")
	if program_id != exp_prog or plan_ind != exp_plan:
		frappe.throw(
			_("Output Indicator {0} hierarchy is inconsistent with Sub Program {1}.").format(
				frappe.bold(iid),
				frappe.bold(sub),
			),
			frappe.ValidationError,
			title=_("Hierarchy mismatch"),
		)


def validate_target(target_id: str, entity: str, as_of_date=None) -> None:
	"""Ensure target exists, indicator chain belongs to ``entity``, stored hierarchy matches indicator.

	If ``as_of_date`` is set, it must fall within the target period (inclusive).
	"""
	tid = _strip(target_id)
	ent = _require_procuring_entity(entity)
	if not tid:
		frappe.throw(_("Performance Target is required."), frappe.ValidationError, title=_("Missing target"))
	if not frappe.db.exists("Performance Target", tid):
		frappe.throw(
			_("Performance Target {0} does not exist.").format(frappe.bold(tid)),
			frappe.ValidationError,
			title=_("Invalid target"),
		)
	ind = frappe.db.get_value("Performance Target", tid, "output_indicator")
	if not ind:
		frappe.throw(
			_("Performance Target {0} has no Output Indicator.").format(frappe.bold(tid)),
			frappe.ValidationError,
			title=_("Invalid target"),
		)
	validate_indicator(ind, ent)

	row_t = frappe.db.get_value(
		"Performance Target",
		tid,
		["sub_program", "program", "entity_strategic_plan"],
		as_dict=True,
	)
	row_i = frappe.db.get_value(
		"Output Indicator",
		ind,
		["sub_program", "program", "entity_strategic_plan"],
		as_dict=True,
	)
	assert row_t and row_i
	for k in ("sub_program", "program", "entity_strategic_plan"):
		if row_t.get(k) != row_i.get(k):
			frappe.throw(
				_("Performance Target {0} does not match Output Indicator hierarchy.").format(frappe.bold(tid)),
				frappe.ValidationError,
				title=_("Hierarchy mismatch"),
			)

	if as_of_date is not None:
		start = frappe.db.get_value("Performance Target", tid, "period_start_date")
		end = frappe.db.get_value("Performance Target", tid, "period_end_date")
		if not start or not end:
			frappe.throw(
				_("Performance Target {0} is missing period dates.").format(frappe.bold(tid)),
				frappe.ValidationError,
				title=_("Invalid period"),
			)
		d = getdate(as_of_date)
		if d < getdate(start) or d > getdate(end):
			frappe.throw(
				_("Date {0} is outside the performance target period ({1} to {2}).").format(
					frappe.bold(str(d)),
					frappe.bold(str(start)),
					frappe.bold(str(end)),
				),
				frappe.ValidationError,
				title=_("Period mismatch"),
			)


def validate_strategic_linkage_set(
	*,
	program: str | None = None,
	sub_program: str | None = None,
	output_indicator: str | None = None,
	performance_target: str | None = None,
	entity: str | None = None,
	as_of_date=None,
) -> None:
	"""Validate any combination of strategy records for a single procuring entity.

	At least ``entity`` is required. Each supplied id is validated; when multiple ids are supplied,
	cross-checks ensure they reference the same chain where applicable.
	"""
	ent = _require_procuring_entity(entity)
	if not any((_strip(program), _strip(sub_program), _strip(output_indicator), _strip(performance_target))):
		return

	p = _strip(program)
	s = _strip(sub_program)
	i = _strip(output_indicator)
	t = _strip(performance_target)

	if p:
		validate_program(p, ent)
	if s:
		validate_sub_program(s, ent)
		if p:
			sp = frappe.db.get_value("Strategic Sub Program", s, "program")
			if sp != p:
				frappe.throw(
					_("Sub Program {0} does not belong to Program {1}.").format(
						frappe.bold(s),
						frappe.bold(p),
					),
					frappe.ValidationError,
					title=_("Linkage mismatch"),
				)
	if i:
		validate_indicator(i, ent)
		if s:
			isub = frappe.db.get_value("Output Indicator", i, "sub_program")
			if isub != s:
				frappe.throw(
					_("Output Indicator {0} does not belong to Sub Program {1}.").format(
						frappe.bold(i),
						frappe.bold(s),
					),
					frappe.ValidationError,
					title=_("Linkage mismatch"),
				)
		if p:
			ip = frappe.db.get_value("Output Indicator", i, "program")
			if ip != p:
				frappe.throw(
					_("Output Indicator {0} does not belong to Program {1}.").format(
						frappe.bold(i),
						frappe.bold(p),
					),
					frappe.ValidationError,
					title=_("Linkage mismatch"),
				)
	if t:
		validate_target(t, ent, as_of_date=as_of_date)
		if i:
			ti = frappe.db.get_value("Performance Target", t, "output_indicator")
			if ti != i:
				frappe.throw(
					_("Performance Target {0} does not reference Output Indicator {1}.").format(
						frappe.bold(t),
						frappe.bold(i),
					),
					frappe.ValidationError,
					title=_("Linkage mismatch"),
				)
		if s:
			ts = frappe.db.get_value("Performance Target", t, "sub_program")
			if ts != s:
				frappe.throw(
					_("Performance Target {0} does not belong to Sub Program {1}.").format(
						frappe.bold(t),
						frappe.bold(s),
					),
					frappe.ValidationError,
					title=_("Linkage mismatch"),
				)
		if p:
			tp = frappe.db.get_value("Performance Target", t, "program")
			if tp != p:
				frappe.throw(
					_("Performance Target {0} does not belong to Program {1}.").format(
						frappe.bold(t),
						frappe.bold(p),
					),
					frappe.ValidationError,
					title=_("Linkage mismatch"),
				)
