# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Remove KenTender UAT / MVP / minimal-golden seed data from a site without re-seeding.

Use before loading a new golden seed. Runs:

1. :func:`kentender.uat.mvp.reset.reset_mvp_seed_data`
2. :func:`kentender.uat.minimal_golden.reset.reset_minimal_golden_data`
3. Deletes Minimal Golden PR workflow policy + route template (``MG_DEFAULT_PR`` / ``MG_PR_HOD_FIN``) if present
4. Optionally deletes **User** rows for emails listed in ``minimal_golden_canonical.json``
   (MVP seed uses the same personas; no separate UAT-only user list).

Console::

    bench --site kentender.midas.com execute kentender.uat.wipe_test_data.wipe_uat_golden_test_data_console

One-off removal of **obsolete** seed users from older bootstraps (PR-phase desk UAT + pre–golden-merge MVP emails)::

    bench --site kentender.midas.com execute kentender.uat.wipe_test_data.purge_legacy_uat_seed_users_console

Removal of **pytest / bench test** fixture users (``_kt_*@test.local``)::

    bench --site kentender.midas.com execute kentender.uat.wipe_test_data.purge_kt_test_local_users_console

Removal of obsolete **Frappe Role** documents (historical ``KT UAT *`` personas and disposable test roles)::

    bench --site kentender.midas.com execute kentender.uat.wipe_test_data.purge_legacy_kt_roles_console
"""

from __future__ import annotations

import sys
import traceback
from typing import Any

import frappe

from kentender.uat.kt_test_local_users import purge_kt_test_local_users as _purge_kt_test_local_users
from kentender.uat.legacy_kt_roles import purge_legacy_kt_roles as _purge_legacy_kt_roles
from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset
from kentender.uat.minimal_golden.reset import reset_minimal_golden_data
from kentender.uat.mvp.dataset import load_mvp_dataset
from kentender.uat.mvp.reset import reset_mvp_seed_data

POLICY_CODE_MG_PR = "MG_DEFAULT_PR"
TEMPLATE_CODE_MG_PR = "MG_PR_HOD_FIN"

_PROTECTED_USERS = frozenset(
	{
		"Administrator",
		"Guest",
		"administrator",
		"guest",
	}
)

# Removed from code: ``kentender.uat.bootstrap`` PR-phase desk list (historical ``seed_pr_uat_users``).
_LEGACY_PR_PHASE_UAT_EMAILS: tuple[str, ...] = (
	"budgetofficer.uat@ken-tender.test",
	"financeapprover.uat@ken-tender.test",
	"hod.uat@ken-tender.test",
	"procurement.uat@ken-tender.test",
	"requisitioner.uat@ken-tender.test",
	"strategy.uat@ken-tender.test",
)

# MVP pack used separate ``*.uat-mvp@`` emails before aligning to minimal golden.
_LEGACY_MVP_UAT_MVP_EMAILS: tuple[str, ...] = (
	"accounting.uat-mvp@ken-tender.test",
	"evaluator.uat-mvp@ken-tender.test",
	"finance.uat-mvp@ken-tender.test",
	"hod.uat-mvp@ken-tender.test",
	"procurement.uat-mvp@ken-tender.test",
	"requisitioner.uat-mvp@ken-tender.test",
	"supplier.uat-mvp@ken-tender.test",
	"supplier2.uat-mvp@ken-tender.test",
)

LEGACY_SEED_USER_EMAILS: tuple[str, ...] = tuple(
	sorted(frozenset(_LEGACY_PR_PHASE_UAT_EMAILS) | frozenset(_LEGACY_MVP_UAT_MVP_EMAILS))
)


def collect_uat_seed_user_emails() -> tuple[str, ...]:
	"""Emails for minimal-golden seed users (single canonical desk/portal test set)."""
	emails: set[str] = set()
	ds_mg = load_minimal_golden_dataset()
	for section in ("internal", "suppliers"):
		for row in (ds_mg.get("users") or {}).get(section) or []:
			email = (row.get("email") or "").strip()
			if email:
				emails.add(email)
	return tuple(sorted(emails))


def _delete_doc_by_field(doctype: str, field: str, value: str) -> bool:
	"""Delete first document matching ``field == value``; return True if deleted."""
	if not frappe.db.exists(doctype, {field: value}):
		return False
	name = frappe.db.get_value(doctype, {field: value}, "name")
	if not name:
		return False
	frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
	return True


def _delete_minimal_golden_pr_workflow_artifacts() -> tuple[bool, bool]:
	"""Remove MG PR policy (depends on template); then template."""
	pol_deleted = _delete_doc_by_field("KenTender Workflow Policy", "policy_code", POLICY_CODE_MG_PR)
	tpl_deleted = _delete_doc_by_field("KenTender Approval Route Template", "template_code", TEMPLATE_CODE_MG_PR)
	return pol_deleted, tpl_deleted


def _delete_seed_users(emails: tuple[str, ...]) -> tuple[list[str], list[str]]:
	"""Delete users by email; skip protected system users."""
	deleted: list[str] = []
	failed: list[str] = []
	for email in emails:
		en = email.strip()
		if not en or en in _PROTECTED_USERS:
			continue
		if not frappe.db.exists("User", en):
			continue
		try:
			frappe.delete_doc("User", en, force=True, ignore_permissions=True)
			deleted.append(en)
		except Exception:
			failed.append(en)
			traceback.print_exc()
	return deleted, failed


def purge_legacy_uat_seed_users() -> dict[str, Any]:
	"""Delete **User** rows for obsolete PR-phase and old MVP seed emails only.

	Does not touch minimal-golden personas (``*.test@ken-tender.test``). Safe to run
	multiple times (skips missing users).
	"""
	frappe.flags.ignore_permissions = True
	try:
		deleted, failed = _delete_seed_users(LEGACY_SEED_USER_EMAILS)
		frappe.db.commit()
		return {
			"ok": len(failed) == 0,
			"users_deleted": deleted,
			"users_failed": failed,
			"candidates": list(LEGACY_SEED_USER_EMAILS),
		}
	finally:
		frappe.flags.ignore_permissions = False


def purge_legacy_uat_seed_users_console() -> None:
	"""``bench execute`` entry point; exits non-zero if any delete failed."""
	try:
		result = purge_legacy_uat_seed_users()
	except SystemExit:
		raise
	except Exception:
		traceback.print_exc(file=sys.stderr)
		raise SystemExit(1) from None

	print(
		f"Legacy seed user purge: deleted {len(result['users_deleted'])} of "
		f"{len(LEGACY_SEED_USER_EMAILS)} candidates."
	)
	print(f"Deleted: {', '.join(result['users_deleted']) or '(none)'}")
	if result["users_failed"]:
		print(f"Failed: {', '.join(result['users_failed'])}", file=sys.stderr)
		raise SystemExit(1)
	print("OK: obsolete PR-phase / uat-mvp seed users removed (golden users unchanged).")


def purge_kt_test_local_users_console() -> None:
	"""``bench execute`` entry point for :func:`kentender.uat.kt_test_local_users.purge_kt_test_local_users`."""
	try:
		result = _purge_kt_test_local_users()
	except SystemExit:
		raise
	except Exception:
		traceback.print_exc(file=sys.stderr)
		raise SystemExit(1) from None

	print(
		f"KT test.local user purge: deleted {len(result['users_deleted'])} user(s)."
	)
	print(f"Deleted: {', '.join(result['users_deleted']) or '(none)'}")
	if result["users_failed"]:
		print(f"Failed: {', '.join(result['users_failed'])}", file=sys.stderr)
		raise SystemExit(1)
	print("OK: _kt_*@test.local fixture users removed.")


def purge_legacy_kt_roles_console() -> None:
	"""``bench execute`` entry point for :func:`kentender.uat.legacy_kt_roles.purge_legacy_kt_roles`."""
	try:
		result = _purge_legacy_kt_roles()
	except SystemExit:
		raise
	except Exception:
		traceback.print_exc(file=sys.stderr)
		raise SystemExit(1) from None

	print(f"Legacy KT Role purge: removed {len(result['roles_deleted'])} role(s).")
	print(f"Deleted: {', '.join(result['roles_deleted']) or '(none)'}")
	if result["roles_failed"]:
		print(f"Failed: {', '.join(result['roles_failed'])}", file=sys.stderr)
		raise SystemExit(1)
	print("OK: obsolete KT UAT / test Role documents removed (matrix roles unchanged).")


def wipe_uat_golden_test_data(*, delete_users: bool = True) -> dict[str, Any]:
	"""Remove MVP + minimal golden business data; optional canonical seed users. Does not re-seed."""
	frappe.flags.ignore_permissions = True
	try:
		reset_mvp_seed_data(load_mvp_dataset())
		reset_minimal_golden_data(load_minimal_golden_dataset())
		pol_gone, tpl_gone = _delete_minimal_golden_pr_workflow_artifacts()
		deleted_users: list[str] = []
		failed_users: list[str] = []
		if delete_users:
			deleted_users, failed_users = _delete_seed_users(collect_uat_seed_user_emails())
		frappe.db.commit()
		return {
			"ok": len(failed_users) == 0,
			"mvp_reset": True,
			"minimal_golden_reset": True,
			"mg_pr_workflow_policy_removed": pol_gone,
			"mg_pr_route_template_removed": tpl_gone,
			"users_deleted": deleted_users,
			"users_failed": failed_users,
		}
	finally:
		frappe.flags.ignore_permissions = False


def wipe_uat_golden_test_data_console() -> None:
	"""Entry point for ``bench execute`` (prints summary, exits non-zero if any user delete failed)."""
	try:
		result = wipe_uat_golden_test_data(delete_users=True)
	except SystemExit:
		raise
	except Exception:
		traceback.print_exc(file=sys.stderr)
		raise SystemExit(1) from None

	print(
		"Wipe: MVP + Minimal Golden business data cleared; "
		f"MG PR policy/template removed: policy={result['mg_pr_workflow_policy_removed']}, "
		f"template={result['mg_pr_route_template_removed']}"
	)
	print(f"Users deleted ({len(result['users_deleted'])}): {', '.join(result['users_deleted']) or '(none)'}")
	if result["users_failed"]:
		print(f"Users failed ({len(result['users_failed'])}): {', '.join(result['users_failed'])}", file=sys.stderr)
		raise SystemExit(1)
	print("OK: UAT / golden test data removed (no re-seed).")
