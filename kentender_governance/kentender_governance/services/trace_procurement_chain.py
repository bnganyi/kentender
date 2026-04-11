# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""GOV-STORY-030: cross-module procurement trace (contract-anchored graph)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

PC = "Procurement Contract"
GRN = "Goods Receipt Note"
AST = "KenTender Asset"
IR = "Inspection Record"
AR = "Acceptance Record"
TENDER = "Tender"
AD = "Award Decision"
ES = "Evaluation Session"
BS = "Bid Submission"
PPI = "Procurement Plan Item"
PR = "Purchase Requisition"
RPL = "Requisition Planning Link"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _exists(dt: str, name: str | None) -> bool:
	return bool(name and frappe.db.exists(dt, name))


def _summarize(doctype: str, name: str | None, fields: list[str]) -> dict[str, Any] | None:
	if not _exists(doctype, name):
		return None
	row = frappe.db.get_value(doctype, name, fields, as_dict=True)
	if not row:
		return None
	out = {"doctype": doctype, "name": name}
	out.update({k: row.get(k) for k in fields if k in row})
	return out


def resolve_procurement_contract(object_type: str, object_id: str) -> str | None:
	"""Return **Procurement Contract** name for known ``object_type`` / ``object_id``, or ``None``."""
	ot = _strip(object_type)
	oid = _strip(object_id)
	if not ot or not oid:
		return None
	if not frappe.db.exists(ot, oid):
		frappe.throw(_("Document not found: {0} {1}").format(ot, oid), frappe.DoesNotExistError)

	if ot == PC:
		return oid
	if ot == GRN:
		return frappe.db.get_value(GRN, oid, "contract")
	if ot == AST:
		src_c = frappe.db.get_value(AST, oid, "source_contract")
		if src_c:
			return src_c
		grn = frappe.db.get_value(AST, oid, "source_grn")
		if grn and _exists(GRN, grn):
			return frappe.db.get_value(GRN, grn, "contract")
		return None
	if ot == IR:
		return frappe.db.get_value(IR, oid, "contract")
	if ot == AR:
		return frappe.db.get_value(AR, oid, "contract")
	if ot == TENDER:
		names = frappe.get_all(PC, filters={"tender": oid}, pluck="name", limit=1)
		return names[0] if names else None
	if ot == AD:
		names = frappe.get_all(PC, filters={"award_decision": oid}, pluck="name", limit=1)
		return names[0] if names else None
	if ot == ES:
		names = frappe.get_all(PC, filters={"evaluation_session": oid}, pluck="name", limit=1)
		return names[0] if names else None
	if ot == BS:
		names = frappe.get_all(PC, filters={"approved_bid_submission": oid}, pluck="name", limit=1)
		return names[0] if names else None
	if ot == PPI:
		names = frappe.get_all(PC, filters={"procurement_plan_item": oid}, pluck="name", limit=1)
		return names[0] if names else None
	if ot == PR:
		links = frappe.get_all(
			RPL,
			filters={"purchase_requisition": oid},
			fields=["procurement_plan_item"],
			limit_page_length=20,
		)
		for row in links:
			pi = row.get("procurement_plan_item")
			if not pi:
				continue
			names = frappe.get_all(PC, filters={"procurement_plan_item": pi}, pluck="name", limit=1)
			if names:
				return names[0]
		return None

	frappe.throw(
		_("Unsupported object_type for trace: {0}. Supported: {1}.").format(
			ot,
			", ".join(
				(
					PC,
					GRN,
					AST,
					IR,
					AR,
					TENDER,
					AD,
					ES,
					BS,
					PPI,
					PR,
				)
			),
		),
		frappe.ValidationError,
	)


def trace_procurement_chain(object_type: str, object_id: str) -> dict[str, Any]:
	"""Build a readable procurement **graph** anchored on **Procurement Contract**.

	:param object_type: DocType name of the entry document.
	:param object_id: Document name.

	Returns ``nodes`` aligned with the Wave 6 pack: requisitions, plan item, tender, bid,
	evaluation, award, contract, inspections, GRNs, KenTender assets (when installed).
	"""
	pc_name = resolve_procurement_contract(object_type, object_id)
	if not pc_name:
		return {
			"ok": False,
			"entry": {"doctype": _strip(object_type), "name": _strip(object_id)},
			"anchor_contract": None,
			"error": _("Could not resolve a Procurement Contract from this document."),
			"nodes": {},
			"notes": [],
		}

	pc = frappe.get_doc(PC, pc_name)
	notes: list[str] = []

	requisitions: list[dict[str, Any]] = []
	if pc.get("procurement_plan_item"):
		for row in (
			frappe.get_all(
				RPL,
				filters={"procurement_plan_item": pc.procurement_plan_item},
				fields=["name", "purchase_requisition", "status"],
			)
			or []
		):
			pr_name = row.get("purchase_requisition")
			if pr_name and _exists(PR, pr_name):
				requisitions.append(
					{
						"doctype": PR,
						"name": pr_name,
						"planning_link": row.get("name"),
						"status": row.get("status"),
					}
				)
		notes.append(_("Requisitions linked via Requisition Planning Link to this plan item."))

	plan_item = _summarize("Procurement Plan Item", pc.get("procurement_plan_item"), ["title", "name", "status"])

	tender = _summarize(TENDER, pc.get("tender"), ["title", "name", "business_id", "status"])

	bid = _summarize(BS, pc.get("approved_bid_submission"), ["name", "business_id", "supplier", "status"])

	evaluation = _summarize(ES, pc.get("evaluation_session"), ["name", "business_id", "status"])

	award = _summarize(AD, pc.get("award_decision"), ["name", "business_id", "status"])

	contract = _summarize(PC, pc_name, ["name", "business_id", "contract_title", "supplier", "status"])

	inspections: list[dict[str, Any]] = []
	if frappe.db.exists("DocType", IR):
		for row in (
			frappe.get_all(
				IR,
				filters={"contract": pc_name},
				fields=["name", "business_id", "inspection_title", "status"],
				order_by="modified desc",
				limit=50,
			)
			or []
		):
			inspections.append(dict(row))

	grns: list[dict[str, Any]] = []
	if frappe.db.exists("DocType", GRN):
		for row in (
			frappe.get_all(
				GRN,
				filters={"contract": pc_name},
				fields=["name", "business_id", "status", "receipt_datetime", "store"],
				order_by="receipt_datetime desc",
				limit=50,
			)
			or []
		):
			grns.append(dict(row))

	assets: list[dict[str, Any]] = []
	if frappe.db.exists("DocType", AST):
		seen: set[str] = set()
		for row in (
			frappe.get_all(
				AST,
				filters={"source_contract": pc_name},
				fields=["name", "asset_code", "asset_name", "status", "source_grn"],
				limit=100,
			)
			or []
		):
			seen.add(row["name"])
			assets.append(dict(row))
		if grns:
			gnames = [g["name"] for g in grns]
			for row in (
				frappe.get_all(
					AST,
					filters={"source_grn": ["in", gnames]},
					fields=["name", "asset_code", "asset_name", "status", "source_grn"],
					limit=100,
				)
				or []
			):
				if row["name"] in seen:
					continue
				seen.add(row["name"])
				assets.append(dict(row))

	notes.append(_("Inspection and GRN lists are limited for performance; expand in reporting if needed."))

	return {
		"ok": True,
		"entry": {"doctype": _strip(object_type), "name": _strip(object_id)},
		"anchor_contract": pc_name,
		"nodes": {
			"requisitions": requisitions,
			"procurement_plan_item": plan_item,
			"tender": tender,
			"bid_submission": bid,
			"evaluation_session": evaluation,
			"award_decision": award,
			"procurement_contract": contract,
			"inspection_records": inspections,
			"goods_receipt_notes": grns,
			"ken_tender_assets": assets,
		},
		"notes": notes,
	}


@frappe.whitelist()
def trace_procurement_chain_api(object_type: str | None = None, object_id: str | None = None):
	"""Whitelisted entry point for ``frappe.call``."""
	if not object_type or not object_id:
		frappe.throw(_("object_type and object_id are required."), frappe.ValidationError)
	return trace_procurement_chain(object_type, object_id)
