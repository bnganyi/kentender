# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Bid draft creation, document upload, and validation (PROC-STORY-043).

Final sealed submission and receipts are **PROC-STORY-044**; this module stops at draft
validation and aggregate status on :class:`~frappe.model.document.Document` **Bid Submission**.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now_datetime

from kentender_procurement.services.bid_supplier_eligibility import assess_supplier_bid_eligibility
from kentender_procurement.services.tender_workflow_actions import SUB_OPEN, WS_PUBLISHED

BS = "Bid Submission"
BD = "Bid Document"
BES = "Bid Envelope Section"
BVI = "Bid Validation Issue"
TDOC = "Tender Document"

SCOPE_WHOLE = "Whole Tender"
SCOPE_SINGLE = "Single Lot"

ST_PASS = "Pass"
ST_FAIL = "Fail"
ST_PENDING = "Pending"
ST_NOT_RUN = "Not Run"

VS_PASS = "Pass"
VS_FAIL = "Fail"
VS_WARNING = "Warning"
VS_PENDING = "Pending"

SEV_BLOCK = "Blocking"
SEV_WARN = "Warning"
ISSUE_ELIG = "Eligibility"
ISSUE_MAND = "Mandatory Document"
ISSUE_STRUCT = "Structure"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _gen_business_id() -> str:
	for _ in range(8):
		cand = f"BID-{_strip(frappe.generate_hash(length=14))}"
		if not frappe.db.exists(BS, {"business_id": cand}):
			return cand
	frappe.throw(_("Could not allocate a unique Business ID."), frappe.ValidationError)


def _assert_tender_allows_bidding(tender_name: str) -> None:
	tn = _strip(tender_name)
	row = frappe.db.get_value(
		"Tender",
		tn,
		["workflow_state", "submission_status"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Tender {0} does not exist.").format(frappe.bold(tn)), frappe.ValidationError)
	if _strip(row.get("workflow_state")) != WS_PUBLISHED:
		frappe.throw(
			_("Tender must be **Published** to work on bids."),
			frappe.ValidationError,
			title=_("Invalid tender stage"),
		)
	if _strip(row.get("submission_status")) != SUB_OPEN:
		frappe.throw(
			_("Tender submission window is not open."),
			frappe.ValidationError,
			title=_("Submission closed"),
		)


def _active_draft_exists(tender: str, supplier: str) -> str | None:
	name = (
		frappe.db.get_value(
			BS,
			{
				"tender": tender,
				"supplier": supplier,
				"workflow_state": "Draft",
				"status": "Draft",
				"active_submission_flag": 1,
			},
			"name",
		)
		or None
	)
	return name


def create_bid_draft(
	tender_name: str,
	supplier_id: str,
	*,
	business_id: str | None = None,
	prior_bid_submission: str | None = None,
	submission_version_no: int | None = None,
	ignore_permissions: bool = True,
) -> Document:
	"""Create a **Draft** bid for an open, published tender when the supplier is eligible.

	:param prior_bid_submission: When set (resubmission chain), must be a withdrawn bid for the same tender/supplier.
	:param submission_version_no: Optional explicit version (default ``1``, or ``prior.version + 1`` when prior is set).
	"""
	tn = _strip(tender_name)
	sup = _strip(supplier_id)
	assess = assess_supplier_bid_eligibility(tn, sup)
	if not assess.get("eligible"):
		msg = "; ".join(assess.get("reasons") or []) or _("Supplier is not eligible to bid.")
		frappe.throw(msg, frappe.ValidationError, title=_("Not eligible"))

	dup = _active_draft_exists(tn, sup)
	if dup:
		frappe.throw(
			_("An active draft bid already exists for this tender and supplier."),
			frappe.ValidationError,
			title=_("Duplicate bid"),
		)

	_assert_tender_allows_bidding(tn)

	prior = _strip(prior_bid_submission)
	if prior:
		pr = frappe.db.get_value(
			BS,
			prior,
			["tender", "supplier", "workflow_state", "status", "submission_version_no"],
			as_dict=True,
		)
		if not pr:
			frappe.throw(_("Prior bid not found."), frappe.ValidationError)
		if _strip(pr.get("tender")) != tn or _strip(pr.get("supplier")) != sup:
			frappe.throw(_("Prior bid does not match tender/supplier."), frappe.ValidationError)
		if _strip(pr.get("workflow_state")) != "Withdrawn" or _strip(pr.get("status")) != "Withdrawn":
			frappe.throw(_("Prior bid must be withdrawn before resubmission."), frappe.ValidationError)

	t_row = frappe.db.get_value(
		"Tender",
		tn,
		[
			"procuring_entity",
			"procurement_method",
			"submission_deadline",
			"opening_datetime",
			"currency",
		],
		as_dict=True,
	)
	if not t_row:
		frappe.throw(_("Tender not found."), frappe.ValidationError)

	biz = _strip(business_id) if business_id else _gen_business_id()

	if submission_version_no is not None:
		ver = cint(submission_version_no)
	else:
		if prior:
			ver = cint(frappe.db.get_value(BS, prior, "submission_version_no")) + 1
		else:
			ver = 1
	if ver < 1:
		frappe.throw(_("Invalid submission version."), frappe.ValidationError)

	payload = {
		"doctype": BS,
		"business_id": biz,
		"tender": tn,
		"supplier": sup,
		"tender_lot_scope": SCOPE_WHOLE,
		"status": "Draft",
		"workflow_state": "Draft",
		"submission_version_no": ver,
		"active_submission_flag": 1,
		"procuring_entity": t_row.get("procuring_entity"),
		"procurement_method": t_row.get("procurement_method"),
		"submission_deadline": t_row.get("submission_deadline"),
		"opening_datetime": t_row.get("opening_datetime"),
		"currency": t_row.get("currency"),
		"eligibility_check_status": ST_PENDING,
		"mandatory_document_check_status": ST_PENDING,
		"structure_check_status": ST_PENDING,
		"validation_status": VS_PENDING,
		"validation_summary": None,
	}
	if prior:
		payload["prior_bid_submission"] = prior

	doc = frappe.get_doc(payload)
	doc.insert(ignore_permissions=ignore_permissions)
	return doc


def upload_bid_document(
	bid_submission: str,
	bid_envelope_section: str,
	*,
	document_type: str,
	attached_file: str,
	document_title: str,
	sensitivity_class: str = "Internal",
	is_mandatory: int = 0,
	ignore_permissions: bool = True,
) -> Document:
	"""Attach a file to a bid envelope section; refreshes document count on the bid."""
	bs = _strip(bid_submission)
	_assert_bid_allows_edit(bs)

	doc = frappe.get_doc(
		{
			"doctype": BD,
			"bid_submission": bs,
			"bid_envelope_section": _strip(bid_envelope_section),
			"document_type": _strip(document_type),
			"attached_file": _strip(attached_file),
			"document_title": _strip(document_title),
			"status": "Draft",
			"sensitivity_class": sensitivity_class,
			"is_mandatory": cint(is_mandatory),
			"validation_status": ST_PENDING,
		}
	)
	doc.insert(ignore_permissions=ignore_permissions)
	_refresh_bid_document_count(bs)
	return doc


def _assert_bid_allows_edit(bid_name: str) -> None:
	b = frappe.db.get_value(
		BS,
		bid_name,
		["tender", "supplier", "workflow_state", "status", "is_locked", "is_final_submission"],
		as_dict=True,
	)
	if not b:
		frappe.throw(_("Bid Submission not found."), frappe.ValidationError)
	if cint(b.get("is_locked")):
		frappe.throw(_("Bid is locked."), frappe.ValidationError, title=_("Locked"))
	if cint(b.get("is_final_submission")):
		frappe.throw(_("Final submission already recorded."), frappe.ValidationError, title=_("Read only"))
	if _strip(b.get("workflow_state")) != "Draft" or _strip(b.get("status")) != "Draft":
		frappe.throw(_("Only draft bids can be edited here."), frappe.ValidationError, title=_("Invalid state"))

	assess = assess_supplier_bid_eligibility(_strip(b.get("tender")), _strip(b.get("supplier")))
	if not assess.get("eligible"):
		msg = "; ".join(assess.get("reasons") or []) or _("Supplier is not eligible.")
		frappe.throw(msg, frappe.ValidationError, title=_("Not eligible"))


def _refresh_bid_document_count(bid_name: str) -> None:
	n = frappe.db.count(BD, {"bid_submission": bid_name})
	frappe.db.set_value(BS, bid_name, "document_count", n, update_modified=False)


def _clear_unresolved_issues(bid_name: str) -> None:
	for row in frappe.get_all(BVI, filters={"bid_submission": bid_name, "resolved_flag": 0}, pluck="name") or []:
		frappe.delete_doc(BVI, row, force=True, ignore_permissions=True)


def _append_issue(
	bid_name: str,
	*,
	issue_type: str,
	severity: str,
	message: str,
) -> None:
	frappe.get_doc(
		{
			"doctype": BVI,
			"bid_submission": bid_name,
			"issue_type": issue_type,
			"severity": severity,
			"issue_message": message[: 140] if len(message) > 140 else message,
			"detected_on": now_datetime(),
		}
	).insert(ignore_permissions=True)


def _mandatory_response_document_types(bid: Document) -> set[str]:
	scope = _strip(bid.tender_lot_scope) or SCOPE_WHOLE
	lot = _strip(bid.tender_lot)
	out: set[str] = set()
	rows = frappe.get_all(
		TDOC,
		filters={
			"tender": bid.tender,
			"is_mandatory_for_supplier_response": 1,
			"status": ("in", ["Active", "Draft"]),
		},
		fields=["document_type", "lot"],
	)
	for r in rows:
		dl = _strip(r.get("lot"))
		dt = _strip(r.get("document_type"))
		if not dt:
			continue
		if scope == SCOPE_WHOLE:
			if dl:
				continue
		elif scope == SCOPE_SINGLE:
			if dl and dl != lot:
				continue
		out.add(dt)
	return out


def _bid_document_types_uploaded(bid_name: str) -> set[str]:
	return set(
		frappe.get_all(
			BD,
			filters={"bid_submission": bid_name},
			pluck="document_type",
		)
		or []
	)


def _required_sections_missing_documents(bid_name: str) -> list[str]:
	missing: list[str] = []
	sections = frappe.get_all(
		BES,
		filters={"bid_submission": bid_name, "is_required": 1},
		fields=["name", "section_title"],
	) or []
	for sec in sections:
		sn = sec.get("name")
		st = _strip(sec.get("section_title")) or sn
		cnt = frappe.db.count(BD, {"bid_submission": bid_name, "bid_envelope_section": sn})
		if cnt < 1:
			missing.append(st)
	return missing


def run_bid_validation(bid_submission_id: str) -> dict[str, Any]:
	"""Recompute per-dimension checks, sync **Bid Validation Issue** rows (unresolved), and summary fields."""
	bn = _strip(bid_submission_id)
	bid = frappe.get_doc(BS, bn)
	if cint(bid.get("is_locked")):
		frappe.throw(_("Bid is locked."), frappe.ValidationError)
	if cint(bid.is_final_submission):
		frappe.throw(_("Validation is not run after final submission."), frappe.ValidationError)
	if _strip(bid.workflow_state) != "Draft" or _strip(bid.status) != "Draft":
		frappe.throw(_("Only draft bids can be validated."), frappe.ValidationError)

	_clear_unresolved_issues(bn)

	elig = assess_supplier_bid_eligibility(bid.tender, bid.supplier)
	elig_ok = bool(elig.get("eligible"))
	eligibility_check_status = ST_PASS if elig_ok else ST_FAIL
	if not elig_ok:
		msg = "; ".join(elig.get("reasons") or []) or _("Not eligible.")
		_append_issue(bn, issue_type=ISSUE_ELIG, severity=SEV_BLOCK, message=msg)

	mandatory_types = _mandatory_response_document_types(bid)
	uploaded_types = _bid_document_types_uploaded(bn)
	missing_mand = sorted(mandatory_types - uploaded_types)
	mandatory_document_check_status = ST_PASS if not missing_mand else ST_FAIL
	for mt in missing_mand:
		dt_label = frappe.db.get_value("Document Type Registry", mt, "document_type_name") or mt
		_append_issue(
			bn,
			issue_type=ISSUE_MAND,
			severity=SEV_BLOCK,
			message=_("Mandatory response document type not uploaded: {0}").format(dt_label),
		)

	missing_struct = _required_sections_missing_documents(bn)
	structure_check_status = ST_PASS if not missing_struct else ST_FAIL
	for title in missing_struct:
		_append_issue(
			bn,
			issue_type=ISSUE_STRUCT,
			severity=SEV_BLOCK,
			message=_("Required envelope section has no document: {0}").format(title),
		)

	blocking = frappe.db.count(BVI, {"bid_submission": bn, "severity": SEV_BLOCK, "resolved_flag": 0})
	warning = frappe.db.count(BVI, {"bid_submission": bn, "severity": SEV_WARN, "resolved_flag": 0})

	if blocking:
		validation_status = VS_FAIL
	elif warning:
		validation_status = VS_WARNING
	else:
		validation_status = VS_PASS

	parts = [
		f"Eligibility: {eligibility_check_status}",
		f"Mandatory documents: {mandatory_document_check_status}",
		f"Structure: {structure_check_status}",
		f"Overall: {validation_status}",
	]
	validation_summary = " | ".join(parts)

	updates = {
		"eligibility_check_status": eligibility_check_status,
		"mandatory_document_check_status": mandatory_document_check_status,
		"structure_check_status": structure_check_status,
		"validation_status": validation_status,
		"validation_summary": validation_summary[: 240],
	}
	for fn, v in updates.items():
		frappe.db.set_value(BS, bn, fn, v, update_modified=False)

	return {
		"bid_submission": bn,
		"eligibility_check_status": eligibility_check_status,
		"mandatory_document_check_status": mandatory_document_check_status,
		"structure_check_status": structure_check_status,
		"validation_status": validation_status,
		"blocking_issues": int(blocking),
		"warning_issues": int(warning),
	}
