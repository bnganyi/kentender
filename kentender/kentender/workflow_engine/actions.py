# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-008: workflow actions + global approval action logging."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender.workflow_engine.hooks import run_side_effects

APPROVAL_ACTION_DOCTYPE = "KenTender Approval Action"


def log_global_approval_action(
	*,
	reference_doctype: str,
	reference_docname: str,
	action: str,
	actor_user: str,
	previous_state: dict[str, Any] | None,
	new_state: dict[str, Any] | None,
	comments: str | None = None,
	workflow_stage: str | None = None,
	decision: str | None = None,
	actor_role: str | None = None,
	route_instance: str | None = None,
	route_step: str | None = None,
	is_final_action: bool = False,
) -> str:
	"""Append a **KenTender Approval Action** row (WF-003)."""
	doc = frappe.get_doc(
		{
			"doctype": APPROVAL_ACTION_DOCTYPE,
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname,
			"route_instance": route_instance,
			"route_step": route_step,
			"workflow_stage": workflow_stage,
			"action": action,
			"decision": decision,
			"actor_user": actor_user,
			"actor_role": actor_role,
			"action_datetime": now_datetime(),
			"comments": comments,
			"previous_state": json.dumps(previous_state, sort_keys=True) if previous_state else None,
			"new_state": json.dumps(new_state, sort_keys=True) if new_state else None,
			"is_final_action": 1 if is_final_action else 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def emit_post_transition(
	*,
	doctype: str,
	docname: str,
	action: str,
	actor: str,
	context: dict[str, Any] | None = None,
) -> None:
	"""WF-010: run registered side-effect hooks after a successful transition."""
	run_side_effects(
		doctype=doctype,
		docname=docname,
		action=action,
		actor=actor,
		context=context or {},
	)
