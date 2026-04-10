# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe
from frappe.permissions import add_user_permission

from kentender.uat.bootstrap import KT_UAT_ROLES, ensure_uat_roles
from kentender.uat.mvp.users import MVP_EXTRA_ROLES, _ensure_role

from kentender.uat.minimal_golden.dataset import minimal_golden_password

# Personas referenced in Minimal Golden Testing Scenario (future SP3+); desk roles for suppliers stay Website User.
GOLDEN_EXTRA_ROLES = (
	("KT UAT Opening Chair", "KenTender Minimal Golden — opening chair (future tender)"),
	("KT UAT Evaluation Chair", "KenTender Minimal Golden — evaluation chair"),
	("KT UAT Contract Manager", "KenTender Minimal Golden — contract manager"),
	("KT UAT Inspection Officer", "KenTender Minimal Golden — inspection officer"),
	("KT UAT Storekeeper", "KenTender Minimal Golden — storekeeper"),
	("KT UAT Asset Officer", "KenTender Minimal Golden — asset officer"),
)


def ensure_golden_roles() -> None:
	ensure_uat_roles()
	for role_name, _desc in MVP_EXTRA_ROLES:
		desk = 0 if role_name == "KT UAT Supplier" else 1
		_ensure_role(role_name, desk_access=desk)
	for role_name, _desc in GOLDEN_EXTRA_ROLES:
		_ensure_role(role_name, desk_access=1)
	frappe.db.commit()


def upsert_internal_system_user(row: dict[str, Any], password: str) -> bool:
	"""Create or update one **internal** golden user (desk System User) with role.

	:param row: Must include ``email`` and ``role``; optional ``first_name``, ``last_name``, ``default_workspace``.
	:returns: True if the User document was newly inserted.
	"""
	tz = frappe.db.get_single_value("System Settings", "time_zone") or "UTC"
	email = row["email"]
	role = row["role"]
	created = False
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": row.get("first_name") or "Golden",
				"last_name": row.get("last_name") or "User",
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User",
				"time_zone": tz,
			}
		).insert(ignore_permissions=True)
		created = True
	user = frappe.get_doc("User", email)
	user.new_password = password
	dw = row.get("default_workspace")
	if dw:
		user.default_workspace = dw
	user.save(ignore_permissions=True)
	existing = {r.role for r in user.roles}
	if role not in existing:
		user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
	return created


def upsert_supplier_user(row: dict[str, Any], password: str) -> bool:
	"""Create or update a Website User supplier with role (e.g. KT UAT Supplier)."""
	tz = frappe.db.get_single_value("System Settings", "time_zone") or "UTC"
	email = row["email"]
	role = row["role"]
	created = False
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": row.get("first_name") or "Supplier",
				"last_name": row.get("last_name") or "User",
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "Website User",
				"time_zone": tz,
			}
		).insert(ignore_permissions=True)
		created = True
	user = frappe.get_doc("User", email)
	user.new_password = password
	user.save(ignore_permissions=True)
	existing = {r.role for r in user.roles}
	if role not in existing:
		user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
	return created


def ensure_department_reference_users(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	password: str | None = None,
) -> dict[str, Any]:
	"""Ensure users referenced from ``departments`` (e.g. ``hod_email_key``) exist with roles.

	Creates missing **User** rows from ``users.internal`` by key, assigns the configured role,
	and grants **User Permission** on **Procuring Entity** when
	``grant_hod_entity_user_permission`` is true (default).

	Requires ``procuring_entity`` to already exist in the database.
	"""
	pwd = password if password is not None else minimal_golden_password(ds)
	ensure_golden_roles()
	internal_by_key = {
		r["key"]: r
		for r in (ds.get("users") or {}).get("internal") or []
		if r.get("key") and r.get("email") and r.get("role")
	}
	out: dict[str, Any] = {
		"hod_users_ensured": [],
		"hod_users_created": [],
		"entity_user_permissions": [],
	}
	for dep in ds.get("departments") or []:
		key = dep.get("hod_email_key")
		if not key:
			continue
		row = internal_by_key.get(key)
		if not row:
			frappe.log_error(
				title="Minimal Golden: missing users.internal row for department key",
				message=f"hod_email_key={key!r} has no matching users.internal entry.",
			)
			continue
		email = row["email"]
		if upsert_internal_system_user(row, pwd):
			out["hod_users_created"].append(email)
		out["hod_users_ensured"].append(email)
		if dep.get("grant_hod_entity_user_permission", 1):
			add_user_permission(
				"Procuring Entity",
				procuring_entity,
				email,
				ignore_permissions=True,
			)
			out["entity_user_permissions"].append(email)
	return out


def seed_minimal_golden_users(ds: dict[str, Any], password: str) -> dict[str, Any]:
	"""Upsert internal + supplier users for Minimal Golden (GOLD-SEED-005).

	Internal rows may set ``grant_entity_user_permission`` (default 1) to add **User Permission**
	on **Procuring Entity** ``entity.entity_code`` (idempotent).
	"""
	ensure_golden_roles()
	summary: dict[str, list[str]] = {}
	ent_code = (ds.get("entity") or {}).get("entity_code")

	uconf = ds.get("users") or {}
	for row in uconf.get("internal") or []:
		upsert_internal_system_user(row, password)
		if ent_code and row.get("grant_entity_user_permission", 1):
			add_user_permission(
				"Procuring Entity",
				ent_code,
				row["email"],
				ignore_permissions=True,
			)
		summary[row["email"]] = sorted(
			{r.role for r in frappe.get_doc("User", row["email"]).roles}
		)
	for row in uconf.get("suppliers") or []:
		upsert_supplier_user(row, password)
		summary[row["email"]] = sorted(
			{r.role for r in frappe.get_doc("User", row["email"]).roles}
		)
	frappe.db.commit()
	extra = len(MVP_EXTRA_ROLES) + len(GOLDEN_EXTRA_ROLES)
	return {"users": summary, "roles_expected": len(KT_UAT_ROLES) + extra}
