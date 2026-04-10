# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""WF-008: route step resolution, actor checks, and route progression + logging."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender.workflow_engine.actions import emit_post_transition, log_global_approval_action
from kentender.workflow_engine.routes import get_active_route_instance


def get_active_route_for_doc(doctype: str, docname: str) -> str | None:
	"""Return the name of the Active **KenTender Approval Route Instance** for the target, if any."""
	return get_active_route_instance(doctype, docname)


def _ordered_route_steps(instance: Document) -> list[Document]:
	return sorted(instance.route_steps or [], key=lambda r: int(r.step_order or 0))


def get_current_step_row(instance: Document) -> Document | None:
	target = int(instance.current_step_no or 0)
	for row in _ordered_route_steps(instance):
		if int(row.step_order or 0) == target:
			return row
	return None


def assert_actor_allowed_on_step(user: str, instance: Document, step_row: Document) -> None:
	"""Layer D: *user* must hold ``assigned_role`` on the current step (System Manager bypass)."""
	u = (user or "").strip()
	role = (step_row.assigned_role or "").strip()
	if not role:
		frappe.throw(
			_("Approval route step {0} has no assigned role.").format(step_row.step_name or step_row.step_order),
			frappe.ValidationError,
		)
	roles = set(frappe.get_roles(u))
	if "System Manager" in roles:
		return
	if role not in roles:
		frappe.throw(_("You are not allowed to act on this approval step."), frappe.ValidationError)


def _primary_role_for_user(user: str) -> str | None:
	roles = frappe.get_roles(user)
	skip = frozenset({"Guest", "All"})
	if "System Manager" in roles:
		return "System Manager"
	for r in roles:
		if r not in skip:
			return r
	return None


def apply_step_decision(
	instance_name: str,
	decision: str,
	*,
	user: str,
	comments: str | None = None,
	reference_doctype: str | None = None,
	reference_docname: str | None = None,
	previous_state: dict[str, Any] | None = None,
	new_state: dict[str, Any] | None = None,
	log_action: str = "approve",
	hook_action: str | None = None,
) -> Document:
	"""Apply *decision* on the current route step, persist route state, log **KenTender Approval Action**, run hooks.

	Call after the business document has been saved so *new_state* matches the database.
	"""
	inst = frappe.get_doc("KenTender Approval Route Instance", instance_name)
	if (inst.status or "").strip() != "Active":
		frappe.throw(_("This approval route is not active."), frappe.ValidationError)

	ref_dt = reference_doctype or inst.reference_doctype
	ref_dn = reference_docname or inst.reference_docname

	step_row = get_current_step_row(inst)
	if not step_row:
		frappe.throw(_("No current approval step found."), frappe.ValidationError)
	if (step_row.status or "").strip() not in ("Active", "Pending"):
		frappe.throw(_("Current approval step is not actionable."), frappe.ValidationError)

	assert_actor_allowed_on_step(user, inst, step_row)

	decision = (decision or "").strip()
	if decision not in ("Approve", "Reject", "Return"):
		frappe.throw(_("Invalid workflow decision."), frappe.ValidationError)

	step_row.status = "Completed"
	step_row.decision = decision
	step_row.acted_on = now_datetime()
	step_row.comments = (comments or "").strip() or None

	steps = _ordered_route_steps(inst)
	max_order = max(int(s.step_order or 0) for s in steps) if steps else 0
	cur_order = int(inst.current_step_no or 0)

	if decision == "Approve":
		if cur_order >= max_order:
			inst.status = "Completed"
		else:
			next_order = cur_order + 1
			inst.current_step_no = next_order
			for s in steps:
				so = int(s.step_order or 0)
				if so == next_order:
					s.status = "Active"
				elif so > next_order:
					s.status = "Pending"
	else:
		inst.status = "Cancelled"

	inst.save(ignore_permissions=True)

	is_final = decision != "Approve" or (inst.status or "").strip() == "Completed"
	ha = hook_action or log_action.lower().replace(" ", "_")

	log_global_approval_action(
		reference_doctype=ref_dt,
		reference_docname=ref_dn,
		action=log_action,
		actor_user=user,
		actor_role=_primary_role_for_user(user),
		previous_state=previous_state,
		new_state=new_state,
		comments=comments,
		workflow_stage=(step_row.step_name or "").strip() or None,
		decision=decision,
		route_instance=inst.name,
		route_step=step_row.name,
		is_final_action=is_final,
	)

	emit_post_transition(
		doctype=ref_dt,
		docname=ref_dn,
		action=ha,
		actor=user,
		context={"route_instance": inst.name, "decision": decision},
	)

	return inst
