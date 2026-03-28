# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Entity scope helpers for KenTender (STORY-CORE-008).

Most transactional DocTypes carry a **Procuring Entity** link (field name
``procuring_entity`` by default). These utilities centralize:

- whether a record **belongs** to a given entity
- whether a **user** may act in the context of an entity
- whether a user may access a **scoped record**, including **central** (cross-entity)
  operators

**Central users:** ``Administrator`` or users with the **System Manager** role are treated
as able to access any entity for purposes of these helpers (when ``allow_central`` is
true). Product-specific central roles can be added later in one place.

**Non-central users:** v1 grants entity access only when explicit **User Permission**
rows exist for DocType **Procuring Entity** (``for_value`` = entity name). No
User Permission rows for that DocType means this helper does **not** grant entity
access (conservative). Combine with :mod:`kentender.services.assignment_access_service`
(CORE-009) where assignment-based access applies.

Call only from **server-side** code.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document

PROCURING_ENTITY_DOCTYPE = "Procuring Entity"
_CENTRAL_ROLES = frozenset({"System Manager"})


def is_central_entity_scope_user(user: str | None = None) -> bool:
	"""True if *user* is allowed cross-entity operations (central operator pattern)."""
	u = (user or frappe.session.user or "").strip()
	if not u or u == "Administrator":
		return True
	return bool(_CENTRAL_ROLES.intersection(frappe.get_roles(u)))


def _procuring_entities_granted_by_user_permission(user: str) -> list[str]:
	return frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": PROCURING_ENTITY_DOCTYPE},
		pluck="for_value",
		distinct=True,
	)


def list_user_procuring_entity_permissions(user: str | None) -> list[str]:
	"""Procuring Entity names granted to *user* via **User Permission** (may be empty)."""
	u = (user or frappe.session.user or "").strip()
	if not u:
		return []
	return _procuring_entities_granted_by_user_permission(u)


def user_has_entity_access(
	user: str | None,
	entity: str | None,
	*,
	allow_central: bool = True,
) -> bool:
	"""Whether *user* may operate in the context of *entity* (entity name / code as stored on links).

	- Central users: any non-empty entity when ``allow_central`` is true.
	- Others: entity must appear in **User Permission** (Allow = Procuring Entity).
	"""
	name = (entity or "").strip()
	if not name:
		return False
	u = (user or frappe.session.user or "").strip()
	if not u:
		return False
	if allow_central and is_central_entity_scope_user(u):
		return True
	granted = list_user_procuring_entity_permissions(u)
	if not granted:
		return False
	return name in granted


def get_record_entity_value(doc: Any, *, entity_field: str = "procuring_entity") -> str | None:
	"""Return the procuring entity name from a mapping or Document, or None."""
	if doc is None:
		return None
	if isinstance(doc, dict):
		raw = doc.get(entity_field)
	else:
		raw = doc.get(entity_field) if hasattr(doc, "get") else getattr(doc, entity_field, None)
	if raw is None:
		return None
	s = str(raw).strip()
	return s or None


def record_belongs_to_entity(
	doc: Any,
	entity: str | None,
	*,
	entity_field: str = "procuring_entity",
) -> bool:
	"""True if the record is scoped to *entity* (default field ``procuring_entity``).

	A **Procuring Entity** document belongs to *entity* when ``doc.name`` matches.
	"""
	expected = (entity or "").strip()
	if not expected:
		return False
	doctype = None
	if isinstance(doc, dict):
		doctype = doc.get("doctype")
	elif isinstance(doc, Document):
		doctype = doc.doctype
	if doctype == PROCURING_ENTITY_DOCTYPE:
		name = doc.get("name") if isinstance(doc, dict) else doc.name
		return (name or "").strip() == expected
	value = get_record_entity_value(doc, entity_field=entity_field)
	if value is None:
		return False
	return value == expected


def user_may_access_scoped_record(
	user: str | None,
	doc: Any,
	*,
	active_entity: str | None = None,
	entity_field: str = "procuring_entity",
	allow_central: bool = True,
) -> bool:
	"""Whether *user* may access *doc* under optional *active_entity* context.

	- If ``allow_central`` and *user* is central: **True** (cross-entity visibility).
	- Otherwise *active_entity* must be set, the record must belong to it, and
	  ``user_has_entity_access(user, active_entity, allow_central=False)`` must hold.
	"""
	u = user or frappe.session.user
	if allow_central and is_central_entity_scope_user(u):
		return True
	ae = (active_entity or "").strip()
	if not ae:
		return False
	if not record_belongs_to_entity(doc, ae, entity_field=entity_field):
		return False
	return user_has_entity_access(u, ae, allow_central=False)
