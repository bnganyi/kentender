# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.minimal_golden.dataset import load_minimal_golden_dataset

PR = "Purchase Requisition"
BL = "Budget Line"


def _ok(label: str, cond: bool, detail: str = "") -> dict[str, Any]:
	return {"check": label, "ok": bool(cond), "detail": detail}


def _doctype_exists(name: str) -> bool:
	return bool(frappe.db.exists("DocType", name))


def _is_kentender_owned_doctype(doctype: str) -> bool:
	"""Avoid treating ERPNext/CRM DocTypes (e.g. Contract, Asset) as golden scenario targets."""
	mod = frappe.db.get_value("DocType", doctype, "module")
	return bool(mod and str(mod).startswith("Kentender"))


def verify_strategy_chain_integrity(ds: dict[str, Any]) -> list[dict[str, Any]]:
	"""Assert seeded strategy rows exist and parent-child DB links match the canonical dataset (GOLD-SEED-V2-003)."""
	st = ds.get("strategy") or {}
	out: list[dict[str, Any]] = []

	def _name(key: str) -> str:
		return ((st.get(key) or {}).get("name") or "").strip()

	nf = _name("national_framework")
	pl = _name("national_pillar")
	ob = _name("national_objective")
	esp = _name("entity_strategic_plan")
	pg = _name("program")
	sg = _name("sub_program")
	ind = _name("output_indicator")
	tgt = _name("performance_target")

	for label, name, dt in (
		("national_framework", nf, "National Framework"),
		("national_pillar", pl, "National Pillar"),
		("national_objective", ob, "National Objective"),
		("entity_strategic_plan", esp, "Entity Strategic Plan"),
		("program", pg, "Strategic Program"),
		("sub_program", sg, "Strategic Sub Program"),
		("output_indicator", ind, "Output Indicator"),
		("performance_target", tgt, "Performance Target"),
	):
		ok = bool(name and frappe.db.exists(dt, name))
		out.append(_ok(f"strategy_{label}_exists", ok, name or "(missing name in dataset)"))

	if not all(
		(
			frappe.db.exists("National Framework", nf),
			frappe.db.exists("National Pillar", pl),
			frappe.db.exists("National Objective", ob),
		)
	):
		return out

	pl_fw = frappe.db.get_value("National Pillar", pl, "national_framework")
	out.append(_ok("strategy_pillar_links_framework", pl_fw == nf, f"pillar.framework={pl_fw!r} expected {nf!r}"))

	ob_pl = frappe.db.get_value("National Objective", ob, "national_pillar")
	out.append(_ok("strategy_objective_links_pillar", ob_pl == pl, f"objective.pillar={ob_pl!r} expected {pl!r}"))

	if not frappe.db.exists("Entity Strategic Plan", esp):
		return out
	esp_fw = frappe.db.get_value("Entity Strategic Plan", esp, "primary_national_framework")
	out.append(_ok("strategy_plan_links_framework", esp_fw == nf, f"plan.framework={esp_fw!r} expected {nf!r}"))

	if not frappe.db.exists("Strategic Program", pg):
		return out
	row_pg = frappe.db.get_value(
		"Strategic Program",
		pg,
		["entity_strategic_plan", "national_objective"],
		as_dict=True,
	)
	out.append(
		_ok(
			"strategy_program_links_plan_and_objective",
			bool(row_pg and row_pg["entity_strategic_plan"] == esp and row_pg["national_objective"] == ob),
			f"program plan={row_pg.get('entity_strategic_plan')!r} objective={row_pg.get('national_objective')!r}",
		)
	)

	if not frappe.db.exists("Strategic Sub Program", sg):
		return out
	row_sg = frappe.db.get_value(
		"Strategic Sub Program",
		sg,
		["program", "entity_strategic_plan"],
		as_dict=True,
	)
	out.append(
		_ok(
			"strategy_sub_program_links_program",
			bool(row_sg and row_sg["program"] == pg and row_sg["entity_strategic_plan"] == esp),
			f"sub_program program={row_sg.get('program')!r} plan={row_sg.get('entity_strategic_plan')!r}",
		)
	)

	if not frappe.db.exists("Output Indicator", ind):
		return out
	row_i = frappe.db.get_value(
		"Output Indicator",
		ind,
		["sub_program", "program", "entity_strategic_plan"],
		as_dict=True,
	)
	out.append(
		_ok(
			"strategy_indicator_links_sub_program",
			bool(
				row_i
				and row_i["sub_program"] == sg
				and row_i["program"] == pg
				and row_i["entity_strategic_plan"] == esp
			),
			f"indicator hierarchy sub={row_i.get('sub_program')!r}",
		)
	)

	if not frappe.db.exists("Performance Target", tgt):
		return out
	row_t = frappe.db.get_value(
		"Performance Target",
		tgt,
		["output_indicator", "sub_program", "program", "entity_strategic_plan"],
		as_dict=True,
	)
	out.append(
		_ok(
			"strategy_target_matches_indicator_hierarchy",
			bool(
				row_t
				and row_t["output_indicator"] == ind
				and row_t["sub_program"] == sg
				and row_t["program"] == pg
				and row_t["entity_strategic_plan"] == esp
			),
			"target vs indicator chain",
		)
	)

	return out


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

	checks.extend(verify_strategy_chain_integrity(ds))

	bud = (ds.get("budget") or {}).get("budget") or {}
	bud_id = bud.get("name")
	checks.append(_ok("budget", bool(bud_id and frappe.db.exists("Budget", bud_id)), bud_id or ""))

	bl = ((ds.get("budget") or {}).get("lines") or {}).get("main") or {}
	bl_id = bl.get("name")
	checks.append(_ok("budget_line_main", bool(bl_id and frappe.db.exists(BL, bl_id)), bl_id or ""))
	if bl_id and frappe.db.exists(BL, bl_id):
		brow = frappe.db.get_value(
			BL,
			bl_id,
			[
				"performance_target",
				"output_indicator",
				"program",
				"sub_program",
				"entity_strategic_plan",
			],
			as_dict=True,
		)
		st_spec = ds.get("strategy") or {}
		exp_tgt = ((st_spec.get("performance_target") or {}).get("name") or "").strip()
		exp_ind = ((st_spec.get("output_indicator") or {}).get("name") or "").strip()
		strat_ok = bool(
			brow
			and (brow.get("performance_target") or "") == exp_tgt
			and (brow.get("output_indicator") or "") == exp_ind
		)
		checks.append(
			_ok(
				"budget_line_strategy_links_match_canonical",
				strat_ok,
				f"BL={bl_id} target={brow.get('performance_target')!r} indicator={brow.get('output_indicator')!r}",
			)
		)

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

	# Only ``bid_1`` / ``bid_2`` are seeded as Bid Submission rows. Other
	# ``future_business_ids`` entries are reserved wave placeholders; once those
	# DocTypes exist, existence checks would incorrectly fail (no row with that
	# ``name`` / stub id). Skip them here — see ``scope_note`` below.
	future = ds.get("future_business_ids") or {}
	FUTURE_SEEDED_LABELS = frozenset(
		{
			"bid_1",
			"bid_2",
			"opening_session",
			"opening_register",
			"evaluation_session",
			"evaluation_report",
			"award_decision",
			"contract",
		}
	)
	if isinstance(future, dict):
		for label, bid in future.items():
			if label == "note":
				continue
			if not bid or not isinstance(bid, str):
				continue
			if label not in FUTURE_SEEDED_LABELS:
				skipped.append(f"{label}:{bid} (reserved — not seeded in minimal golden)")
				continue
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
			"Minimal Golden: base ref → strategy → budget → users → approved PR + reservation → plan/item → Tender → two bids + bid receipt → "
			"E2E post-tender (publish, opening, evaluation session + report, award approval, contract activation) when `load_post_tender_scenario` runs. "
			"Inspection / acceptance / GRN / Kentender Asset rows are optional follow-on (stores/assets apps); future_business_ids for those remain placeholders until seeded."
		),
	}


def _future_record_exists(dt: str, value: str) -> bool:
	"""``value`` is the canonical business key (name or ``business_id``)."""
	v = value.strip()
	if dt == "Bid Submission":
		return bool(frappe.db.exists("Bid Submission", {"business_id": v}))
	if dt in ("Bid Opening Session", "Bid Opening Register", "Evaluation Session", "Evaluation Report", "Award Decision", "Procurement Contract"):
		return bool(frappe.db.exists(dt, {"business_id": v}))
	return bool(frappe.db.exists(dt, v))


def _future_id_to_doctype(label: str) -> str | None:
	m = {
		"tender": "Tender",
		"bid_1": "Bid Submission",
		"bid_2": "Bid Submission",
		"opening_session": "Bid Opening Session",
		"opening_register": "Bid Opening Register",
		"evaluation_session": "Evaluation Session",
		"evaluation_report": "Evaluation Report",
		"award_decision": "Award Decision",
		"standstill": "Standstill Period",
		"contract": "Procurement Contract",
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
