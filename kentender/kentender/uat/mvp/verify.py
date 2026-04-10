# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.mvp.dataset import load_mvp_dataset

PR = "Purchase Requisition"


def _ok(label: str, cond: bool, detail: str = "") -> dict[str, Any]:
	return {"check": label, "ok": bool(cond), "detail": detail}


def verify_uat_mvp(ds: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Return structured verification suitable for printing; does not throw."""
	if ds is None:
		ds = load_mvp_dataset()

	checks: list[dict[str, Any]] = []
	ent = (ds.get("entity") or {}).get("entity_code")
	checks.append(_ok("procuring_entity", bool(ent and frappe.db.exists("Procuring Entity", ent)), ent or ""))

	fs = (ds.get("funding_source") or {}).get("funding_source_code")
	checks.append(_ok("funding_source", bool(fs and frappe.db.exists("Funding Source", fs)), fs or ""))

	st = (ds.get("strategy") or {}).get("entity_strategic_plan") or {}
	esp = st.get("name")
	checks.append(_ok("entity_strategic_plan", bool(esp and frappe.db.exists("Entity Strategic Plan", esp)), esp or ""))

	bud = (ds.get("budget") or {}).get("budget") or {}
	bud_id = bud.get("name")
	checks.append(_ok("budget", bool(bud_id and frappe.db.exists("Budget", bud_id)), bud_id or ""))

	bl_h = ((ds.get("budget") or {}).get("lines") or {}).get("healthy") or {}
	bl_id = bl_h.get("name")
	checks.append(_ok("budget_line_healthy", bool(bl_id and frappe.db.exists("Budget Line", bl_id)), bl_id or ""))

	pr_summary = {}
	for scenario, spec in (ds.get("purchase_requisitions") or {}).items():
		bid = (spec or {}).get("name")
		if not bid:
			continue
		exists = frappe.db.exists(PR, bid)
		row = {"name": bid, "exists": bool(exists)}
		if exists:
			row.update(
				frappe.db.get_value(
					PR,
					bid,
					["workflow_state", "status", "budget_reservation_status", "name"],
					as_dict=True,
				)
			)
		pr_summary[scenario] = row
		checks.append(_ok(f"pr_{scenario}", bool(exists), bid))

	users_out: dict[str, bool] = {}
	for row in (ds.get("users") or {}).get("internal") or []:
		email = row.get("email")
		if email:
			users_out[email] = bool(frappe.db.exists("User", email))
	for row in (ds.get("users") or {}).get("suppliers") or []:
		email = row.get("email")
		if email:
			users_out[email] = bool(frappe.db.exists("User", email))

	all_ok = all(c["ok"] for c in checks) and all(users_out.values())

	return {
		"ok": all_ok,
		"checks": checks,
		"purchase_requisitions": pr_summary,
		"users": users_out,
		"scope_note": "MVP through PR only: procurement_plan_ids / tender_ids / bid_ids / opening_session not seeded (n/a).",
	}


def format_verify_report(result: dict[str, Any]) -> str:
	lines = [
		f"MVP verify: {'PASS' if result.get('ok') else 'FAIL'}",
		"",
		"Checks:",
	]
	for c in result.get("checks") or []:
		flag = "Y" if c.get("ok") else "N"
		lines.append(f"  [{flag}] {c.get('check')}: {c.get('detail')}")
	lines.append("")
	lines.append("Purchase Requisitions:")
	for k, v in (result.get("purchase_requisitions") or {}).items():
		lines.append(f"  - {k}: {v}")
	lines.append("")
	lines.append("Users:")
	for email, ok in (result.get("users") or {}).items():
		lines.append(f"  [{'Y' if ok else 'N'}] {email}")
	lines.append("")
	lines.append(result.get("scope_note") or "")
	return "\n".join(lines)
