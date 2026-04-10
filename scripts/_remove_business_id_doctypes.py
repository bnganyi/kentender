#!/usr/bin/env python3
"""One-off: strip business_id from DocType JSON (run from repo root)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATHS = [
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/entity_strategic_plan/entity_strategic_plan.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_program/strategic_program.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_sub_program/strategic_sub_program.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/national_framework/national_framework.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/national_pillar/national_pillar.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/national_objective/national_objective.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/output_indicator/output_indicator.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/performance_target/performance_target.json",
	ROOT / "kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_revision_record/strategic_revision_record.json",
	ROOT / "kentender_budget/kentender_budget/kentender_budget/doctype/budget/budget.json",
	ROOT / "kentender_budget/kentender_budget/kentender_budget/doctype/budget_line/budget_line.json",
	ROOT / "kentender_budget/kentender_budget/kentender_budget/doctype/budget_control_period/budget_control_period.json",
	ROOT / "kentender_budget/kentender_budget/kentender_budget/doctype/budget_allocation/budget_allocation.json",
	ROOT / "kentender_budget/kentender_budget/kentender_budget/doctype/budget_revision/budget_revision.json",
	ROOT / "kentender_budget/kentender_budget/kentender_budget/doctype/budget_ledger_entry/budget_ledger_entry.json",
	ROOT / "kentender_procurement/kentender_procurement/kentender_procurement/doctype/purchase_requisition/purchase_requisition.json",
	ROOT / "kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_plan/procurement_plan.json",
	ROOT / "kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_plan_item/procurement_plan_item.json",
	ROOT / "kentender/kentender/kentender/doctype/exception_record/exception_record.json",
	ROOT / "kentender/kentender/kentender/doctype/kentender_audit_event/kentender_audit_event.json",
]


def patch(data: dict) -> bool:
	changed = False
	if data.get("autoname") == "field:business_id":
		data["autoname"] = "Prompt"
		changed = True
	fo = data.get("field_order") or []
	if "business_id" in fo:
		data["field_order"] = [x for x in fo if x != "business_id"]
		changed = True
	fields = data.get("fields") or []
	nf = [f for f in fields if f.get("fieldname") != "business_id"]
	if len(nf) != len(fields):
		data["fields"] = nf
		changed = True
	sf = (data.get("search_fields") or "").strip()
	if sf and "business_id" in sf:
		parts = [p.strip() for p in sf.split(",") if p.strip()]
		parts = ["name" if p == "business_id" else p for p in parts]
		# dedupe while preserving order
		seen = set()
		out = []
		for p in parts:
			if p not in seen:
				seen.add(p)
				out.append(p)
		data["search_fields"] = ",".join(out)
		changed = True
	return changed


def main() -> int:
	for p in PATHS:
		if not p.exists():
			print("missing", p, file=sys.stderr)
			return 1
		raw = p.read_text(encoding="utf-8")
		data = json.loads(raw)
		if not patch(data):
			print("skip (no business_id change)", p)
			continue
		p.write_text(json.dumps(data, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8")
		print("patched", p)
	return 0


if __name__ == "__main__":
	sys.exit(main())
