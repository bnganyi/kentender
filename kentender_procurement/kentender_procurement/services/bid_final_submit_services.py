# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Final bid submission and receipt generation (PROC-STORY-044).

Submission must go through :func:`submit_bid` — not via direct **Bid Submission** edits.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from kentender.services.audit_event_service import log_audit_event

from kentender_procurement.services.bid_draft_validate_services import run_bid_validation
from kentender_procurement.services.bid_supplier_eligibility import assess_supplier_bid_eligibility
from kentender_procurement.services.tender_workflow_actions import SUB_OPEN, WS_PUBLISHED

BS = "Bid Submission"
BR = "Bid Receipt"
BSE = "Bid Submission Event"

VS_FAIL = "Fail"
SEALED_SEALED = "Sealed"

AUDIT_BID_SUBMITTED = "kt.procurement.bid.submitted"
SOURCE_MODULE = "kentender_procurement"


def _strip(s: str | None) -> str:
	return (s or "").strip()


def _norm_dt(value) -> str:
	if value is None:
		return ""
	d = get_datetime(value)
	return d.isoformat() if d else str(value)


def compute_submission_content_hash(bid_name: str) -> str:
	"""Deterministic SHA-256 over bid identity and attached bid document fingerprints."""
	rows = (
		frappe.get_all(
			"Bid Document",
			filters={"bid_submission": bid_name},
			fields=["name", "hash_value", "document_type", "bid_envelope_section"],
			order_by="name asc",
		)
		or []
	)
	bid = frappe.db.get_value(
		BS,
		bid_name,
		["business_id", "submission_version_no", "tender", "supplier"],
		as_dict=True,
	)
	if not bid:
		frappe.throw(_("Bid Submission not found."), frappe.ValidationError)
	payload = {
		"bid": bid_name,
		"business_id": _strip(bid.get("business_id")),
		"submission_version_no": cint(bid.get("submission_version_no")),
		"supplier": _strip(bid.get("supplier")),
		"tender": _strip(bid.get("tender")),
		"documents": [
			{
				"bid_envelope_section": _strip(r.get("bid_envelope_section")),
				"document_type": _strip(r.get("document_type")),
				"hash_value": _strip(r.get("hash_value")),
				"name": _strip(r.get("name")),
			}
			for r in rows
		],
	}
	canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _new_submission_token() -> str:
	return frappe.generate_hash(length=32)


def _new_receipt_business_id() -> str:
	for _ in range(8):
		cand = f"REC-{_strip(frappe.generate_hash(length=14))}"
		if not frappe.db.exists(BR, {"business_id": cand}):
			return cand
	frappe.throw(_("Could not allocate a unique receipt Business ID."), frappe.ValidationError)


def _new_receipt_no() -> str:
	# Human-facing number; uniqueness enforced by DocType.
	return f"R-{now_datetime().strftime('%Y%m%d%H%M%S')}-{_strip(frappe.generate_hash(length=6))}"


def _receipt_integrity_hash(
	*,
	bid_name: str,
	tender: str,
	supplier: str,
	submission_hash: str,
	submission_timestamp,
	issued_to: str,
	receipt_no: str,
) -> str:
	payload = {
		"bid_submission": bid_name,
		"issued_to_user": issued_to,
		"receipt_no": receipt_no,
		"submission_hash": submission_hash,
		"submission_timestamp": _norm_dt(submission_timestamp),
		"supplier": supplier,
		"tender": tender,
	}
	canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _event_integrity_hash(
	*,
	bid_name: str,
	event_type: str,
	summary: str,
	actor: str,
	event_datetime,
) -> str:
	payload = {
		"actor_user": actor,
		"bid_submission": bid_name,
		"event_datetime": _norm_dt(event_datetime),
		"event_summary": summary,
		"event_type": event_type,
	}
	canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
	return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _assert_deadline(bid) -> None:
	raw = bid.submission_deadline
	if not raw:
		frappe.throw(
			_("Submission deadline is not set on the bid."),
			frappe.ValidationError,
			title=_("Missing deadline"),
		)
	deadline = get_datetime(raw)
	if not deadline:
		frappe.throw(_("Invalid submission deadline."), frappe.ValidationError)
	now = now_datetime()
	if now > deadline:
		frappe.throw(
			_("The submission deadline has passed."),
			frappe.ValidationError,
			title=_("Deadline passed"),
		)


def _assert_tender_window_open(tender_name: str) -> None:
	row = frappe.db.get_value(
		"Tender",
		tender_name,
		["workflow_state", "submission_status"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Tender not found."), frappe.ValidationError)
	if _strip(row.get("workflow_state")) != WS_PUBLISHED:
		frappe.throw(_("Tender is not published."), frappe.ValidationError, title=_("Invalid tender"))
	if _strip(row.get("submission_status")) != SUB_OPEN:
		frappe.throw(_("Submission window is not open."), frappe.ValidationError, title=_("Closed"))


def _insert_submitted_event(bid_name: str, summary: str, *, user: str) -> None:
	ts = now_datetime()
	eh = _event_integrity_hash(
		bid_name=bid_name,
		event_type="Submitted",
		summary=summary,
		actor=user,
		event_datetime=ts,
	)
	frappe.get_doc(
		{
			"doctype": BSE,
			"bid_submission": bid_name,
			"event_type": "Submitted",
			"event_datetime": ts,
			"event_summary": summary,
			"actor_user": user,
			"event_hash": eh,
		}
	).insert(ignore_permissions=True)


def _insert_bid_receipt_doc(
	bid,
	*,
	submission_hash: str,
	submission_timestamp,
	user: str,
):
	biz = _new_receipt_business_id()
	rno = _new_receipt_no()
	rh = _receipt_integrity_hash(
		bid_name=bid.name,
		tender=_strip(bid.tender),
		supplier=_strip(bid.supplier),
		submission_hash=submission_hash,
		submission_timestamp=submission_timestamp,
		issued_to=user,
		receipt_no=rno,
	)
	doc = frappe.get_doc(
		{
			"doctype": BR,
			"business_id": biz,
			"receipt_no": rno,
			"status": "Issued",
			"bid_submission": bid.name,
			"tender": bid.tender,
			"supplier": bid.supplier,
			"issued_to_user": user,
			"submission_timestamp": submission_timestamp,
			"submission_hash": submission_hash,
			"issued_on": submission_timestamp,
			"receipt_hash": rh,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def generate_bid_receipt(
	bid_submission_id: str,
	*,
	user: str | None = None,
):
	"""Return the existing receipt or create one for a **finalized** bid (repair path).

	Normal flow uses :func:`submit_bid`, which creates the receipt in the same transaction.
	"""
	bn = _strip(bid_submission_id)
	u = _strip(user) or _strip(getattr(frappe.session, "user", None)) or "Administrator"
	bid = frappe.get_doc(BS, bn)
	if not cint(bid.is_final_submission):
		frappe.throw(
			_("Finalize the bid with **Submit Bid** before generating a receipt."),
			frappe.ValidationError,
			title=_("Not submitted"),
		)
	sh = _strip(bid.submission_hash)
	if not sh:
		frappe.throw(_("Submission hash is missing."), frappe.ValidationError, title=_("Incomplete"))
	if _strip(bid.latest_receipt):
		return frappe.get_doc(BR, bid.latest_receipt)
	ts = bid.submitted_on or now_datetime()
	return _insert_bid_receipt_doc(bid, submission_hash=sh, submission_timestamp=ts, user=u)


def submit_bid(bid_submission_id: str, *, user: str | None = None) -> dict[str, Any]:
	"""Validate, hash, seal, receipt, lock — final supplier submission (pre-opening)."""
	bn = _strip(bid_submission_id)
	u = _strip(user) or _strip(getattr(frappe.session, "user", None)) or "Administrator"

	bid = frappe.get_doc(BS, bn)
	if cint(bid.is_final_submission):
		frappe.throw(_("This bid is already submitted."), frappe.ValidationError, title=_("Already submitted"))
	if cint(bid.get("is_locked")):
		frappe.throw(_("This bid is locked."), frappe.ValidationError, title=_("Locked"))
	if _strip(bid.workflow_state) != "Draft" or _strip(bid.status) != "Draft":
		frappe.throw(_("Only draft bids can be submitted."), frappe.ValidationError, title=_("Invalid state"))

	_assert_tender_window_open(_strip(bid.tender))
	elig = assess_supplier_bid_eligibility(bid.tender, bid.supplier)
	if not elig.get("eligible"):
		msg = "; ".join(elig.get("reasons") or []) or _("Not eligible to submit.")
		frappe.throw(msg, frappe.ValidationError, title=_("Not eligible"))

	_assert_deadline(bid)

	val = run_bid_validation(bn)
	if val.get("validation_status") == VS_FAIL or val.get("blocking_issues", 0) > 0:
		frappe.throw(
			_("Bid validation failed; fix blocking issues before submitting."),
			frappe.ValidationError,
			title=_("Validation failed"),
		)
	if val.get("eligibility_check_status") != "Pass" or val.get("mandatory_document_check_status") != "Pass":
		frappe.throw(_("Eligibility or mandatory document checks must pass."), frappe.ValidationError)
	if val.get("structure_check_status") != "Pass":
		frappe.throw(_("Structure validation must pass before submitting."), frappe.ValidationError)

	submission_hash = compute_submission_content_hash(bn)
	token = _new_submission_token()
	ts = now_datetime()

	receipt = _insert_bid_receipt_doc(bid, submission_hash=submission_hash, submission_timestamp=ts, user=u)

	# Use :meth:`Document.set` for ``is_locked`` / ``is_final_submission`` — base
	# :class:`frappe.model.document.Document` exposes ``is_locked`` as a read-only property.
	frappe.flags.in_bid_submit_service = True
	try:
		b2 = frappe.get_doc(BS, bn)
		b2.set("is_final_submission", 1)
		b2.set("is_locked", 1)
		b2.set("status", "Submitted")
		b2.set("workflow_state", "Submitted")
		b2.set("submitted_by_user", u)
		b2.set("submitted_on", ts)
		b2.set("submission_hash", submission_hash)
		b2.set("submission_token", token)
		b2.set("sealed_status", SEALED_SEALED)
		b2.set("latest_receipt", receipt.name)
		b2.set("receipt_no", receipt.receipt_no)
		b2.save(ignore_permissions=True)
	finally:
		frappe.flags.in_bid_submit_service = False

	pe = _strip(frappe.db.get_value("Tender", bid.tender, "procuring_entity"))
	log_audit_event(
		event_type=AUDIT_BID_SUBMITTED,
		actor=u,
		source_module=SOURCE_MODULE,
		target_doctype=BS,
		target_docname=bn,
		procuring_entity=pe or None,
		old_state="Draft",
		new_state="Submitted",
		changed_fields_summary=f"receipt={receipt.name}; hash={submission_hash[:16]}…",
		reason=_("Final bid submission"),
		event_datetime=ts,
	)

	summary = _("Bid submitted; receipt {0}").format(receipt.receipt_no)
	_insert_submitted_event(bn, summary, user=u)

	return {
		"bid_submission": bn,
		"submission_hash": submission_hash,
		"submission_token": token,
		"bid_receipt": receipt.name,
		"receipt_no": receipt.receipt_no,
		"submitted_on": ts,
	}

