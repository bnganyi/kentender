# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Generate human-readable business IDs from **Reference Number Policy** rows.

Pattern language (v1)
---------------------
- **Sequence token:** exactly one placeholder consisting of only hash characters inside braces,
  e.g. ``{####}`` (4-digit zero-padded) or ``{#####}``. The number of ``#`` sets the width
  passed to Frappe ``getseries``.
- **Optional literals:** any other characters are copied as-is after substitution.
- **Placeholders:** ``{entity}`` and ``{fy}`` are replaced from the arguments to
  :func:`generate_business_id` when they appear in the pattern. When the policy has
  ``entity_scoped`` / ``fiscal_year_scoped``, the corresponding argument is **required**
  (even if the placeholder does not appear in the pattern), so series keys stay consistent.

``procuring_entity`` should be the **Procuring Entity** document name (typically the entity code).

Series keys are internal ``tabSeries`` names and are **not** the same as the returned business ID.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.model.naming import getseries
from frappe.utils import cint

if TYPE_CHECKING:
	from frappe.model.document import Document

_SEQUENCE_IN_PATTERN = re.compile(r"\{(#+)\}")


def get_reference_number_policy(policy_code: str) -> Document:
	"""Return active Reference Number Policy for ``policy_code``."""
	if not (policy_code or "").strip():
		frappe.throw(_("Policy code is required."), frappe.ValidationError)
	name = frappe.db.get_value(
		"Reference Number Policy",
		{"policy_code": policy_code, "docstatus": ("!=", 2)},
		"name",
	)
	if not name:
		frappe.throw(
			_("Reference Number Policy not found for code {0}.").format(
				frappe.bold(policy_code)
			),
			frappe.DoesNotExistError,
		)
	doc = frappe.get_doc("Reference Number Policy", name)
	if not cint(doc.active):
		frappe.throw(
			_("Reference Number Policy {0} is inactive.").format(frappe.bold(policy_code)),
			frappe.ValidationError,
		)
	return doc


def _normalize_series_token(value: str | None) -> str:
	if not value or not str(value).strip():
		return "NA"
	cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(value).strip())
	return cleaned or "NA"


def _build_series_key(
	policy: Document,
	procuring_entity: str | None,
	fiscal_year: str | None,
) -> str:
	entity_part = _normalize_series_token(
		procuring_entity if cint(policy.entity_scoped) else None
	)
	fy_part = _normalize_series_token(fiscal_year if cint(policy.fiscal_year_scoped) else None)
	if not cint(policy.entity_scoped):
		entity_part = "NA"
	if not cint(policy.fiscal_year_scoped):
		fy_part = "NA"
	return (
		f"KT-RNP-{policy.policy_code}-{policy.target_doctype}-{entity_part}-{fy_part}"
	)


def generate_business_id(
	policy_code: str,
	*,
	procuring_entity: str | None = None,
	fiscal_year: str | None = None,
) -> str:
	"""Return the next business ID for the given policy and scope.

	:param policy_code: ``Reference Number Policy.policy_code``
	:param procuring_entity: Required when policy ``entity_scoped`` is set.
	:param fiscal_year: Required when policy ``fiscal_year_scoped`` is set.
	"""
	policy = get_reference_number_policy(policy_code)

	if cint(policy.entity_scoped) and not (procuring_entity or "").strip():
		frappe.throw(
			_("Procuring entity is required for entity-scoped policy {0}.").format(
				frappe.bold(policy_code)
			),
			frappe.ValidationError,
		)
	if cint(policy.fiscal_year_scoped) and not (fiscal_year or "").strip():
		frappe.throw(
			_("Fiscal year is required for fiscal-year-scoped policy {0}.").format(
				frappe.bold(policy_code)
			),
			frappe.ValidationError,
		)

	series_key = _build_series_key(policy, procuring_entity, fiscal_year)
	text = policy.pattern or ""

	if "{entity}" in text:
		text = text.replace("{entity}", (procuring_entity or "").strip())
	if "{fy}" in text:
		text = text.replace("{fy}", (fiscal_year or "").strip())

	matches = list(_SEQUENCE_IN_PATTERN.finditer(text))
	if len(matches) == 0:
		frappe.throw(
			_("Pattern must contain exactly one sequence token like {{####}}, found none."),
			frappe.ValidationError,
			title=_("Invalid Reference Number Pattern"),
		)
	if len(matches) > 1:
		frappe.throw(
			_("Pattern must contain exactly one sequence token like {{####}}, found {0}.").format(
				len(matches)
			),
			frappe.ValidationError,
			title=_("Invalid Reference Number Pattern"),
		)

	m = matches[0]
	hashes = m.group(1)
	digits = len(hashes)
	start, end = m.span()
	sequence = getseries(series_key, digits)
	return text[:start] + sequence + text[end:]
