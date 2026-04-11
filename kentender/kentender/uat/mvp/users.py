# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.bootstrap import KT_UAT_ROLES, ensure_uat_roles


def ensure_mvp_roles() -> None:
	"""Ensure matrix Role documents (same catalogue as minimal golden / Excel Role Catalogue)."""
	ensure_uat_roles()


def seed_mvp_users(ds: dict[str, Any], password: str) -> dict[str, Any]:
	"""Upsert internal + supplier MVP users; return email→roles map summary."""
	ensure_mvp_roles()
	tz = frappe.db.get_single_value("System Settings", "time_zone") or "UTC"
	summary: dict[str, list[str]] = {}

	def upsert_user(
		email: str,
		first: str,
		last: str,
		role: str,
		*,
		user_type: str = "System User",
	):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"enabled": 1,
					"user_type": user_type,
					"time_zone": tz,
				}
			).insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.new_password = password
		user.save(ignore_permissions=True)
		existing = {r.role for r in user.roles}
		if role not in existing:
			user.append("roles", {"role": role})
			user.save(ignore_permissions=True)
		summary[email] = sorted({r.role for r in user.roles})

	uconf = ds.get("users") or {}
	for row in uconf.get("internal") or []:
		upsert_user(row["email"], row.get("first_name", "MVP"), row.get("last_name", "User"), row["role"])
	for row in uconf.get("suppliers") or []:
		upsert_user(
			row["email"],
			row.get("first_name", "MVP"),
			row.get("last_name", "Supplier"),
			row["role"],
			user_type="Website User",
		)
	frappe.db.commit()
	return {"users": summary, "roles_expected": len(KT_UAT_ROLES)}
