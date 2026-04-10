# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""STAT-003: central workflow_state → derived summary ``status`` mapping."""

from __future__ import annotations

from typing import Callable

from frappe.model.document import Document

_SUMMARY_MAPPERS: dict[str, Callable[[str], str]] = {}

PR_DOCTYPE = "Purchase Requisition"
PLAN_DOCTYPE = "Procurement Plan"


def register_doctype_summary_mapping(
	doctype: str,
	mapper: Callable[[str], str],
) -> None:
	"""Register a function: normalized workflow_state -> derived summary status string."""
	dt = (doctype or "").strip()
	if not dt:
		return
	_SUMMARY_MAPPERS[dt] = mapper


def derive_summary_status(doctype: str, workflow_state: str | None) -> str:
	"""Return derived summary for *workflow_state*; unknown doctype returns stripped *workflow_state*."""
	dt = (doctype or "").strip()
	ws = (workflow_state or "").strip()
	fn = _SUMMARY_MAPPERS.get(dt)
	if fn:
		return fn(ws)
	return ws


def apply_registered_summary_fields(doc: Document) -> None:
	"""If *doc*'s doctype has a mapper, set ``status`` and mirror ``approval_status`` = workflow_state (legacy)."""
	dt = (doc.doctype or "").strip()
	if dt not in _SUMMARY_MAPPERS:
		return
	ws = (doc.get("workflow_state") or "").strip()
	doc.set("status", derive_summary_status(dt, ws))
	# Deprecated duplicate: keep DB aligned with authoritative stage for legacy SQL/report code.
	doc.set("approval_status", ws)


def derive_purchase_requisition_summary_status(workflow_state: str | None) -> str:
	"""Map PR workflow_state -> compact summary (Standard Status Model §5)."""
	ws = (workflow_state or "").strip()
	if ws == "Draft":
		return "Draft"
	if ws in (
		"Submitted",
		"Under Review",
		"Pending HOD Approval",
		"Pending Finance Approval",
	):
		return "Pending"
	if ws == "Returned for Amendment":
		return "Draft"
	if ws == "Approved":
		return "Approved"
	if ws == "Rejected":
		return "Rejected"
	if ws == "Cancelled":
		return "Cancelled"
	# Unknown future state: do not invent meaning; echo workflow label.
	return ws


def derive_procurement_plan_summary_status(workflow_state: str | None) -> str:
	"""Map Procurement Plan workflow_state (spec v2 §7.2) → compact summary status."""
	ws = (workflow_state or "").strip()
	if ws == "Draft":
		return "Draft"
	if ws == "Submitted":
		return "Pending"
	if ws == "Approved":
		return "Approved"
	if ws == "Active":
		return "Active"
	if ws == "Rejected":
		return "Rejected"
	if ws == "Returned":
		return "Returned"
	return ws


register_doctype_summary_mapping(PR_DOCTYPE, derive_purchase_requisition_summary_status)
register_doctype_summary_mapping(PLAN_DOCTYPE, derive_procurement_plan_summary_status)
