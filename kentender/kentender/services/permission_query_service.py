# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Reusable **filter fragments** for scope-aware list queries (STORY-CORE-010).

These helpers produce dicts suitable for ``frappe.get_all`` / ``frappe.get_list``
``filters`` (AND-combined with other keys). They do **not** run queries themselves.

**Entity scope** uses the same rules as :mod:`kentender.services.entity_scope_service`:
central users see all entities unless an *active* entity is supplied; other users are
limited to **User Permission** values on **Procuring Entity**.

**Self-owned** patterns use a configurable owner field (Frappe default ``owner``).

**Assignment-based** visibility: use
:func:`kentender.services.assignment_access_service.list_assigned_target_docnames_for_user`
with :func:`name_in_docnames` to build ``{"name": ("in", ...)}`` fragments. Combining
entity scope with assignment visibility often requires ``or_filters`` or a two-step
query — see module docstring examples in tests.

Avoid hardcoding module-specific DocTypes here; callers pass ``doctype`` when running queries.

Call only from **server-side** code.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender.services.entity_scope_service import (
	is_central_entity_scope_user,
	list_user_procuring_entity_permissions,
)

# Matches no rows when used as ``{"name": ("in", NO_DOCNAMES)}`` in Frappe list queries.
NO_MATCHING_DOCNAMES: tuple[str, ...] = ()


def name_in_docnames(
	docnames: list[str] | tuple[str, ...],
	*,
	name_field: str = "name",
) -> dict[str, Any]:
	"""Filter *name_field* to the given primary keys; empty *docnames* matches nothing."""
	unique = list(dict.fromkeys((d or "").strip() for d in docnames if (d or "").strip()))
	if not unique:
		return {name_field: ("in", list(NO_MATCHING_DOCNAMES))}
	return {name_field: ("in", unique)}


def owner_is_user(
	user: str | None,
	*,
	owner_field: str = "owner",
) -> dict[str, Any]:
	"""Filter rows where *owner_field* equals *user* (defaults to session user)."""
	u = (user or frappe.session.user or "").strip()
	return {owner_field: u}


def merge_entity_scope_filters(
	base_filters: dict[str, Any] | None,
	user: str | None,
	*,
	active_entity: str | None = None,
	entity_field: str = "procuring_entity",
	allow_central: bool = True,
) -> dict[str, Any]:
	"""Return a new filter dict: *base_filters* plus procuring-entity constraints.

	- **Central** (*allow_central* and user is central): no extra filter unless
	  *active_entity* is set, then ``{entity_field: active_entity}``.
	- **Non-central**: if *active_entity* is set, it must be in the user's allowed
	  entities; otherwise filters to ``("in", allowed_entities)``. No allowed entities
	  yields a filter that matches no rows.
	"""
	out: dict[str, Any] = dict(base_filters or {})
	u = (user or frappe.session.user or "").strip()
	ae = (active_entity or "").strip()

	if allow_central and is_central_entity_scope_user(u):
		if ae:
			out[entity_field] = ae
		return out

	granted = list_user_procuring_entity_permissions(u)
	if not granted:
		out.update(name_in_docnames([], name_field="name"))
		return out

	if ae:
		if ae not in granted:
			out.update(name_in_docnames([], name_field="name"))
			return out
		out[entity_field] = ae
		return out

	if len(granted) == 1:
		out[entity_field] = granted[0]
	else:
		out[entity_field] = ("in", granted)
	return out


def or_filters_entity_or_docnames(
	*,
	entity_field: str,
	entity_values: list[str] | tuple[str, ...],
	name_field: str = "name",
	docnames: list[str] | tuple[str, ...],
) -> list[list[str]]:
	"""Build ``or_filters`` for: (*entity_field* in *entity_values*) OR (*name_field* in *docnames*).

	Empty *entity_values* and *docnames* yields a condition that matches nothing
	(``name`` ``in`` empty tuple). Callers should pass only non-empty legs when possible.

	Example::

	    names = list_assigned_target_docnames_for_user(user, \"Tender\")
	    filters = {\"status\": \"Open\"}
	    of = or_filters_entity_or_docnames(
	        entity_field=\"procuring_entity\",
	        entity_values=[\"PE-1\"],
	        docnames=names,
	    )
	    frappe.get_all(\"My DocType\", filters=filters, or_filters=of)
	"""
	ev = [x for x in entity_values if (x or "").strip()]
	dn = [x for x in docnames if (x or "").strip()]
	ors: list[list[str]] = []
	if ev:
		if len(ev) == 1:
			ors.append([entity_field, "=", ev[0]])
		else:
			ors.append([entity_field, "in", ev])
	if dn:
		if len(dn) == 1:
			ors.append([name_field, "=", dn[0]])
		else:
			ors.append([name_field, "in", dn])
	if not ors:
		return [["name", "in", []]]
	return ors
