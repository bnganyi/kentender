# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset

PR = "Purchase Requisition"


def _ok(label: str, cond: bool, detail: str = "") -> dict[str, Any]:
	return {"check": label, "ok": bool(cond), "detail": detail}


def _doctype_exists(name: str) -> bool:
	return bool(frappe.db.exists("DocType", name))


def _is_kentender_owned_doctype(doctype: str) -> bool:
	"""Avoid treating ERPNext/CRM DocTypes (e.g. Contract, Asset) as golden scenario targets."""
	mod = frappe.db.get_value("DocType", doctype, "module")
	return bool(mod and str(mod).startswith("Kentender"))


def verify_minimal_golden(ds: dict[str, Any] | None = None) -> dict[str, Any]:
	"""Structured verification for seeded layers + future business IDs (skipped if DocTypes missing)."""
	if ds is None:
		ds = load_minimal_golden_dataset()

	checks: list[dict[str, Any]] = []
	skipped: list[str] = []

	ent = (ds.get("entity") or {}).get("entity_code")
	checks.append(_ok("procuring_entity", bool(ent and frappe.db.exists("Procuring Entity", ent)), ent or ""))

	fs = (ds.get("funding_source") or {}).get("funding_source_code")
	checks.append(_ok("funding_source", bool(fs and frappe.db.exists("Funding Source", fs)), fs or ""))

	st = (ds.get("strategy") or {}).get("entity_strategic_plan") or {}
	esp = st.get("name")
	checks.append(_ok("entity_strategic_plan", bool(esp and frappe.db.exists("Entity Strategic Plan", esp)), esp or ""))

	pt = (ds.get("strategy") or {}).get("performance_target") or {}
	pt_id = pt.get("name")
	checks.append(_ok("performance_target", bool(pt_id and frappe.db.exists("Performance Target", pt_id)), pt_id or ""))

	bud = (ds.get("budget") or {}).get("budget") or {}
	bud_id = bud.get("name")
	checks.append(_ok("budget", bool(bud_id and frappe.db.exists("Budget", bud_id)), bud_id or ""))

	bl = ((ds.get("budget") or {}).get("lines") or {}).get("main") or {}
	bl_id = bl.get("name")
	checks.append(_ok("budget_line_main", bool(bl_id and frappe.db.exists("Budget Line", bl_id)), bl_id or ""))

	pp_sec = ds.get("procurement_planning") or {}
	pp_pl = (pp_sec.get("plan") or {}).get("name")
	pp_it = (pp_sec.get("plan_item") or {}).get("name")
	if pp_pl:
		checks.append(
			_ok("procurement_plan", bool(frappe.db.exists("Procurement Plan", pp_pl)), pp_pl),
		)
	if pp_it:
		checks.append(
			_ok(
				"procurement_plan_item",
				bool(frappe.db.exists("Procurement Plan Item", pp_it)),
				pp_it,
			),
		)

	pr_spec = ds.get("purchase_requisition") or {}
	pr_bid = pr_spec.get("name")
	pr_row = {}
	if pr_bid:
		exists = frappe.db.exists(PR, pr_bid)
		pr_row = {"name": pr_bid, "exists": bool(exists)}
		if exists:
			pr_row.update(
				frappe.db.get_value(
					PR,
					pr_bid,
					[
						"workflow_state",
						"status",
						"budget_reservation_status",
						"requested_amount",
						"name",
					],
					as_dict=True,
				)
			)
		checks.append(_ok("purchase_requisition", bool(exists), pr_bid or ""))

	reservation_ok = False
	if pr_bid and frappe.db.exists(PR, pr_bid):
		ble = frappe.db.exists("Budget Ledger Entry", {"related_requisition": pr_bid})
		reservation_ok = bool(ble)
		checks.append(_ok("budget_reservation_ble", reservation_ok, "Budget Ledger Entry for PR"))

	t_spec = ds.get("tender") or {}
	t_name = (t_spec.get("name") or "").strip()
	if t_name:
		checks.append(_ok("tender", bool(frappe.db.exists("Tender", t_name)), t_name))

	br_spec = ds.get("bid_receipt") or {}
	br_biz = (br_spec.get("business_id") or "").strip()
	if br_biz:
		checks.append(
			_ok(
				"bid_receipt",
				bool(frappe.db.exists("Bid Receipt", {"business_id": br_biz})),
				br_biz,
			)
		)

	users_out: dict[str, bool] = {}
	for row in (ds.get("users") or {}).get("internal") or []:
		email = row.get("email")
		if email:
			users_out[email] = bool(frappe.db.exists("User", email))
	for row in (ds.get("users") or {}).get("suppliers") or []:
		email = row.get("email")
		if email:
			users_out[email] = bool(frappe.db.exists("User", email))

	future = ds.get("future_business_ids") or {}
	if isinstance(future, dict):
		for label, bid in future.items():
			if label == "note":
				continue
			if not bid or not isinstance(bid, str):
				continue
			# Map to doctype when implemented
			dt = _future_id_to_doctype(label)
			if not dt or not _doctype_exists(dt):
				skipped.append(f"{label}:{bid} (no DocType)")
				continue
			if not _is_kentender_owned_doctype(dt):
				skipped.append(f"{label}:{bid} (DocType {dt} is not KenTender-owned)")
				continue
			checks.append(_ok(f"future_{label}", _future_record_exists(dt, bid), bid))

	core_ok = all(c["ok"] for c in checks) and all(users_out.values())

	return {
		"ok": core_ok,
		"checks": checks,
		"purchase_requisition": pr_row,
		"users": users_out,
		"skipped_future": skipped,
		"scope_note": (
			"Minimal Golden through SP1 (approved PR + reservation), procurement plan/item, seeded Tender (manual origin), "
			"two Bid Submission rows (future_business_ids bid_1 / bid_2), and one Bid Receipt for bid_1 when bid_receipt is set in JSON. "
			"Opening/evaluation/award/contract/GRN/asset rows remain under future_business_ids until those DocTypes exist."
		),
	}


def _future_record_exists(dt: str, value: str) -> bool:
	"""``value`` is the canonical business key (name or ``business_id``)."""
	if dt == "Bid Submission":
		return bool(frappe.db.exists("Bid Submission", {"business_id": value.strip()}))
	return bool(frappe.db.exists(dt, value))


def _future_id_to_doctype(label: str) -> str | None:
	m = {
		"tender": "Tender",
		"bid_1": "Bid Submission",
		"bid_2": "Bid Submission",
		"opening_session": "Opening Session",
		"opening_register": "Opening Register",
		"evaluation_session": "Evaluation Session",
		"evaluation_report": "Evaluation Report",
		"award_decision": "Award Decision",
		"standstill": "Standstill Period",
		"contract": "Contract",
		"inspection": "Inspection Record",
		"acceptance": "Acceptance Record",
		"grn": "Goods Receipt Note",
		"asset_1": "Asset",
		"asset_2": "Asset",
	}
	return m.get(label)


def format_verify_report(result: dict[str, Any]) -> str:
	lines = [
		f"Minimal Golden verify: {'PASS' if result.get('ok') else 'FAIL'}",
		"",
		"Checks:",
	]
	for c in result.get("checks") or []:
		flag = "Y" if c.get("ok") else "N"
		lines.append(f"  [{flag}] {c.get('check')}: {c.get('detail')}")
	lines.append("")
	lines.append("Purchase Requisition:")
	lines.append(f"  {result.get('purchase_requisition')}")
	lines.append("")
	lines.append("Users:")
	for email, ok in (result.get("users") or {}).items():
		lines.append(f"  [{'Y' if ok else 'N'}] {email}")
	skip = result.get("skipped_future") or []
	if skip:
		lines.append("")
		lines.append("Skipped (future / no DocType):")
		for s in skip:
			lines.append(f"  - {s}")
	lines.append("")
	lines.append(result.get("scope_note") or "")
	return "\n".join(lines)
