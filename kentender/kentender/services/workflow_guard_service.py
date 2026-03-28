# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Workflow guard execution (STORY-CORE-013).

Loads **Workflow Guard Rule** rows for a DocType + logical *event*, runs them in
``evaluation_order``, and aggregates **blocking** vs **warning** issues.

**Events:** use the string constants below (or your own names) consistently in
rule rows and callers — e.g. ``pre_submit`` on save, ``before_transition`` on
workflow state changes.

**Evaluators:** this module does not embed domain rules. Pass ``evaluator`` — a
callable ``(rule_dict, document, context) -> :class:`GuardEvalOutcome``` — so
CORE-014 / feature code can implement checks per ``rule_code`` or ``rule_type``.
If ``evaluator`` is ``None``, every rule is treated as **passed** (metadata-only
or dry-run listing via :func:`get_active_workflow_guard_rules`).

**Policies:** when an evaluator returns ``passed=False``, ``exception_policy`` on
the rule decides whether the issue is **blocking** (``Block``) or a **warning**
(``Warn Only``, ``Allow With Approval``).

Call only from **server-side** code.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import frappe
from frappe.model.document import Document

WORKFLOW_GUARD_RULE_DOCTYPE = "Workflow Guard Rule"

EVENT_PRE_CREATE = "pre_create"
EVENT_PRE_SUBMIT = "pre_submit"
EVENT_PRE_APPROVE = "pre_approve"
EVENT_PRE_TRANSITION = "pre_transition"

_POLICY_BLOCK = "Block"
_POLICY_WARN = "Warn Only"
_POLICY_ALLOW_APPROVAL = "Allow With Approval"


@dataclass
class GuardEvalOutcome:
	"""Result of evaluating a single rule."""

	passed: bool = True
	message: str = ""


@dataclass
class WorkflowGuardIssue:
	"""A failed rule, classified by severity channel."""

	rule_code: str
	rule_name: str
	severity: str
	rule_type: str
	exception_policy: str
	evaluation_order: int
	blocking: bool
	message: str


@dataclass
class WorkflowGuardResult:
	"""Aggregate outcome for one guard run."""

	passed: bool
	blocking_issues: list[WorkflowGuardIssue] = field(default_factory=list)
	warning_issues: list[WorkflowGuardIssue] = field(default_factory=list)
	evaluated_rule_codes: list[str] = field(default_factory=list)


RuleEvaluator = Callable[[dict[str, Any], Document | None, dict[str, Any] | None], GuardEvalOutcome]


def get_active_workflow_guard_rules(
	applies_to_doctype: str,
	event_name: str,
	*,
	active_only: bool = True,
) -> list[dict[str, Any]]:
	"""Return active **Workflow Guard Rule** rows for *applies_to_doctype* and *event_name*.

	Ordered by ``evaluation_order`` ascending, then ``rule_code``.
	"""
	dt = (applies_to_doctype or "").strip()
	ev = (event_name or "").strip()
	if not dt or not ev:
		return []

	filters: dict[str, Any] = {"applies_to_doctype": dt, "event_name": ev}
	if active_only:
		filters["active"] = 1

	return frappe.get_all(
		WORKFLOW_GUARD_RULE_DOCTYPE,
		filters=filters,
		fields=[
			"name",
			"rule_code",
			"rule_name",
			"applies_to_doctype",
			"event_name",
			"rule_type",
			"severity",
			"evaluation_order",
			"exception_policy",
			"active",
		],
		order_by="evaluation_order asc, rule_code asc",
	)


def _resolve_document(
	applies_to_doctype: str,
	target_docname: str | None,
	document: Document | None,
	*,
	load_document: bool,
) -> Document | None:
	if document is not None:
		return document
	if not load_document:
		return None
	dn = (target_docname or "").strip()
	if not dn:
		return None
	if not frappe.db.exists(applies_to_doctype, dn):
		return None
	return frappe.get_doc(applies_to_doctype, dn)


def evaluate_workflow_guards(
	*,
	applies_to_doctype: str,
	event_name: str,
	target_docname: str | None = None,
	context: dict[str, Any] | None = None,
	document: Document | None = None,
	load_document: bool = False,
	evaluator: RuleEvaluator | None = None,
) -> WorkflowGuardResult:
	"""Run all applicable guards and return structured issues.

	:param target_docname: Target document name (optional if *document* or no load).
	:param context: Arbitrary dict (actor, transition, workflow state, etc.).
	:param load_document: If true and *document* is None, load from DB.
	:param evaluator: If None, all rules pass.
	"""
	dt = (applies_to_doctype or "").strip()
	ev = (event_name or "").strip()
	ctx: dict[str, Any] = dict(context) if context else {}

	blocking: list[WorkflowGuardIssue] = []
	warnings: list[WorkflowGuardIssue] = []
	codes: list[str] = []

	if not dt or not ev:
		return WorkflowGuardResult(passed=True, evaluated_rule_codes=codes)

	doc = _resolve_document(dt, target_docname, document, load_document=load_document)
	rules = get_active_workflow_guard_rules(dt, ev, active_only=True)

	for rule in rules:
		rc = (rule.get("rule_code") or "").strip() or rule.get("name") or ""
		codes.append(rc)

		if evaluator is None:
			continue

		outcome = evaluator(rule, doc, ctx)
		if outcome.passed:
			continue

		policy = (rule.get("exception_policy") or _POLICY_BLOCK).strip()
		is_blocking = policy == _POLICY_BLOCK
		issue = WorkflowGuardIssue(
			rule_code=rc,
			rule_name=(rule.get("rule_name") or "").strip(),
			severity=(rule.get("severity") or "Medium").strip(),
			rule_type=(rule.get("rule_type") or "Validate").strip(),
			exception_policy=policy,
			evaluation_order=int(rule.get("evaluation_order") or 0),
			blocking=is_blocking,
			message=(outcome.message or "").strip() or "Guard check failed.",
		)
		if is_blocking:
			blocking.append(issue)
		else:
			warnings.append(issue)

	return WorkflowGuardResult(
		passed=len(blocking) == 0,
		blocking_issues=blocking,
		warning_issues=warnings,
		evaluated_rule_codes=codes,
	)


def workflow_guard_result_summary(result: WorkflowGuardResult) -> dict[str, Any]:
	"""Compact dict for APIs and logging."""
	return {
		"passed": result.passed,
		"blocking_count": len(result.blocking_issues),
		"warning_count": len(result.warning_issues),
		"rules_evaluated": len(result.evaluated_rule_codes),
	}
