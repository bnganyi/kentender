# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""KenTender UAT bootstrap: roles and optional PR-phase test users (Wave 2 desk testing).

Roles are ensured on every after_migrate. Users are created only when you run
`bench --site kentender.midas.com execute kentender.uat.bootstrap.seed_pr_uat_users_console`
(or `seed_pr_uat_users`, System Manager only).

Default password for seeded users: `k3nTender!uat` (change on real deployments).
"""

from __future__ import annotations

import frappe
KT_UAT_ROLES = (
	("KT UAT Strategy Manager", "KenTender UAT — national/entity strategy and program chain"),
	("KT UAT Budget Officer", "KenTender UAT — budget control period, budget, and lines"),
	("KT UAT Requisitioner", "KenTender UAT — department requisitioner"),
	("KT UAT HOD", "KenTender UAT — head of department"),
	("KT UAT Finance Approver", "KenTender UAT — finance approver"),
	("KT UAT Procurement Officer", "KenTender UAT — procurement officer"),
	("KT UAT Auditor", "KenTender UAT — auditor / oversight read"),
)

# Map seed-pack style emails to role and default Desk workspace (see KenTender Seed Data.md)
PR_UAT_USERS = (
	("strategy.uat@ken-tender.test", "KT UAT Strategy Manager", "Strategy", "UAT", "KenTender Strategy"),
	("budgetofficer.uat@ken-tender.test", "KT UAT Budget Officer", "Budget", "UAT", "KenTender Budget"),
	("requisitioner.uat@ken-tender.test", "KT UAT Requisitioner", "Requisitioner", "UAT", "KenTender My Work"),
	("hod.uat@ken-tender.test", "KT UAT HOD", "HOD", "UAT", "KenTender Approvals"),
	("financeapprover.uat@ken-tender.test", "KT UAT Finance Approver", "Finance", "UAT", "KenTender Approvals"),
	("procurement.uat@ken-tender.test", "KT UAT Procurement Officer", "Procurement", "UAT", "KenTender Procurement"),
)

DEFAULT_WORKSPACE = "KenTender My Work"
DEFAULT_PASSWORD = "k3nTender!uat"


def _ensure_role(role_name: str) -> None:
	if frappe.db.exists("Role", role_name):
		return
	doc = frappe.get_doc(
		{
			"doctype": "Role",
			"role_name": role_name,
			"desk_access": 1,
			"is_custom": 1,
		}
	)
	doc.insert(ignore_permissions=True)


def ensure_uat_roles() -> None:
	for role_name, _desc in KT_UAT_ROLES:
		_ensure_role(role_name)
	frappe.db.commit()


def after_migrate() -> None:
	ensure_uat_roles()


def _upsert_pr_uat_users() -> None:
	ensure_uat_roles()
	for row in PR_UAT_USERS:
		email, role, first, last = row[0], row[1], row[2], row[3]
		default_workspace = row[4] if len(row) > 4 else DEFAULT_WORKSPACE
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"enabled": 1,
					"user_type": "System User",
					"time_zone": frappe.db.get_single_value("System Settings", "time_zone")
					or "UTC",
				}
			)
			user.insert(ignore_permissions=True)
		user = frappe.get_doc("User", email)
		user.new_password = DEFAULT_PASSWORD
		user.default_workspace = default_workspace
		user.save(ignore_permissions=True)
		existing = {r.role for r in user.roles}
		if role not in existing:
			user.append("roles", {"role": role})
			user.save(ignore_permissions=True)
	frappe.db.commit()


@frappe.whitelist()
def seed_pr_uat_users() -> None:
	"""Create PR-phase UAT users (System Manager only)."""
	frappe.only_for("System Manager")
	_upsert_pr_uat_users()


def seed_pr_uat_users_console() -> None:
	"""For `bench execute kentender.uat.bootstrap.seed_pr_uat_users_console`."""
	_upsert_pr_uat_users()
	print(
		f"OK: {len(PR_UAT_USERS)} users (Strategy/Budget + procurement chain); "
		f"password={DEFAULT_PASSWORD}; per-user default_workspace from seed list"
	)
