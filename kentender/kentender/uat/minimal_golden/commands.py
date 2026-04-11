# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

import json
import sys
import traceback
from collections.abc import Callable

import frappe

from kentender.uat.minimal_golden.base_ref import load_base_ref
from kentender.uat.minimal_golden.bid_receipts import load_bid_receipts
from kentender.uat.minimal_golden.bid_submissions import load_bid_submissions
from kentender.uat.minimal_golden.post_tender_scenario import load_post_tender_scenario
from kentender.uat.minimal_golden.budget import (
	assert_budget_seeded_for_pr,
	assert_strategy_chain_seeded,
	load_budget,
)
from kentender.uat.minimal_golden.cleanup import cleanup_mvp_uat_data
from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset, minimal_golden_password
from kentender.uat.minimal_golden.procurement_planning import load_procurement_planning
from kentender.uat.minimal_golden.requisition import load_purchase_requisition
from kentender.uat.minimal_golden.reset import reset_minimal_golden_data
from kentender.uat.minimal_golden.tender import load_tender
from kentender.uat.minimal_golden.templates import ensure_minimal_golden_template_codes
from kentender.uat.minimal_golden.strategy import assert_strategy_context_for_pr, load_strategy
from kentender.uat.minimal_golden.users import seed_minimal_golden_users as upsert_minimal_golden_user_accounts
from kentender.uat.minimal_golden.verify import format_verify_report, verify_minimal_golden


def _assert_minimal_golden_pr_actor_users(ds: dict) -> None:
	"""Requisitioner, HOD, and finance users must exist (step 4)."""
	emails: dict[str, str] = {}
	for row in (ds.get("users") or {}).get("internal") or []:
		if row.get("key") and row.get("email"):
			emails[row["key"]] = row["email"]
	for key in ("requisitioner", "hod", "finance"):
		email = emails.get(key)
		if not email or not frappe.db.exists("User", email):
			frappe.throw(
				f"User for {key!r} ({email!r}) not found. Run step 4: seed_minimal_golden_users_console.",
				frappe.ValidationError,
			)


def _minimal_golden_console_main(fn: Callable[[], None]) -> None:
	"""Run ``fn`` for ``bench execute``.

	Frappe's ``execute`` catches *any* exception from the resolved callable and then
	tries ``eval(method_string)``, which breaks for dotted paths (``NameError:
	kentender is not defined``). Exit via ``SystemExit`` so that fallback never runs.
	"""
	try:
		fn()
	except SystemExit:
		raise
	except frappe.ValidationError as e:
		print(str(e), file=sys.stderr)
		raise SystemExit(1) from None
	except Exception:
		traceback.print_exc(file=sys.stderr)
		raise SystemExit(1) from None


def seed_minimal_golden(*, cleanup_mvp: bool = True) -> dict:
	"""	Load Minimal Golden: optional MVP cleanup → base_ref → strategy → budget → users → PR (SP1) → Tender → Bid Submissions.

	Stepwise consoles: ``seed_minimal_golden_base_ref_console`` (1), ``seed_minimal_golden_strategy_console`` (2),
	``seed_minimal_golden_budget_console`` (3), ``seed_minimal_golden_users_console`` (4),
	``seed_minimal_golden_requisition_console`` (5). The default full-seed entrypoint runs the same PR + tender + bids leg after users.

	:param cleanup_mvp: When True (default), run :func:`cleanup_mvp_uat_data` first to remove UAT-MVP rows.
	"""
	frappe.flags.ignore_permissions = True
	ds = load_minimal_golden_dataset()
	if cleanup_mvp:
		cleanup_mvp_uat_data()
	pwd = minimal_golden_password(ds)
	ref = load_base_ref(ds)
	dept_first = ref["departments"][0] if ref.get("departments") else None
	strat = load_strategy(ds, procuring_entity=ref["procuring_entity"])
	template_codes = ensure_minimal_golden_template_codes(ds)
	bud = load_budget(
		ds,
		procuring_entity=ref["procuring_entity"],
		strategy=strat,
		departments=ref.get("departments") or [],
		funding_source_code=ref["funding_source"],
	)
	frappe.db.commit()
	users = upsert_minimal_golden_user_accounts(ds, pwd)
	# Re-load departments with HOD now that users exist
	ref = load_base_ref(ds)
	dept_first = ref["departments"][0] if ref.get("departments") else None
	planning = load_procurement_planning(
		ds,
		procuring_entity=ref["procuring_entity"],
		budget=bud,
		strategy=strat,
		funding_source=ref["funding_source"],
		requesting_department=dept_first,
	)
	pr = load_purchase_requisition(
		ds,
		procuring_entity=ref["procuring_entity"],
		requesting_department=dept_first,
		strategy=strat,
		budget=bud,
		funding_source=ref["funding_source"],
	)
	td = load_tender(
		ds,
		procuring_entity=ref["procuring_entity"],
		requesting_department=dept_first,
		strategy=strat,
		budget=bud,
		funding_source=ref["funding_source"],
	)
	bs = load_bid_submissions(ds, procuring_entity=ref["procuring_entity"])
	br = load_bid_receipts(ds, procuring_entity=ref["procuring_entity"])
	post = load_post_tender_scenario(ds)
	frappe.db.commit()
	return {
		"cleanup_mvp": cleanup_mvp,
		"base_ref": ref,
		"strategy": strat,
		"template_codes": template_codes,
		"budget": bud,
		"users": users,
		"procurement_planning": planning,
		"purchase_requisition": pr,
		"tender": td,
		"bid_submissions": bs,
		"bid_receipt": br,
		"post_tender": post,
	}


def reset_minimal_golden(*, cleanup_mvp: bool = True) -> dict:
	"""Delete Minimal Golden rows, optionally clear MVP UAT, then re-seed."""
	frappe.flags.ignore_permissions = True
	ds = load_minimal_golden_dataset()
	reset_minimal_golden_data(ds)
	if cleanup_mvp:
		cleanup_mvp_uat_data()
	out = seed_minimal_golden(cleanup_mvp=False)
	out["reset"] = True
	out["cleanup_mvp_after_reset"] = cleanup_mvp
	return out


def seed_minimal_golden_base_ref_console() -> None:
	"""GOLD step 1 only: master data (entity, departments, funding, category, method)."""

	def _go() -> None:
		frappe.flags.ignore_permissions = True
		ds = load_minimal_golden_dataset()
		out = load_base_ref(ds)
		frappe.db.commit()
		print(json.dumps({"step": "base_ref", **out}, indent=2, default=str))

	_minimal_golden_console_main(_go)


def seed_minimal_golden_strategy(*, ensure_base_ref: bool = False) -> dict:
	"""GOLD step 2: national + entity strategy chain (requires procuring entity).

	:param ensure_base_ref: When True, run :func:`load_base_ref` first (idempotent shortcut).
	"""
	frappe.flags.ignore_permissions = True
	ds = load_minimal_golden_dataset()
	ref = load_base_ref(ds) if ensure_base_ref else {}
	ent = (ds.get("entity") or {}).get("entity_code")
	if ensure_base_ref:
		ent = ref.get("procuring_entity") or ent
	if not ent or not frappe.db.exists("Procuring Entity", ent):
		frappe.throw(
			f"Procuring Entity {ent!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
			frappe.ValidationError,
		)
	strat = load_strategy(ds, procuring_entity=ent)
	frappe.db.commit()
	return {
		"step": "strategy",
		"procuring_entity": ent,
		"strategy": strat,
	}


def seed_minimal_golden_strategy_console() -> None:
	"""GOLD step 2 only: strategy chain. Run step 1 first (`seed_minimal_golden_base_ref_console`)."""

	def _go() -> None:
		out = seed_minimal_golden_strategy(ensure_base_ref=False)
		print(json.dumps(out, indent=2, default=str))

	_minimal_golden_console_main(_go)


def seed_minimal_golden_budget(
	*, ensure_base_ref: bool = False, ensure_strategy: bool = False
) -> dict:
	"""GOLD step 3: budget control period, budget, main budget line (requires entity + strategy).

	:param ensure_base_ref: When True, run :func:`load_base_ref` first (idempotent).
	:param ensure_strategy: When True, run :func:`load_strategy` first (requires procuring entity).
	"""
	frappe.flags.ignore_permissions = True
	ds = load_minimal_golden_dataset()
	ref: dict = load_base_ref(ds) if ensure_base_ref else {}
	ent = ref.get("procuring_entity") or (ds.get("entity") or {}).get("entity_code")
	if ensure_base_ref:
		ent = ref.get("procuring_entity") or ent
	if not ent or not frappe.db.exists("Procuring Entity", ent):
		frappe.throw(
			f"Procuring Entity {ent!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
			frappe.ValidationError,
		)

	if ensure_strategy:
		strat = load_strategy(ds, procuring_entity=ent)
	else:
		strat = assert_strategy_chain_seeded(ds)

	departments = ref.get("departments")
	if not departments:
		departments = [f"{d['department_code']}-{ent}" for d in (ds.get("departments") or []) if d.get("department_code")]
	fs_code = ref.get("funding_source") or (ds.get("funding_source") or {}).get("funding_source_code")
	if fs_code and not frappe.db.exists("Funding Source", fs_code):
		frappe.throw(
			f"Funding Source {fs_code!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
			frappe.ValidationError,
		)
	for dname in departments:
		if not frappe.db.exists("Procuring Department", dname):
			frappe.throw(
				f"Procuring Department {dname!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
				frappe.ValidationError,
			)

	bud = load_budget(
		ds,
		procuring_entity=ent,
		strategy=strat,
		departments=departments,
		funding_source_code=fs_code,
	)
	frappe.db.commit()
	return {
		"step": "budget",
		"procuring_entity": ent,
		"budget": bud,
	}


def seed_minimal_golden_budget_console() -> None:
	"""GOLD step 3 only: budget. Run steps 1–2 first (or pass ensure flags via Python API)."""

	def _go() -> None:
		out = seed_minimal_golden_budget(ensure_base_ref=False, ensure_strategy=False)
		print(json.dumps(out, indent=2, default=str))

	_minimal_golden_console_main(_go)


def seed_minimal_golden_users(*, ensure_base_ref: bool = False) -> dict:
	"""GOLD step 4: internal + supplier users, then refresh base_ref (departments / HOD).

	Requires procuring entity from step 1. Steps 2–3 are not required for user upsert but are
	recommended before step 5 (PR) for a coherent dataset.

	:param ensure_base_ref: When True, run :func:`load_base_ref` before user upsert (idempotent shortcut).
	"""
	frappe.flags.ignore_permissions = True
	ds = load_minimal_golden_dataset()
	if ensure_base_ref:
		load_base_ref(ds)
	ent = (ds.get("entity") or {}).get("entity_code")
	if not ent or not frappe.db.exists("Procuring Entity", ent):
		frappe.throw(
			f"Procuring Entity {ent!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
			frappe.ValidationError,
		)
	pwd = minimal_golden_password(ds)
	users_out = upsert_minimal_golden_user_accounts(ds, pwd)
	ref_out = load_base_ref(ds)
	frappe.db.commit()
	return {
		"step": "users",
		"procuring_entity": ent,
		**users_out,
		"base_ref": ref_out,
	}


def seed_minimal_golden_users_console() -> None:
	"""GOLD step 4 only: users + base_ref refresh. Run step 1 first (steps 2–3 recommended before PR)."""

	def _go() -> None:
		out = seed_minimal_golden_users(ensure_base_ref=False)
		print(json.dumps(out, indent=2, default=str))

	_minimal_golden_console_main(_go)


def seed_minimal_golden_requisition(
	*,
	ensure_base_ref: bool = False,
	ensure_strategy: bool = False,
	ensure_budget: bool = False,
) -> dict:
	"""GOLD step 5: approved purchase requisition with budget reservation (SP1) and canonical Tender.

	Requires steps 1–4 (or pass ``ensure_*`` for idempotent shortcuts).

	:param ensure_base_ref: When True, run :func:`load_base_ref` first.
	:param ensure_strategy: When True, run :func:`load_strategy` first (requires procuring entity).
	:param ensure_budget: When True, run :func:`load_budget` first (requires strategy + departments + funding source).
	"""
	frappe.flags.ignore_permissions = True
	ds = load_minimal_golden_dataset()
	ref: dict = load_base_ref(ds) if ensure_base_ref else {}
	ent = ref.get("procuring_entity") or (ds.get("entity") or {}).get("entity_code")
	if ensure_base_ref:
		ent = ref.get("procuring_entity") or ent
	if not ent or not frappe.db.exists("Procuring Entity", ent):
		frappe.throw(
			f"Procuring Entity {ent!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
			frappe.ValidationError,
		)

	if ensure_strategy:
		strat = load_strategy(ds, procuring_entity=ent)
	else:
		strat = assert_strategy_context_for_pr(ds)

	departments = ref.get("departments")
	if not departments:
		departments = [f"{d['department_code']}-{ent}" for d in (ds.get("departments") or []) if d.get("department_code")]
	fs_code = ref.get("funding_source") or (ds.get("funding_source") or {}).get("funding_source_code")
	if fs_code and not frappe.db.exists("Funding Source", fs_code):
		frappe.throw(
			f"Funding Source {fs_code!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
			frappe.ValidationError,
		)
	for dname in departments:
		if not frappe.db.exists("Procuring Department", dname):
			frappe.throw(
				f"Procuring Department {dname!r} not found. Run step 1: seed_minimal_golden_base_ref_console.",
				frappe.ValidationError,
			)

	if ensure_budget:
		bud = load_budget(
			ds,
			procuring_entity=ent,
			strategy=strat,
			departments=departments,
			funding_source_code=fs_code,
		)
	else:
		bud = assert_budget_seeded_for_pr(ds)

	_assert_minimal_golden_pr_actor_users(ds)
	ref_out = load_base_ref(ds)
	dept_first = ref_out["departments"][0] if ref_out.get("departments") else None
	planning = load_procurement_planning(
		ds,
		procuring_entity=ent,
		budget=bud,
		strategy=strat,
		funding_source=ref_out["funding_source"],
		requesting_department=dept_first,
	)
	pr = load_purchase_requisition(
		ds,
		procuring_entity=ent,
		requesting_department=dept_first,
		strategy=strat,
		budget=bud,
		funding_source=ref_out["funding_source"],
	)
	td = load_tender(
		ds,
		procuring_entity=ent,
		requesting_department=dept_first,
		strategy=strat,
		budget=bud,
		funding_source=ref_out["funding_source"],
	)
	bs = load_bid_submissions(ds, procuring_entity=ent)
	br = load_bid_receipts(ds, procuring_entity=ent)
	post = load_post_tender_scenario(ds)
	frappe.db.commit()
	return {
		"step": "requisition",
		"procuring_entity": ent,
		"procurement_planning": planning,
		"purchase_requisition": pr,
		"tender": td,
		"bid_submissions": bs,
		"bid_receipt": br,
		"post_tender": post,
		"base_ref": ref_out,
	}


def seed_minimal_golden_requisition_console() -> None:
	"""GOLD step 5 only: PR + budget reservation. Run steps 1–4 first (or ``ensure_*`` via Python API)."""

	def _go() -> None:
		out = seed_minimal_golden_requisition(
			ensure_base_ref=False,
			ensure_strategy=False,
			ensure_budget=False,
		)
		print(json.dumps(out, indent=2, default=str))

	_minimal_golden_console_main(_go)


def seed_minimal_golden_console() -> None:
	def _go() -> None:
		out = seed_minimal_golden()
		print(json.dumps(out, indent=2, default=str))

	_minimal_golden_console_main(_go)


def reset_minimal_golden_console() -> None:
	def _go() -> None:
		out = reset_minimal_golden()
		print(json.dumps(out, indent=2, default=str))

	_minimal_golden_console_main(_go)


def verify_minimal_golden_console() -> None:
	def _go() -> None:
		frappe.flags.ignore_permissions = True
		res = verify_minimal_golden()
		print(format_verify_report(res))
		if not res.get("ok"):
			raise SystemExit(1)

	_minimal_golden_console_main(_go)
