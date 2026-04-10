# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Pairwise fragmentation heuristics for Procurement Plan Items (PROC-STORY-017).

Deferred (no supplier / policy masters on PPI yet):
- **Repeated Same Supplier Pattern:** PPI has no supplier field — intentionally not implemented.
- **Threshold Avoidance Risk:** requires a registered monetary threshold policy — hook for a later PROC policy story.

Rollup rule: After alerts exist, ``_refresh_fragmentation_flags_for_plan`` sets
``fragmentation_alert_status`` to **Warning** and ``fragmentation_risk_score`` to
``min(1.0, 0.25 * open_alert_count)`` for items referenced by any **Open** alert
for the plan (pair names are recovered from ``business_id``). Items on the plan not
referenced by any Open alert are reset to **Not Assessed** and risk score **0**.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import frappe
from frappe.utils import getdate, now_datetime

from kentender_procurement.services.procurement_plan_totals import (
	EXCLUDED_PPI_STATUSES,
	PPI_DOCTYPE,
)

PP_DOCTYPE = "Procurement Plan"
PFRA_DOCTYPE = "Plan Fragmentation Alert"

BUSINESS_ID_VERSION = "v1"
BUSINESS_ID_PREFIX = "FRA"

RULE_KEY_CATEGORY = "cat"
RULE_KEY_BUDGET_LINE = "budget"
RULE_KEY_DEPARTMENT = "dept"
RULE_KEY_SCHEDULE = "schedule"
RULE_KEY_TITLE = "title"
RULE_KEY_MANUAL_OVERRIDE = "manual_override"

_ALERT_SIMILAR_DEMAND = "Similar Demand Split"
_ALERT_DEPT = "Duplicate Department Demand"
_ALERT_SCHEDULE = "Duplicate Schedule Window"
_ALERT_MANUAL = "Manual Override Risk"


@dataclass
class FragmentationScanConfig:
	"""Tunables for fragmentation scan."""

	schedule_proximity_days: int = 14
	min_title_chars: int = 12
	pairwise_item_cap: int = 200


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _normalize_title(title: str | None) -> str:
	return _strip(title).lower()


def _dept_for_item(row: dict[str, Any]) -> str:
	rd = _strip(row.get("requesting_department"))
	if rd:
		return rd
	return _strip(row.get("responsible_department"))


def _item_label(row: dict[str, Any]) -> str:
	t = _strip(row.get("title")) or row.get("name") or ""
	n = row.get("name") or ""
	return f"{n} ({t})" if t != n else n


def _title_similarity(a: str | None, b: str | None, min_chars: int) -> bool:
	na = _normalize_title(a)
	nb = _normalize_title(b)
	if not na or not nb:
		return False
	if na == nb:
		return True
	if len(na) < min_chars or len(nb) < min_chars:
		return False
	return na in nb or nb in na


def _schedule_pair_match(
	pub_a,
	aw_a,
	pub_b,
	aw_b,
	proximity_days: int,
) -> bool:
	"""True when both items have publication + award dates and windows overlap or starts are near."""
	if not (pub_a and aw_a and pub_b and aw_b):
		return False
	d1p, d1a = getdate(pub_a), getdate(aw_a)
	d2p, d2a = getdate(pub_b), getdate(aw_b)
	s1_start: date = min(d1p, d1a)
	s1_end: date = max(d1p, d1a)
	s2_start: date = min(d2p, d2a)
	s2_end: date = max(d2p, d2a)
	if s1_start <= s2_end and s2_start <= s1_end:
		return True
	return abs((s1_start - s2_start).days) <= proximity_days


def _ordered_pair_names(ni: str, nj: str) -> tuple[str, str]:
	if ni <= nj:
		return ni, nj
	return nj, ni


def _make_business_id(
	procurement_plan: str,
	alert_type: str,
	name_i: str,
	name_j: str,
	rule_key: str,
) -> str:
	lo, hi = _ordered_pair_names(name_i, name_j)
	# Order: FRA | v1 | plan | alert_type | min_name | max_name | rule_key
	return "|".join(
		[
			BUSINESS_ID_PREFIX,
			BUSINESS_ID_VERSION,
			procurement_plan,
			alert_type,
			lo,
			hi,
			rule_key,
		]
	)


def _pair_item_names_from_business_id(business_id: str) -> tuple[str, str] | None:
	parts = (business_id or "").split("|")
	if len(parts) < 7:
		return None
	if parts[0] != BUSINESS_ID_PREFIX or parts[1] != BUSINESS_ID_VERSION:
		return None
	return parts[4], parts[5]


def _pfra_exists(procurement_plan: str, business_id: str) -> bool:
	return bool(
		frappe.db.exists(PFRA_DOCTYPE, {"procurement_plan": procurement_plan, "business_id": business_id})
	)


def _collect_base_rules_for_pair(
	row_i: dict[str, Any],
	row_j: dict[str, Any],
	config: FragmentationScanConfig,
) -> list[tuple[str, str, str]]:
	"""Return list of (rule_key, alert_type, summary) for base heuristics."""
	out: list[tuple[str, str, str]] = []
	li, lj = _item_label(row_i), _item_label(row_j)

	cat_i = _strip(row_i.get("procurement_category"))
	cat_j = _strip(row_j.get("procurement_category"))
	if cat_i and cat_i == cat_j:
		out.append(
			(
				RULE_KEY_CATEGORY,
				_ALERT_SIMILAR_DEMAND,
				f"Same procurement category ({cat_i}): {li}; {lj}",
			)
		)

	bl_i = _strip(row_i.get("budget_line"))
	bl_j = _strip(row_j.get("budget_line"))
	if bl_i and bl_i == bl_j:
		out.append(
			(
				RULE_KEY_BUDGET_LINE,
				_ALERT_SIMILAR_DEMAND,
				f"Same budget line ({bl_i}): {li}; {lj}",
			)
		)

	d_i, d_j = _dept_for_item(row_i), _dept_for_item(row_j)
	if d_i and d_i == d_j:
		out.append(
			(
				RULE_KEY_DEPARTMENT,
				_ALERT_DEPT,
				f"Same department ({d_i}): {li}; {lj}",
			)
		)

	if _schedule_pair_match(
		row_i.get("planned_publication_date"),
		row_i.get("planned_award_date"),
		row_j.get("planned_publication_date"),
		row_j.get("planned_award_date"),
		config.schedule_proximity_days,
	):
		pi, ai = row_i.get("planned_publication_date"), row_i.get("planned_award_date")
		pj, aj = row_j.get("planned_publication_date"), row_j.get("planned_award_date")
		out.append(
			(
				RULE_KEY_SCHEDULE,
				_ALERT_SCHEDULE,
				f"Schedule proximity/overlap (pub/award {pi}–{ai} vs {pj}–{aj}): {li}; {lj}",
			)
		)

	if _title_similarity(row_i.get("title"), row_j.get("title"), config.min_title_chars):
		ts_i = _strip(row_i.get("title"))
		ts_j = _strip(row_j.get("title"))
		out.append(
			(
				RULE_KEY_TITLE,
				_ALERT_SIMILAR_DEMAND,
				f"Similar titles ({ts_i!r} / {ts_j!r}): {li}; {lj}",
			)
		)

	return out


def _severity_for_pair(rule_count_for_pair: int) -> tuple[str, float]:
	if rule_count_for_pair >= 2:
		return "High", 0.75
	return "Medium", 0.5


def _refresh_fragmentation_flags_for_plan(plan_name: str) -> None:
	"""Sync PPI fragmentation fields from Open Plan Fragmentation Alerts on this plan."""
	plan_name = _strip(plan_name)
	if not plan_name:
		return

	alert_rows = frappe.get_all(
		PFRA_DOCTYPE,
		filters={"procurement_plan": plan_name, "status": "Open"},
		pluck="business_id",
	) or []

	counts: dict[str, int] = {}
	for bid in alert_rows:
		pair = _pair_item_names_from_business_id(bid or "")
		if not pair:
			continue
		for item_name in pair:
			counts[item_name] = counts.get(item_name, 0) + 1

	item_names = (
		frappe.get_all(
			PPI_DOCTYPE,
			filters={"procurement_plan": plan_name},
			pluck="name",
		)
		or []
	)

	for item_name in item_names:
		n = counts.get(item_name, 0)
		if n:
			frappe.db.set_value(
				PPI_DOCTYPE,
				item_name,
				{
					"fragmentation_alert_status": "Warning",
					"fragmentation_risk_score": min(1.0, 0.25 * n),
				},
				update_modified=False,
			)
		else:
			frappe.db.set_value(
				PPI_DOCTYPE,
				item_name,
				{
					"fragmentation_alert_status": "Not Assessed",
					"fragmentation_risk_score": 0,
				},
				update_modified=False,
			)


def run_fragmentation_scan_for_plan(
	procurement_plan: str,
	*,
	dry_run: bool = False,
	config: FragmentationScanConfig | None = None,
) -> dict[str, Any]:
	"""Pairwise-scan active Procurement Plan Items and insert Plan Fragmentation Alerts.

	Returns counts, duplicate skips, and inserted alert names. On ``dry_run``, no writes
	and ``candidates`` lists would-be rows. If item count exceeds ``pairwise_item_cap``,
	returns an error dict without scanning.
	"""
	cfg = config or FragmentationScanConfig()
	plan = _strip(procurement_plan)
	out: dict[str, Any] = {
		"items_scanned": 0,
		"alerts_created": 0,
		"alerts_skipped_duplicate": 0,
		"alert_names": [],
		"warning": None,
	}

	if not plan:
		out["error"] = "missing_plan"
		return out
	if not frappe.db.exists(PP_DOCTYPE, plan):
		out["error"] = "plan_not_found"
		return out

	status_filter = {"status": ("not in", list(EXCLUDED_PPI_STATUSES))}
	items = frappe.get_all(
		PPI_DOCTYPE,
		filters={"procurement_plan": plan, **status_filter},
		fields=[
			"name",
			"title",
			"procurement_category",
			"budget_line",
			"requesting_department",
			"responsible_department",
			"origin_type",
			"planned_publication_date",
			"planned_award_date",
		],
		order_by="name asc",
	) or []

	n = len(items)
	out["items_scanned"] = n

	if n > cfg.pairwise_item_cap:
		out["error"] = "item_count_exceeds_cap"
		out["cap"] = cfg.pairwise_item_cap
		out["items_count"] = n
		return out

	candidates: list[dict[str, Any]] = []

	for i in range(n):
		row_i = items[i]
		ni = row_i["name"]
		for j in range(i + 1, n):
			row_j = items[j]
			nj = row_j["name"]
			base = _collect_base_rules_for_pair(row_i, row_j, cfg)
			if not base:
				continue

			manual_any = _strip(row_i.get("origin_type")) == "Manual" or _strip(
				row_j.get("origin_type")
			) == "Manual"

			if manual_any:
				summary_bits = [x[2] for x in base]
				summary = "Manual origin with fragmentation signals — " + " | ".join(summary_bits)
				rel = _ordered_pair_names(ni, nj)[0]
				bid = _make_business_id(plan, _ALERT_MANUAL, ni, nj, RULE_KEY_MANUAL_OVERRIDE)
				severity, risk = "Low", 0.35
				row_payload = {
					"business_id": bid,
					"alert_type": _ALERT_MANUAL,
					"severity": severity,
					"risk_score": risk,
					"rule_trigger_summary": summary,
					"related_plan_item": rel,
				}
				if dry_run:
					candidates.append(row_payload)
					continue
				if _pfra_exists(plan, bid):
					out["alerts_skipped_duplicate"] += 1
					continue
				doc = frappe.get_doc(
					{
						"doctype": PFRA_DOCTYPE,
						**row_payload,
						"procurement_plan": plan,
						"status": "Open",
						"raised_on": now_datetime(),
						"raised_by_system": 1,
					}
				)
				doc.insert(ignore_permissions=True)
				out["alerts_created"] += 1
				out["alert_names"].append(doc.name)
				continue

			distinct_rules = sorted({r[0] for r in base})
			sev, rk = _severity_for_pair(len(distinct_rules))
			for rule_key, alert_type, summary in base:
				bid = _make_business_id(plan, alert_type, ni, nj, rule_key)
				rel = _ordered_pair_names(ni, nj)[0]
				row_payload = {
					"business_id": bid,
					"alert_type": alert_type,
					"severity": sev,
					"risk_score": rk,
					"rule_trigger_summary": summary,
					"related_plan_item": rel,
				}
				if dry_run:
					candidates.append(row_payload)
					continue
				if _pfra_exists(plan, bid):
					out["alerts_skipped_duplicate"] += 1
					continue
				doc = frappe.get_doc(
					{
						"doctype": PFRA_DOCTYPE,
						**row_payload,
						"procurement_plan": plan,
						"status": "Open",
						"raised_on": now_datetime(),
						"raised_by_system": 1,
					}
				)
				doc.insert(ignore_permissions=True)
				out["alerts_created"] += 1
				out["alert_names"].append(doc.name)

	if dry_run:
		out["candidates"] = candidates
		out["candidates_count"] = len(candidates)

	if not dry_run:
		_refresh_fragmentation_flags_for_plan(plan)

	return out


__all__ = [
	"FragmentationScanConfig",
	"run_fragmentation_scan_for_plan",
	"_refresh_fragmentation_flags_for_plan",
]
