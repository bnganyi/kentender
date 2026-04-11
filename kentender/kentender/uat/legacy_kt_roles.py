# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Legacy Frappe **Role** names superseded by the matrix catalogue (plain names, no ``KT UAT`` prefix).

Older bootstraps and docs created ``KT UAT Requisitioner``-style roles; current code uses
:class:`kentender.permissions.registry.MATRIX_ROLE` values only (e.g. ``Requisitioner``).

Unit tests also create disposable roles ``KT PQ Test Role``, ``KT ASG Test Role``,
``KT C008 Scope Test`` — tearDown should remove them; :func:`purge_legacy_kt_roles` cleans sites.
"""

from __future__ import annotations

import traceback
from typing import Any

import frappe

__all__ = [
	"delete_obsolete_kt_role",
	"is_legacy_kt_uat_role_name",
	"iter_legacy_kt_role_names_on_site",
	"purge_legacy_kt_roles",
]

# Exact names used by kentender unit tests (must be deleted if tests leave them behind).
_KT_TEST_DISPOSABLE_ROLES: tuple[str, ...] = (
	"KT PQ Test Role",
	"KT ASG Test Role",
	"KT C008 Scope Test",
)


def is_legacy_kt_uat_role_name(name: str) -> bool:
	"""True for historical desk personas ``KT UAT …`` (not matrix Role.name)."""
	n = (name or "").strip()
	return n.startswith("KT UAT ") and len(n) > len("KT UAT ")


def iter_legacy_kt_role_names_on_site() -> tuple[str, ...]:
	"""Role names on this site that are obsolete (``KT UAT *`` or known test roles)."""
	found: set[str] = set()
	for r in _KT_TEST_DISPOSABLE_ROLES:
		if frappe.db.exists("Role", r):
			found.add(r)
	for row in frappe.get_all("Role", filters={"name": ("like", "KT UAT%")}, pluck="name") or []:
		if is_legacy_kt_uat_role_name(row):
			found.add(row)
	return tuple(sorted(found))


def _purge_one_role_permissions_and_doc(role_name: str) -> None:
	frappe.db.delete("Custom DocPerm", {"role": role_name})
	frappe.db.delete("DocPerm", {"role": role_name})
	frappe.db.delete("Has Role", {"role": role_name})
	frappe.delete_doc("Role", role_name, force=True, ignore_permissions=True, ignore_on_trash=True)


def delete_obsolete_kt_role(role_name: str) -> bool:
	"""Remove permissions and the Role row. Returns True if a Role was deleted."""
	rn = (role_name or "").strip()
	if not rn or not frappe.db.exists("Role", rn):
		return False
	frappe.flags.ignore_permissions = True
	try:
		_purge_one_role_permissions_and_doc(rn)
		return True
	finally:
		frappe.flags.ignore_permissions = False


def purge_legacy_kt_roles() -> dict[str, Any]:
	"""Delete every obsolete ``KT UAT *`` and known disposable test Role on this site."""
	deleted: list[str] = []
	failed: list[str] = []
	frappe.flags.ignore_permissions = True
	try:
		for rn in iter_legacy_kt_role_names_on_site():
			try:
				_purge_one_role_permissions_and_doc(rn)
				deleted.append(rn)
			except Exception:
				failed.append(rn)
				traceback.print_exc()
		frappe.db.commit()
	finally:
		frappe.flags.ignore_permissions = False
	frappe.clear_cache()
	return {"ok": len(failed) == 0, "roles_deleted": deleted, "roles_failed": failed}
