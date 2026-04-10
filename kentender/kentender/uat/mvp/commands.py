# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import json

import frappe

from kentender.uat.mvp.base_bud import load_base_bud
from kentender.uat.mvp.base_ref import load_base_ref
from kentender.uat.mvp.base_strat import load_base_strat
from kentender.uat.mvp.dataset import load_mvp_dataset, mvp_password
from kentender.uat.mvp.reset import reset_mvp_seed_data
from kentender.uat.mvp.sp1 import load_sp1
from kentender.uat.mvp.users import seed_mvp_users
from kentender.uat.mvp.verify import format_verify_report, verify_uat_mvp


def seed_uat_mvp() -> dict:
	"""Load MVP dataset: users → BASE-REF → BASE-STRAT → BASE-BUD → SP1."""
	frappe.flags.ignore_permissions = True
	ds = load_mvp_dataset()
	pwd = mvp_password(ds)
	summary_users = seed_mvp_users(ds, pwd)
	ref = load_base_ref(ds)
	dept_first = ref["departments"][0] if ref.get("departments") else None
	strat = load_base_strat(ds, procuring_entity=ref["procuring_entity"])
	bud = load_base_bud(
		ds,
		procuring_entity=ref["procuring_entity"],
		strategy=strat,
		departments=ref.get("departments") or [],
		funding_source_code=ref["funding_source"],
	)
	sp1 = load_sp1(
		ds,
		procuring_entity=ref["procuring_entity"],
		requesting_department=dept_first,
		strategy=strat,
		budget=bud,
		funding_source=ref["funding_source"],
	)
	frappe.db.commit()
	out = {
		"users": summary_users,
		"base_ref": ref,
		"base_strat": strat,
		"base_bud": bud,
		"sp1": sp1,
	}
	return out


def reset_uat_mvp() -> dict:
	"""Delete MVP business rows then re-run :func:`seed_uat_mvp`."""
	frappe.flags.ignore_permissions = True
	ds = load_mvp_dataset()
	reset_mvp_seed_data(ds)
	out = seed_uat_mvp()
	out["reset"] = True
	return out


def seed_uat_mvp_console() -> None:
	out = seed_uat_mvp()
	print(json.dumps(out, indent=2, default=str))


def reset_uat_mvp_console() -> None:
	out = reset_uat_mvp()
	print(json.dumps(out, indent=2, default=str))


def verify_uat_mvp_console() -> None:
	frappe.flags.ignore_permissions = True
	res = verify_uat_mvp()
	print(format_verify_report(res))
	if not res.get("ok"):
		raise SystemExit(1)


@frappe.whitelist()
def seed_uat_mvp_for_desk() -> None:
	frappe.only_for("System Manager")
	seed_uat_mvp_console()


@frappe.whitelist()
def reset_uat_mvp_for_desk() -> None:
	frappe.only_for("System Manager")
	reset_uat_mvp_console()


@frappe.whitelist()
def verify_uat_mvp_for_desk() -> None:
	frappe.only_for("System Manager")
	verify_uat_mvp_console()
