# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Sensitivity classification primitives (STORY-CORE-019).

Canonical labels match **KenTender Typed Attachment** ``sensitivity_class`` options:

- Public
- Internal
- Confidential
- Restricted
- Sealed Procurement

These helpers express **policy-neutral** facts (e.g. “is this label sealed?”). They do **not**
enforce permissions, route access, or encode module-specific disclosure rules — use
CORE-020 and permission layers for that.
"""

from __future__ import annotations

CANONICAL_SENSITIVITY_CLASSES: tuple[str, ...] = (
	"Public",
	"Internal",
	"Confidential",
	"Restricted",
	"Sealed Procurement",
)

_SENSITIVITY_SET = frozenset(CANONICAL_SENSITIVITY_CLASSES)
_PUBLIC = "Public"
_SEALED_PROCUREMENT = "Sealed Procurement"


def normalize_sensitivity_class(value: str | None) -> str | None:
	"""Return the canonical sensitivity label, or ``None`` if missing/unknown.

	Whitespace is stripped; the label must match a canonical value exactly (same as stored Select values).
	"""
	if value is None:
		return None
	stripped = value.strip()
	if not stripped or stripped not in _SENSITIVITY_SET:
		return None
	return stripped


def is_publicly_disclosable(
	sensitivity_class: str | None,
	*,
	public_disclosure_eligibility: bool = False,
) -> bool:
	"""Whether content may be treated as publicly disclosable under v1 infrastructure rules.

	- **Public** class is always disclosable.
	- Any other **canonical** class is disclosable only when ``public_disclosure_eligibility``
	  is true (operator flag, e.g. on KenTender Typed Attachment).
	- Missing or unknown labels are not disclosable (fail closed).
	"""
	normalized = normalize_sensitivity_class(sensitivity_class)
	if normalized == _PUBLIC:
		return True
	if normalized is None:
		return False
	return bool(public_disclosure_eligibility)


def is_sensitive(sensitivity_class: str | None) -> bool:
	"""True if the class is not **Public**, or if the value is missing/invalid (fail closed)."""
	normalized = normalize_sensitivity_class(sensitivity_class)
	if normalized is None:
		return True
	return normalized != _PUBLIC


def is_sealed(sensitivity_class: str | None) -> bool:
	"""True iff sensitivity is **Sealed Procurement**."""
	return normalize_sensitivity_class(sensitivity_class) == _SEALED_PROCUREMENT
