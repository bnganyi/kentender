# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Assignment-based access helpers (STORY-CORE-009).

Uses **KenTender Assignment** rows to decide whether a user is assigned to a target
record (committee, case session, etc.). This is **not** a substitute for Frappe
permissions; combine with :mod:`kentender.services.entity_scope_service` and DocType
rules in higher-level APIs.

**Checks supported:**

- user assigned to a target (``target_doctype`` / ``target_docname``)
- ``active`` flag
- optional ``assignment_type`` and ``assignment_role`` filters
- optional **validity window** (``valid_from`` / ``valid_to``) evaluated against an
  *as-of* date (defaults to today)

Call only from **server-side** code.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import frappe
from frappe.utils import getdate

ASSIGNMENT_DOCTYPE = "KenTender Assignment"


def _coerce_date(value: date | str | None) -> date | None:
	if value is None:
		return None
	if isinstance(value, date):
		return value
	return getdate(value)


def assignment_valid_for_date(
	*,
	valid_from: date | str | None,
	valid_to: date | str | None,
	as_of: date | str | None = None,
) -> bool:
	"""Return whether *as_of* falls in ``[valid_from, valid_to]`` (inclusive), open-ended if bounds missing."""
	d = _coerce_date(as_of) or getdate()
	vf = _coerce_date(valid_from)
	vt = _coerce_date(valid_to)
	if vf is not None and d < vf:
		return False
	if vt is not None and d > vt:
		return False
	return True


def user_has_assignment(
	user: str | None,
	target_doctype: str,
	target_docname: str,
	*,
	assignment_type: str | None = None,
	assignment_role: str | None = None,
	active_only: bool = True,
	as_of_date: date | str | None = None,
) -> bool:
	"""True if *user* has at least one matching **KenTender Assignment** row."""
	u = (user or frappe.session.user or "").strip()
	dt = (target_doctype or "").strip()
	dn = (target_docname or "").strip()
	if not u or not dt or not dn:
		return False

	filters: dict[str, Any] = {
		"user": u,
		"target_doctype": dt,
		"target_docname": dn,
	}
	if active_only:
		filters["active"] = 1
	if assignment_type:
		filters["assignment_type"] = assignment_type.strip()
	if assignment_role is not None and (assignment_role.strip() != ""):
		filters["assignment_role"] = assignment_role.strip()

	rows = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=filters,
		fields=["valid_from", "valid_to"],
	)
	for row in rows:
		if assignment_valid_for_date(
			valid_from=row.get("valid_from"),
			valid_to=row.get("valid_to"),
			as_of=as_of_date,
		):
			return True
	return False


def get_assignments_for_target(
	target_doctype: str,
	target_docname: str,
	*,
	active_only: bool = True,
	as_of_date: date | str | None = None,
) -> list[dict[str, Any]]:
	"""Return assignment rows for *target_doctype* / *target_docname* passing date checks."""
	dt = (target_doctype or "").strip()
	dn = (target_docname or "").strip()
	if not dt or not dn:
		return []

	filters: dict[str, Any] = {"target_doctype": dt, "target_docname": dn}
	if active_only:
		filters["active"] = 1

	candidates = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=filters,
		fields=[
			"name",
			"user",
			"assignment_type",
			"assignment_role",
			"active",
			"valid_from",
			"valid_to",
			"procuring_entity",
		],
	)
	out: list[dict[str, Any]] = []
	for row in candidates:
		if assignment_valid_for_date(
			valid_from=row.get("valid_from"),
			valid_to=row.get("valid_to"),
			as_of=as_of_date,
		):
			out.append(row)
	return out


def user_assignment_roles_on_target(
	user: str | None,
	target_doctype: str,
	target_docname: str,
	*,
	active_only: bool = True,
	as_of_date: date | str | None = None,
) -> list[str]:
	"""Distinct non-empty ``assignment_role`` values for *user* on the target."""
	u = (user or frappe.session.user or "").strip()
	dt = (target_doctype or "").strip()
	dn = (target_docname or "").strip()
	if not u or not dt or not dn:
		return []

	filters: dict[str, Any] = {
		"user": u,
		"target_doctype": dt,
		"target_docname": dn,
	}
	if active_only:
		filters["active"] = 1

	rows = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=filters,
		fields=["assignment_role", "valid_from", "valid_to"],
	)
	roles: set[str] = set()
	for row in rows:
		if not assignment_valid_for_date(
			valid_from=row.get("valid_from"),
			valid_to=row.get("valid_to"),
			as_of=as_of_date,
		):
			continue
		r = (row.get("assignment_role") or "").strip()
		if r:
			roles.add(r)
	return sorted(roles)


def list_assigned_target_docnames_for_user(
	user: str | None,
	target_doctype: str,
	*,
	assignment_type: str | None = None,
	active_only: bool = True,
	as_of_date: date | str | None = None,
) -> list[str]:
	"""Distinct ``target_docname`` values for *user* on *target_doctype* (validity-respecting).

	Intended for **permission query** composition (CORE-010): combine with entity filters
	using ``or_filters`` or separate queries, depending on product rules.
	"""
	u = (user or frappe.session.user or "").strip()
	dt = (target_doctype or "").strip()
	if not u or not dt:
		return []

	filters: dict[str, Any] = {"user": u, "target_doctype": dt}
	if active_only:
		filters["active"] = 1
	if assignment_type:
		filters["assignment_type"] = assignment_type.strip()

	rows = frappe.get_all(
		ASSIGNMENT_DOCTYPE,
		filters=filters,
		fields=["target_docname", "valid_from", "valid_to"],
	)
	names: set[str] = set()
	for row in rows:
		if not assignment_valid_for_date(
			valid_from=row.get("valid_from"),
			valid_to=row.get("valid_to"),
			as_of=as_of_date,
		):
			continue
		dn = (row.get("target_docname") or "").strip()
		if dn:
			names.add(dn)
	return sorted(names)
