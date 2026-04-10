# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Tender clarification and amendment business actions (PROC-STORY-034).

Mutations run inside :func:`kentender.workflow_engine.safeguards.workflow_mutation_context`.
Tender counters ``clarification_count`` / ``amendment_count`` are read-only on Tender; update via
``frappe.db.set_value`` after validation.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime, now_datetime

from kentender.services.audit_event_service import log_audit_event
from kentender.services.controlled_action_service import (
	ACTION_APPROVE,
	ACTION_PUBLISH,
	ACTION_SUBMIT,
	log_controlled_action_completed,
	run_controlled_action_gate,
)
from kentender.workflow_engine.safeguards import workflow_mutation_context

from kentender_procurement.kentender_procurement.doctype.tender_clarification.tender_clarification import (
	STATUS_ANSWERED as CLAR_STATUS_ANSWERED,
)
from kentender_procurement.kentender_procurement.doctype.tender_amendment.tender_amendment import (
	STATUS_PUBLISHED as AMENDMENT_STATUS_PUBLISHED,
)

TENDER_DOCTYPE = "Tender"
CLAR_DOCTYPE = "Tender Clarification"
AMEND_DOCTYPE = "Tender Amendment"

SOURCE_MODULE = "kentender_procurement"

AUDIT_CLAR_SUBMITTED = "kt.procurement.tender_clarification.submitted"
AUDIT_CLAR_RESPONSE_PUBLISHED = "kt.procurement.tender_clarification.response_published"
AUDIT_AMEND_CREATED = "kt.procurement.tender_amendment.created"
AUDIT_AMEND_PUBLISHED = "kt.procurement.tender_amendment.published"

WS_PUBLISHED = "Published"
SUB_OPEN = "Open"
SUB_CANCELLED = "Cancelled"

CLAR_DRAFT = "Draft"
CLAR_PENDING = "Pending Response"

AMD_DRAFT = "Draft"
AMD_APPROVED = "Approved"
AMD_PUBLISHED = "Published"
AMD_SUPERSEDED = "Superseded"
AMD_CANCELLED = "Cancelled"


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _assert_gate_ok(result: Any, action: str) -> None:
	if result.ok:
		return
	frappe.throw(
		_(result.failure_reason or "Action not allowed."),
		frappe.ValidationError,
		title=_("{0} blocked").format(_(action)),
	)


def _audit_json(**payload: Any) -> str:
	return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _now_coerce() -> Any:
	return now_datetime()


def _is_past_deadline(now: Any, deadline: Any) -> bool:
	if not deadline:
		return False
	dt = get_datetime(deadline)
	if not dt:
		return False
	return get_datetime(now) > dt


def _require_tender_clarification_window(tender: Document, *, for_new_question: bool) -> None:
	if _norm(tender.workflow_state) != WS_PUBLISHED:
		frappe.throw(
			_("Clarifications require a **Published** tender (current workflow: {0}).").format(
				_norm(tender.workflow_state) or "—",
			),
			frappe.ValidationError,
			title=_("Invalid tender stage"),
		)
	ss = _norm(tender.submission_status)
	if ss == SUB_CANCELLED:
		frappe.throw(_("Tender submission is cancelled."), frappe.ValidationError, title=_("Invalid stage"))
	if ss != SUB_OPEN:
		frappe.throw(
			_("Clarifications require submission status **Open** (current: {0}).").format(ss or "—"),
			frappe.ValidationError,
			title=_("Market closed"),
		)
	now = _now_coerce()
	if _is_past_deadline(now, tender.submission_deadline):
		frappe.throw(
			_("The submission deadline has passed."),
			frappe.ValidationError,
			title=_("Deadline passed"),
		)
	if for_new_question and _is_past_deadline(now, tender.clarification_deadline):
		frappe.throw(
			_("The clarification deadline for new questions has passed."),
			frappe.ValidationError,
			title=_("Clarification window closed"),
		)


def _require_tender_amendment_actions(tender: Document, *, require_open_for_create: bool) -> None:
	if _norm(tender.workflow_state) != WS_PUBLISHED:
		frappe.throw(
			_("Amendments require a **Published** tender (current workflow: {0}).").format(
				_norm(tender.workflow_state) or "—",
			),
			frappe.ValidationError,
			title=_("Invalid tender stage"),
		)
	ss = _norm(tender.submission_status)
	if ss == SUB_CANCELLED:
		frappe.throw(_("Tender submission is cancelled."), frappe.ValidationError, title=_("Invalid stage"))
	if require_open_for_create and ss != SUB_OPEN:
		frappe.throw(
			_("Creating an amendment requires submission status **Open** (current: {0}).").format(
				ss or "—",
			),
			frappe.ValidationError,
			title=_("Market closed"),
		)


def _bump_clarification_count(tender_name: str) -> None:
	row = frappe.db.get_value(
		TENDER_DOCTYPE,
		tender_name,
		["clarification_count"],
		as_dict=True,
	)
	cur = cint((row or {}).get("clarification_count"))
	frappe.db.set_value(
		TENDER_DOCTYPE,
		tender_name,
		"clarification_count",
		cur + 1,
		update_modified=False,
	)


def _bump_amendment_publish(tender_name: str, amendment_business_id: str) -> None:
	row = frappe.db.get_value(
		TENDER_DOCTYPE,
		tender_name,
		["amendment_count"],
		as_dict=True,
	)
	cur = cint((row or {}).get("amendment_count"))
	frappe.db.set_value(
		TENDER_DOCTYPE,
		tender_name,
		{"amendment_count": cur + 1, "latest_amendment_ref": amendment_business_id},
		update_modified=False,
	)


def _next_amendment_no(tender_name: str) -> int:
	rows = frappe.get_all(
		AMEND_DOCTYPE,
		filters={"tender": tender_name},
		fields=["amendment_no"],
		order_by="amendment_no desc",
		limit=1,
	)
	if not rows:
		return 1
	return cint(rows[0].get("amendment_no")) + 1


def submit_clarification(
	clarification_name: str | None = None,
	*,
	tender: str | None = None,
	business_id: str | None = None,
	supplier: str | None = None,
	question_text: str | None = None,
	user: str | None = None,
) -> Document:
	"""Draft **Tender Clarification** → ``Pending Response``; increments ``Tender.clarification_count``.

	Either pass *clarification_name* of an existing **Draft** row, or pass *tender* + *business_id* +
	*supplier* + *question_text* to insert then submit.
	"""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"

	if not clarification_name:
		tn = _norm(tender)
		bid = _norm(business_id)
		if not tn or not bid or not _norm(supplier) or not _norm(question_text):
			frappe.throw(
				_("Provide **clarification_name** or all of: tender, business_id, supplier, question_text."),
				frappe.ValidationError,
				title=_("Missing fields"),
			)
		tender_doc = frappe.get_doc(TENDER_DOCTYPE, tn)
		_require_tender_clarification_window(tender_doc, for_new_question=True)
		res = run_controlled_action_gate(
			doctype=TENDER_DOCTYPE,
			docname=tn,
			action=ACTION_SUBMIT,
			user=u,
			procuring_entity=_norm(tender_doc.procuring_entity) or None,
		)
		_assert_gate_ok(res, ACTION_SUBMIT)
		with workflow_mutation_context():
			doc = frappe.get_doc(
				{
					"doctype": CLAR_DOCTYPE,
					"business_id": bid,
					"tender": tn,
					"supplier": _norm(supplier),
					"question_submitted_by": u,
					"question_datetime": now_datetime(),
					"question_text": _norm(question_text),
					"status": CLAR_DRAFT,
					"visibility_mode": "Internal",
				}
			)
			doc.insert(ignore_permissions=True)
			old_status = CLAR_DRAFT
			doc.status = CLAR_PENDING
			doc.save(ignore_permissions=True)
			_bump_clarification_count(tn)
		log_audit_event(
			event_type=AUDIT_CLAR_SUBMITTED,
			actor=u,
			source_module=SOURCE_MODULE,
			target_doctype=TENDER_DOCTYPE,
			target_docname=tn,
			procuring_entity=_norm(tender_doc.procuring_entity) or None,
			old_state=_audit_json(child_doctype=CLAR_DOCTYPE, child=doc.name, status=old_status),
			new_state=_audit_json(child_doctype=CLAR_DOCTYPE, child=doc.name, status=doc.status),
		)
		log_controlled_action_completed(
			action=ACTION_SUBMIT,
			doctype=TENDER_DOCTYPE,
			docname=tn,
			actor=u,
			procuring_entity=_norm(tender_doc.procuring_entity) or None,
		)
		doc.reload()
		return doc

	doc = frappe.get_doc(CLAR_DOCTYPE, _norm(clarification_name))
	tn = _norm(doc.tender)
	tender_doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	_require_tender_clarification_window(tender_doc, for_new_question=True)

	st = _norm(doc.status)
	if st != CLAR_DRAFT:
		frappe.throw(
			_("Only **Draft** clarifications can be submitted (current: {0}).").format(st or "—"),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	old_status = st
	with workflow_mutation_context():
		doc.status = CLAR_PENDING
		doc.save(ignore_permissions=True)
		_bump_clarification_count(tn)

	log_audit_event(
		event_type=AUDIT_CLAR_SUBMITTED,
		actor=u,
		source_module=SOURCE_MODULE,
		target_doctype=TENDER_DOCTYPE,
		target_docname=tn,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
		old_state=_audit_json(child_doctype=CLAR_DOCTYPE, child=doc.name, status=old_status),
		new_state=_audit_json(child_doctype=CLAR_DOCTYPE, child=doc.name, status=doc.status),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	doc.reload()
	return doc


def publish_clarification_response(
	clarification_name: str,
	*,
	response_text: str,
	user: str | None = None,
	is_response_official: bool = True,
) -> Document:
	"""``Pending Response`` → ``Answered`` with response metadata (does not increment clarification_count)."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(CLAR_DOCTYPE, _norm(clarification_name))
	tn = _norm(doc.tender)
	tender_doc = frappe.get_doc(TENDER_DOCTYPE, tn)

	_require_tender_clarification_window(tender_doc, for_new_question=False)

	st = _norm(doc.status)
	if st != CLAR_PENDING:
		frappe.throw(
			_("Only clarifications **Pending Response** can be answered (current: {0}).").format(
				st or "—",
			),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_SUBMIT,
		user=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_SUBMIT)

	old_status = st
	with workflow_mutation_context():
		doc.status = CLAR_STATUS_ANSWERED
		doc.response_text = _norm(response_text)
		doc.response_datetime = now_datetime()
		doc.responded_by_user = u
		doc.is_response_official = 1 if is_response_official else 0
		doc.save(ignore_permissions=True)

	log_audit_event(
		event_type=AUDIT_CLAR_RESPONSE_PUBLISHED,
		actor=u,
		source_module=SOURCE_MODULE,
		target_doctype=TENDER_DOCTYPE,
		target_docname=tn,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
		old_state=_audit_json(child_doctype=CLAR_DOCTYPE, child=doc.name, status=old_status),
		new_state=_audit_json(
			child_doctype=CLAR_DOCTYPE,
			child=doc.name,
			status=doc.status,
			official=bool(is_response_official),
		),
	)
	log_controlled_action_completed(
		action=ACTION_SUBMIT,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	doc.reload()
	return doc


def create_tender_amendment(
	tender_name: str,
	*,
	change_summary: str,
	reason: str,
	effective_datetime: str | Any,
	amendment_type: str = "Administrative",
	requires_deadline_extension: bool = False,
	new_submission_deadline: str | None = None,
	new_opening_datetime: str | None = None,
	related_document: str | None = None,
	user: str | None = None,
) -> Document:
	"""Insert a **Draft** Tender Amendment (no tender counter bump)."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	tn = _norm(tender_name)
	tender_doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	_require_tender_amendment_actions(tender_doc, require_open_for_create=True)

	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_APPROVE,
		user=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_APPROVE)

	no = _next_amendment_no(tn)
	tbiz = _norm(tender_doc.business_id) or tn
	business_id = f"{tbiz}-AMD-{no}"

	with workflow_mutation_context():
		doc = frappe.get_doc(
			{
				"doctype": AMEND_DOCTYPE,
				"business_id": business_id,
				"tender": tn,
				"amendment_no": no,
				"amendment_type": _norm(amendment_type) or "Administrative",
				"change_summary": _norm(change_summary),
				"reason": _norm(reason),
				"effective_datetime": effective_datetime,
				"requires_deadline_extension": 1 if requires_deadline_extension else 0,
				"new_submission_deadline": new_submission_deadline,
				"new_opening_datetime": new_opening_datetime,
				"related_document": _norm(related_document) or None,
				"status": AMD_DRAFT,
			}
		)
		doc.insert(ignore_permissions=True)

	log_audit_event(
		event_type=AUDIT_AMEND_CREATED,
		actor=u,
		source_module=SOURCE_MODULE,
		target_doctype=TENDER_DOCTYPE,
		target_docname=tn,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
		old_state=_audit_json(amendment=None),
		new_state=_audit_json(
			child_doctype=AMEND_DOCTYPE,
			child=doc.name,
			business_id=business_id,
			amendment_no=no,
			status=AMD_DRAFT,
		),
	)
	log_controlled_action_completed(
		action=ACTION_APPROVE,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	doc.reload()
	return doc


def publish_tender_amendment(
	amendment_name: str,
	*,
	user: str | None = None,
) -> Document:
	"""``Draft`` or ``Approved`` → ``Published``; bumps ``amendment_count`` and ``latest_amendment_ref``."""
	u = _norm(user) or _norm(frappe.session.user) or "Administrator"
	doc = frappe.get_doc(AMEND_DOCTYPE, _norm(amendment_name))
	tn = _norm(doc.tender)
	tender_doc = frappe.get_doc(TENDER_DOCTYPE, tn)
	_require_tender_amendment_actions(tender_doc, require_open_for_create=False)

	st = _norm(doc.status)
	if st in (AMD_PUBLISHED, AMD_SUPERSEDED, AMD_CANCELLED):
		frappe.throw(
			_("Amendment cannot be published from status **{0}**.").format(st),
			frappe.ValidationError,
			title=_("Invalid status"),
		)
	if st not in (AMD_DRAFT, AMD_APPROVED):
		frappe.throw(
			_("Only **Draft** or **Approved** amendments can be published (current: {0}).").format(
				st or "—",
			),
			frappe.ValidationError,
			title=_("Invalid status"),
		)

	res = run_controlled_action_gate(
		doctype=TENDER_DOCTYPE,
		docname=tn,
		action=ACTION_PUBLISH,
		user=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	_assert_gate_ok(res, ACTION_PUBLISH)

	old_status = st
	with workflow_mutation_context():
		if st == AMD_DRAFT:
			doc.approved_by = u
		doc.status = AMENDMENT_STATUS_PUBLISHED
		doc.published_by = u
		doc.published_at = now_datetime()
		doc.save(ignore_permissions=True)
		_bump_amendment_publish(tn, _norm(doc.business_id))

	log_audit_event(
		event_type=AUDIT_AMEND_PUBLISHED,
		actor=u,
		source_module=SOURCE_MODULE,
		target_doctype=TENDER_DOCTYPE,
		target_docname=tn,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
		old_state=_audit_json(child_doctype=AMEND_DOCTYPE, child=doc.name, status=old_status),
		new_state=_audit_json(
			child_doctype=AMEND_DOCTYPE,
			child=doc.name,
			status=doc.status,
			business_id=_norm(doc.business_id),
		),
	)
	log_controlled_action_completed(
		action=ACTION_PUBLISH,
		doctype=TENDER_DOCTYPE,
		docname=tn,
		actor=u,
		procuring_entity=_norm(tender_doc.procuring_entity) or None,
	)
	doc.reload()
	return doc
