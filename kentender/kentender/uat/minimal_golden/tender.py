# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

TENDER = "Tender"


def _emails_by_key(ds: dict[str, Any]) -> dict[str, str]:
	out: dict[str, str] = {}
	for row in (ds.get("users") or {}).get("internal") or []:
		if row.get("key") and row.get("email"):
			out[row["key"]] = row["email"]
	return out


def _delete_tender(docname: str) -> None:
	if docname and frappe.db.exists(TENDER, docname):
		frappe.delete_doc(TENDER, docname, force=True, ignore_permissions=True)


def load_tender(
	ds: dict[str, Any],
	*,
	procuring_entity: str,
	requesting_department: str | None,
	strategy: dict[str, Any],
	budget: dict[str, Any],
	funding_source: str,
) -> dict[str, Any]:
	"""Create canonical Tender (manual origin) for Minimal Golden; idempotent on fixed name."""
	spec = ds.get("tender") or {}
	if not spec:
		return {}
	name = (spec.get("name") or "").strip()
	if not name:
		return {}

	business_id = (spec.get("business_id") or name).strip()
	_delete_tender(name)

	em = _emails_by_key(ds)
	cur = (ds.get("currency_code") or "KES").strip()
	pc = (ds.get("procurement_category") or {}).get("category_code") or ""

	row: dict[str, Any] = {
		"doctype": TENDER,
		"name": name,
		"business_id": business_id,
		"title": (spec.get("title") or "Golden tender").strip(),
		"tender_number": (spec.get("tender_number") or name).strip(),
		"workflow_state": "Draft",
		"status": "Draft",
		"approval_status": "Draft",
		"origin_type": (spec.get("origin_type") or "Manual").strip(),
		"procuring_entity": procuring_entity,
		"requesting_department": requesting_department,
		"procurement_officer": em.get("procurement"),
		"procurement_method": (spec.get("procurement_method") or "Open National Tender").strip(),
		"tender_type": (spec.get("tender_type") or "Goods").strip(),
		"currency": cur,
		"estimated_amount": float(spec.get("estimated_amount") or 0),
		"entity_strategic_plan": strategy.get("entity_strategic_plan"),
		"program": strategy.get("strategic_program"),
		"sub_program": strategy.get("strategic_sub_program"),
		"output_indicator": strategy.get("output_indicator"),
		"performance_target": strategy.get("performance_target"),
		"national_objective": strategy.get("national_objective"),
		"budget": budget.get("budget"),
		"budget_line": budget.get("budget_line_main"),
		"funding_source": funding_source,
		"publication_datetime": spec.get("publication_datetime"),
		"clarification_deadline": spec.get("clarification_deadline"),
		"submission_deadline": spec.get("submission_deadline"),
		"opening_datetime": spec.get("opening_datetime"),
	}
	if pc:
		row["procurement_category"] = pc

	doc = frappe.get_doc(row)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "business_id": doc.business_id}
