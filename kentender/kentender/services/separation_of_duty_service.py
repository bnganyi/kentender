# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Separation-of-duty conflict evaluation (STORY-CORE-011).

Rules are stored as **Separation of Duty Conflict Rule**. Callers supply a proposed
action (user, role, target document, logical action name) plus a **participation
history** for that user — typically built from audit trails, workflow steps, or
domain tables. The service returns zero or more :class:`SodViolation` records when
a rule fires.

**Scope types**

- **Same Document** — prior participation ``docname`` must equal the proposed
  target document name (same primary key string).
- **Same Scope Key** — caller passes ``scope_key`` (e.g. tender id); prior
  participation must carry the same ``scope_key`` on :class:`ParticipationRecord`.
- **Global** — any prior participation matching the source side triggers a conflict
  (use sparingly).

This module does **not** persist participation; it only evaluates rules against
caller-supplied facts. Integrations (submit/approve hooks) are out of scope for this story.

Call only from **server-side** code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import frappe
from frappe import _

RULE_DOCTYPE = "Separation of Duty Conflict Rule"

SCOPE_SAME_DOCUMENT = "Same Document"
SCOPE_SAME_SCOPE_KEY = "Same Scope Key"
SCOPE_GLOBAL = "Global"


@dataclass(frozen=True)
class ParticipationRecord:
	"""A single prior act by a user, as known to the caller."""

	user: str
	doctype: str
	docname: str
	action: str
	role: str | None = None
	scope_key: str | None = None


@dataclass(frozen=True)
class SodViolation:
	"""One fired SoD rule."""

	rule_code: str
	severity: str
	exception_policy: str
	message: str
	source_doctype: str
	source_docname: str
	source_action: str


def _norm(s: str | None) -> str:
	return (s or "").strip()


def _scope_applies(
	scope_type: str,
	participation: ParticipationRecord,
	target_docname: str,
	scope_key: str | None,
) -> bool:
	st = _norm(scope_type) or SCOPE_SAME_DOCUMENT
	if st == SCOPE_SAME_DOCUMENT:
		return _norm(participation.docname) == _norm(target_docname)
	if st == SCOPE_SAME_SCOPE_KEY:
		sk = _norm(scope_key)
		pk = _norm(participation.scope_key)
		return bool(sk) and sk == pk
	if st == SCOPE_GLOBAL:
		return True
	return False


def evaluate_sod_conflicts(
	*,
	target_doctype: str,
	target_docname: str,
	proposed_user: str,
	proposed_action: str,
	proposed_role: str | None = None,
	participation_history: Sequence[ParticipationRecord],
	scope_key: str | None = None,
) -> list[SodViolation]:
	"""Return violations for *proposed_user* performing *proposed_action* on the target.

	Loads **active** rules where ``target_doctype`` and ``target_action`` match.
	``target_role`` on the rule must match *proposed_role* when the rule sets a role;
	if *proposed_role* is empty and the rule requires a target role, the rule is skipped.
	"""
	dt = _norm(target_doctype)
	dn = _norm(target_docname)
	user = _norm(proposed_user)
	action = _norm(proposed_action)
	role = _norm(proposed_role) or None

	if not dt or not dn or not user or not action:
		return []

	rules = frappe.get_all(
		RULE_DOCTYPE,
		filters={"active": 1, "target_doctype": dt, "target_action": action},
		fields=[
			"name",
			"rule_code",
			"source_doctype",
			"source_action",
			"source_role",
			"target_role",
			"scope_type",
			"severity",
			"exception_policy",
		],
	)

	violations: list[SodViolation] = []
	for rule in rules:
		tr = _norm(rule.get("target_role")) or None
		if tr and not role:
			continue
		if tr and role != tr:
			continue

		sdt = _norm(rule.get("source_doctype"))
		sa = _norm(rule.get("source_action"))
		sr = _norm(rule.get("source_role")) or None
		stype = _norm(rule.get("scope_type")) or SCOPE_SAME_DOCUMENT

		matched_p: ParticipationRecord | None = None
		for p in participation_history:
			if _norm(p.user) != user:
				continue
			if _norm(p.doctype) != sdt:
				continue
			if _norm(p.action) != sa:
				continue
			pr = _norm(p.role) or None
			if sr and pr != sr:
				continue

			if not _scope_applies(stype, p, dn, scope_key):
				continue

			matched_p = p
			break

		if matched_p is None:
			continue

		rc = _norm(rule.get("rule_code")) or rule.get("name") or "UNKNOWN"
		msg = _(
			"Separation of duty: rule {0} blocks {1} on {2} {3} after {4} on {5} {6}."
		).format(
			frappe.bold(rc),
			frappe.bold(action),
			frappe.bold(dt),
			frappe.bold(dn),
			frappe.bold(sa),
			frappe.bold(sdt),
			frappe.bold(_norm(matched_p.docname) or "?"),
		)
		violations.append(
			SodViolation(
				rule_code=rc,
				severity=_norm(rule.get("severity")) or "High",
				exception_policy=_norm(rule.get("exception_policy")) or "Block",
				message=msg,
				source_doctype=sdt,
				source_docname=_norm(matched_p.docname),
				source_action=sa,
			)
		)

	return violations


def has_blocking_sod_violation(
	*,
	target_doctype: str,
	target_docname: str,
	proposed_user: str,
	proposed_action: str,
	proposed_role: str | None = None,
	participation_history: Sequence[ParticipationRecord],
	scope_key: str | None = None,
) -> bool:
	"""True if any violation has ``exception_policy`` **Block**."""
	for v in evaluate_sod_conflicts(
		target_doctype=target_doctype,
		target_docname=target_docname,
		proposed_user=proposed_user,
		proposed_action=proposed_action,
		proposed_role=proposed_role,
		participation_history=participation_history,
		scope_key=scope_key,
	):
		if v.exception_policy == "Block":
			return True
	return False


def sod_evaluation_summary(
	violations: Sequence[SodViolation],
) -> dict[str, Any]:
	"""Lightweight aggregate for APIs (counts by severity / policy)."""
	out: dict[str, Any] = {
		"count": len(violations),
		"blocking": sum(1 for v in violations if v.exception_policy == "Block"),
		"warn_only": sum(1 for v in violations if v.exception_policy == "Warn Only"),
		"allow_with_approval": sum(
			1 for v in violations if v.exception_policy == "Allow With Approval"
		),
	}
	return out
