# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""KenTender UAT bootstrap: ensure Frappe **Role** documents for the permissions matrix.

Role names follow ``docs/security/KenTender Roles and Permissions Matrix.md`` and
``docs/security/KenTender_Permissions_Matrix.xlsx`` (Role Catalogue), via
:class:`kentender.permissions.registry.MATRIX_ROLE`.

Desk and portal test **users** are seeded only from **minimal golden** JSON
(``kentender.uat.minimal_golden``) and optional MVP loaders that reuse the same
emails — not from this module.

On every site migrate, :func:`after_migrate` ensures all matrix roles exist
(except Frappe built-in ``System Manager``, which is not inserted here).
"""

from __future__ import annotations

import frappe

from kentender.permissions.registry import MATRIX_ROLE

# Back-compat name: tuple of (role_name, description) for all matrix roles except System Manager.
# Dedupes enum aliases that share the same Frappe Role.name.
def _matrix_bootstrap_rows() -> tuple[tuple[str, str], ...]:
	seen: set[str] = set()
	out: list[tuple[str, str]] = []
	for m in MATRIX_ROLE:
		if m is MATRIX_ROLE.SYSTEM_MANAGER:
			continue
		v = m.value
		if v in seen:
			continue
		seen.add(v)
		out.append((v, f"KenTender matrix — {v}"))
	return tuple(out)


KT_UAT_ROLES = _matrix_bootstrap_rows()


def _ensure_role(role_name: str, *, desk_access: int = 1) -> None:
	if frappe.db.exists("Role", role_name):
		return
	frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": role_name,
			"desk_access": desk_access,
			"is_custom": 1,
		}
	).insert(ignore_permissions=True)


def ensure_uat_roles() -> None:
	for role_name, _desc in KT_UAT_ROLES:
		desk = 0 if role_name == MATRIX_ROLE.SUPPLIER.value else 1
		_ensure_role(role_name, desk_access=desk)
	frappe.db.commit()


def after_migrate() -> None:
	ensure_uat_roles()
