# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Workflow and controlled-action integration (PERM-005 / PERM-006).

**Implementation** lives in :mod:`kentender.services.controlled_action_service`
(``run_controlled_action_gate``, ``log_controlled_action_completed``) and
:mod:`kentender.services.workflow_guard_service`.

Domain code should call ``run_controlled_action_gate`` before submit/approve/publish
so permission type + workflow guards + audit run in one place. Assignment-only
gates (PERM-006) combine with
:mod:`kentender.services.assignment_access_service` at the call site.

This module re-exports the main entry points for a stable ``kentender.permissions``
import path.
"""

from kentender.services.controlled_action_service import (
	ACTION_APPROVE,
	ACTION_CLOSE,
	ACTION_FINALIZE,
	ACTION_OPEN,
	ACTION_PUBLISH,
	ACTION_SUBMIT,
	ControlledActionResult,
	default_permtype_for_action,
	log_controlled_action_completed,
	run_controlled_action_gate,
	workflow_event_for_action,
)

__all__ = [
	"ACTION_APPROVE",
	"ACTION_CLOSE",
	"ACTION_FINALIZE",
	"ACTION_OPEN",
	"ACTION_PUBLISH",
	"ACTION_SUBMIT",
	"ControlledActionResult",
	"default_permtype_for_action",
	"log_controlled_action_completed",
	"run_controlled_action_gate",
	"workflow_event_for_action",
]
