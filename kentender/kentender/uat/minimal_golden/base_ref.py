# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe

from kentender.uat.minimal_golden.dataset import minimal_golden_password
from kentender.uat.minimal_golden.users import ensure_department_reference_users


def _ensure_currency(code: str) -> None:
	code = (code or "").strip()
	if not code or frappe.db.exists("Currency", code):
		return
	frappe.get_doc(
		{
			"doctype": "Currency",
			"currency_name": code,
			"enabled": 1,
			"symbol": code[:3],
		}
	).insert(ignore_permissions=True)


def _upsert_doc(doctype: str, name_field: str, name: str, fields: dict[str, Any]) -> str:
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for k, v in fields.items():
			if k != name_field:
				doc.set(k, v)
		doc.save(ignore_permissions=True)
		return doc.name
	fields[name_field] = name
	doc = frappe.get_doc({"doctype": doctype, **fields})
	doc.insert(ignore_permissions=True)
	return doc.name


def load_base_ref(ds: dict[str, Any]) -> dict[str, Any]:
	"""Minimal Golden BASE-REF: entity, departments, funding source, category, method (no Store/Asset until apps exist)."""
	fy = ds.get("fiscal_year") or "2026-2027"
	cur = (ds.get("currency_code") or "KES").strip()
	_ensure_currency(cur)

	ent_spec = ds.get("entity") or {}
	ecode = ent_spec.get("entity_code")
	entity_name = _upsert_doc(
		"Procuring Entity",
		"entity_code",
		ecode,
		{
			"entity_name": ent_spec.get("entity_name") or ecode,
			"entity_type": ent_spec.get("entity_type") or "Other",
			"default_currency": cur,
		},
	)

	dept_ref_users = ensure_department_reference_users(
		ds,
		procuring_entity=entity_name,
		password=minimal_golden_password(ds),
	)

	email_by_key = {
		(r.get("key")): r.get("email")
		for r in (ds.get("users") or {}).get("internal") or []
		if r.get("key")
	}
	dept_names: list[str] = []
	for dep in ds.get("departments") or []:
		dcode = dep["department_code"]
		hod_key = dep.get("hod_email_key")
		hod_user = email_by_key.get(hod_key) if hod_key else None
		dept_name = f"{dcode}-{entity_name}"
		if frappe.db.exists("Procuring Department", dept_name):
			drow = frappe.get_doc("Procuring Department", dept_name)
			drow.department_name = dep.get("department_name") or dcode
			drow.hod_user = hod_user
			drow.active = 1
			drow.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Procuring Department",
					"department_code": dcode,
					"department_name": dep.get("department_name") or dcode,
					"procuring_entity": entity_name,
					"hod_user": hod_user,
					"active": 1,
				}
			).insert(ignore_permissions=True)
		dept_names.append(dept_name)

	fs = ds.get("funding_source") or {}
	fs_code = fs.get("funding_source_code")
	_upsert_doc(
		"Funding Source",
		"funding_source_code",
		fs_code,
		{
			"funding_source_name": fs.get("funding_source_name") or fs_code,
			"funding_source_type": fs.get("funding_source_type") or "Other",
			"active": 1,
		},
	)

	pc = ds.get("procurement_category") or {}
	_upsert_doc(
		"Procurement Category",
		"category_code",
		pc.get("category_code"),
		{
			"category_name": pc.get("category_name"),
			"category_type": pc.get("category_type") or "Goods",
			"active": 1,
		},
	)

	pm = ds.get("procurement_method") or {}
	_upsert_doc(
		"Procurement Method",
		"method_code",
		pm.get("method_code"),
		{
			"method_name": pm.get("method_name"),
			"requires_publication": int(pm.get("requires_publication") or 0),
			"requires_invitation_only": int(pm.get("requires_invitation_only") or 0),
			"allows_lotting": int(pm.get("allows_lotting") or 0),
			"allows_framework": int(pm.get("allows_framework") or 0),
			"active": 1,
		},
	)

	frappe.db.commit()
	return {
		"procuring_entity": entity_name,
		"departments": dept_names,
		"funding_source": fs_code,
		"fiscal_year": fy,
		"currency": cur,
		"department_reference_users": dept_ref_users,
	}
