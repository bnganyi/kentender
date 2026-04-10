# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""National reference immutability (STORY-STRAT-003).

Records with ``status == Active`` and ``is_locked_reference`` set are treated as
read-only: any change to *tracked* fields on save raises :class:`frappe.ValidationError`.

**Controlled bypass:** set ``frappe.flags.ignore_national_reference_immutability = True``
only in maintenance jobs, patches, or tests that must correct data integrity.
Do not set this flag from generic desk flows.

Workflow hooks (STORY-CORE-013) may call :func:`enforce_active_locked_immutability` or
duplicate the same rules via :func:`is_active_locked_reference` for pre-event checks.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

IGNORE_NATIONAL_REFERENCE_IMMUTABILITY = "ignore_national_reference_immutability"

REFERENCE_ACTIVE_STATUS = "Active"


def is_active_locked_reference(doc: Document) -> bool:
	return (doc.status or "").strip() == REFERENCE_ACTIVE_STATUS and cint(doc.is_locked_reference)


def enforce_active_locked_immutability(doc: Document, tracked_fieldnames: list[str]) -> None:
	"""Raise if *doc* is an active locked reference and any *tracked_fieldnames* value changed."""
	if doc.is_new():
		return
	if not is_active_locked_reference(doc):
		return
	if frappe.flags.get(IGNORE_NATIONAL_REFERENCE_IMMUTABILITY):
		return
	previous = doc.get_doc_before_save()
	if not previous:
		return
	for fn in tracked_fieldnames:
		cur = doc.get(fn)
		prev = previous.get(fn)
		if (cur != prev) and not _values_equal(cur, prev):
			frappe.throw(
				_(
					"This national reference is active and locked; field {0} cannot be changed."
				).format(frappe.bold(fn)),
				frappe.ValidationError,
				title=_("Locked national reference"),
			)


def national_framework_tracked_fieldnames() -> list[str]:
	return [
		"framework_code",
		"framework_name",
		"framework_type",
		"version_label",
		"status",
		"is_locked_reference",
		"start_date",
		"end_date",
		"source_reference",
		"source_document_url",
		"import_batch_id",
		"imported_at",
		"imported_by",
		"description",
	]


def national_pillar_tracked_fieldnames() -> list[str]:
	return [
		"national_framework",
		"pillar_code",
		"pillar_name",
		"status",
		"is_locked_reference",
		"display_order",
		"description",
	]


def national_objective_tracked_fieldnames() -> list[str]:
	return [
		"national_pillar",
		"national_framework",
		"objective_code",
		"objective_name",
		"status",
		"is_locked_reference",
		"display_order",
		"description",
	]


def _values_equal(a, b) -> bool:
	if a == b:
		return True
	sa = a if a is None else str(a)
	sb = b if b is None else str(b)
	return sa == sb
