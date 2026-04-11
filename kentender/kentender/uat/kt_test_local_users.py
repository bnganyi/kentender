# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Unit-test fixture users: ``_kt_*@test.local`` emails created by KenTender tests.

Shared-site test runs should delete these in tearDown (or use :func:`purge_kt_test_local_users`).
"""

from __future__ import annotations

import traceback
from typing import Any

import frappe

__all__ = [
	"delete_kt_test_local_user",
	"is_kt_test_local_email",
	"iter_kt_test_local_user_emails",
	"purge_kt_test_local_users",
]


def is_kt_test_local_email(email: str) -> bool:
	"""True for the convention ``_kt_*@test.local`` used by procurement/strategy tests."""
	e = (email or "").strip().lower()
	return e.startswith("_kt_") and e.endswith("@test.local")


def iter_kt_test_local_user_emails() -> tuple[str, ...]:
	"""Return User names (emails) on this site matching :func:`is_kt_test_local_email`."""
	out: list[str] = []
	for name in frappe.get_all("User", filters={"name": ("like", "%@test.local")}, pluck="name") or []:
		if is_kt_test_local_email(name):
			out.append(name)
	return tuple(sorted(out))


def delete_kt_test_local_user(email: str) -> bool:
	"""Delete one fixture user if it exists. Returns True if a row was removed."""
	en = (email or "").strip()
	if not en or not is_kt_test_local_email(en):
		return False
	if not frappe.db.exists("User", en):
		return False
	frappe.delete_doc("User", en, force=True, ignore_permissions=True)
	return True


def purge_kt_test_local_users() -> dict[str, Any]:
	"""Delete every ``User`` whose email matches ``_kt_*@test.local``."""
	deleted: list[str] = []
	failed: list[str] = []
	frappe.flags.ignore_permissions = True
	try:
		for email in iter_kt_test_local_user_emails():
			try:
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
				deleted.append(email)
			except Exception:
				failed.append(email)
				traceback.print_exc()
		frappe.db.commit()
	finally:
		frappe.flags.ignore_permissions = False
	return {
		"ok": len(failed) == 0,
		"users_deleted": deleted,
		"users_failed": failed,
	}
