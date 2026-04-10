# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-002: block unauthorized changes to approval-controlled fields."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import FrozenSet

import frappe
from frappe import _
from frappe.model.document import Document

_APPROVAL_FIELDS: dict[str, FrozenSet[str]] = {}
_mutation_allowed: ContextVar[bool] = ContextVar("kt_workflow_field_mutation", default=False)


def register_approval_controlled_fields(doctype: str, fields: tuple[str, ...] | list[str]) -> None:
	"""Declare fields that may only change inside :func:`workflow_mutation_context`."""
	dt = (doctype or "").strip()
	if not dt:
		return
	_APPROVAL_FIELDS[dt] = frozenset(f for f in fields if (f or "").strip())


def is_workflow_mutation_allowed() -> bool:
	return _mutation_allowed.get()


@contextmanager
def workflow_mutation_context():
	"""Allow registered approval-controlled fields to change for the enclosed block."""
	token: Token = _mutation_allowed.set(True)
	try:
		yield
	finally:
		_mutation_allowed.reset(token)


def document_validate_approval_controlled_fields(doc: Document, method: str | None = None) -> None:
	"""``doc_events`` hook: ``validate`` target for registered DocTypes."""
	if is_workflow_mutation_allowed():
		return
	# Amendment apply service uses this flag for approved-PR controlled mutations (PROC-STORY-008).
	if frappe.flags.get("allow_approved_requisition_mutation"):
		return
	# Scripted migrations / data fixes (use inside workflow_mutation_context when mutating stage).
	if frappe.flags.get("ignore_workflow_field_protection"):
		return
	dt = doc.doctype
	protected = _APPROVAL_FIELDS.get(dt)
	if not protected:
		return
	if doc.is_new():
		return
	before = doc.get_doc_before_save()
	if before is None:
		return
	for field in protected:
		if doc.get(field) != before.get(field):
			frappe.throw(
				_(
					"Field {0} is approval-controlled and cannot be changed outside workflow services."
				).format(frappe.bold(field)),
				frappe.ValidationError,
				title=_("Approval-controlled field"),
			)
