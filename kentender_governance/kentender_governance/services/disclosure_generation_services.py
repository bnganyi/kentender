# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-037: create **KenTender Public Disclosure Record** from non-sensitive field allowlists only."""

from __future__ import annotations

import html
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

PDR = "KenTender Public Disclosure Record"
DS = "KenTender Disclosure Dataset"

TENDER = "Tender"
PC = "Procurement Contract"

# Explicit allowlists — no financial amounts, personal IDs, or free-text large fields.
_SAFE_FIELDS: dict[str, list[str]] = {
	TENDER: ["title", "tender_number", "status", "procurement_method"],
	PC: ["contract_title", "business_id", "supplier", "status", "currency", "contract_start_date"],
}


def _build_summary_html(object_type: str, data: dict[str, Any]) -> str:
	parts: list[str] = []
	for key in _SAFE_FIELDS.get(object_type, []):
		val = data.get(key)
		if val is None or val == "":
			continue
		parts.append(f"<p><b>{html.escape(key)}</b>: {html.escape(str(val))}</p>")
	if not parts:
		return f"<p><i>{html.escape(_('No non-sensitive fields available for disclosure.'))}</i></p>"
	return "\n".join(parts)


def generate_public_disclosure(
	object_type: str,
	object_id: str,
	*,
	disclosure_stage: str,
	business_id: str | None = None,
	published_by_user: str | None = None,
	status: str = "Draft",
) -> dict[str, Any]:
	"""Create a **KenTender Public Disclosure Record** with redacted, field-bound content.

	Only **Tender** and **Procurement Contract** are supported out of the box; extend ``_SAFE_FIELDS`` deliberately.
	"""
	ot = (object_type or "").strip()
	oid = (object_id or "").strip()
	if not frappe.db.exists(ot, oid):
		frappe.throw(_("Document not found."), frappe.DoesNotExistError)

	fields = _SAFE_FIELDS.get(ot)
	if not fields:
		frappe.throw(
			_("Public disclosure is not enabled for DocType {0}. Extend allowlists in code.").format(ot),
			frappe.ValidationError,
		)

	row = frappe.db.get_value(ot, oid, fields, as_dict=True) or {}
	summary = _build_summary_html(ot, row)

	pub = (published_by_user or frappe.session.user or "Administrator").strip()
	if not frappe.db.exists("User", pub):
		frappe.throw(_("Published By user not found."), frappe.ValidationError)

	biz = (business_id or "").strip() or f"DISC-{frappe.generate_hash(length=10)}"
	if frappe.db.exists(PDR, {"business_id": biz}):
		frappe.throw(_("Business ID already exists."), frappe.ValidationError)

	doc = frappe.get_doc(
		{
			"doctype": PDR,
			"business_id": biz,
			"related_doctype": ot,
			"related_docname": oid,
			"disclosure_stage": disclosure_stage,
			"disclosure_datetime": now_datetime(),
			"public_summary": summary,
			"redacted_flag": 1,
			"published_by_user": pub,
			"status": status,
		}
	)
	doc.insert(ignore_permissions=True)

	return {"public_disclosure": doc.name, "business_id": doc.business_id}


def export_disclosure_dataset_rows(dataset_name: str, *, limit: int = 200) -> dict[str, Any]:
	"""Return rows from ``source_doctype`` limited to dataset allowlist (GOV-STORY-037/038 bridge)."""
	if not frappe.db.exists(DS, dataset_name):
		frappe.throw(_("KenTender Disclosure Dataset not found."), frappe.DoesNotExistError)
	ds = frappe.get_doc(DS, dataset_name)
	if ds.status != "Active":
		frappe.throw(_("Dataset is not active."), frappe.ValidationError)

	try:
		fields = json.loads(ds.field_allowlist_json or "[]")
	except json.JSONDecodeError:
		frappe.throw(_("Invalid dataset JSON."), frappe.ValidationError)

	meta = frappe.get_meta(ds.source_doctype)
	allowed: list[str] = []
	for f in fields:
		if not isinstance(f, str):
			continue
		if meta.has_field(f):
			df = meta.get_field(f)
			if df.fieldtype in ("Password", "Attach", "Attach Image"):
				continue
			allowed.append(f)

	if not allowed:
		frappe.throw(_("No valid fields to export."), frappe.ValidationError)

	rows = frappe.get_all(
		ds.source_doctype,
		fields=allowed,
		limit_start=0,
		limit_page_length=limit,
	)
	return {"doctype": ds.source_doctype, "fields": allowed, "rows": rows, "row_count": len(rows)}


@frappe.whitelist()
def generate_public_disclosure_api(
	object_type: str | None = None,
	object_id: str | None = None,
	disclosure_stage: str | None = None,
	business_id: str | None = None,
	published_by_user: str | None = None,
	status: str | None = None,
):
	if not object_type or not object_id or not disclosure_stage:
		frappe.throw(_("object_type, object_id, and disclosure_stage are required."), frappe.ValidationError)
	return generate_public_disclosure(
		object_type,
		object_id,
		disclosure_stage=disclosure_stage,
		business_id=business_id,
		published_by_user=published_by_user,
		status=status or "Draft",
	)


@frappe.whitelist()
def export_disclosure_dataset_rows_api(dataset_name: str | None = None, limit: int = 200):
	if not dataset_name:
		frappe.throw(_("dataset_name is required."), frappe.ValidationError)
	return export_disclosure_dataset_rows(dataset_name, limit=int(limit or 200))
