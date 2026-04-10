# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Stable integration hooks for `kentender_governance` complaint flows (hold / actions).

Procurement or other apps may replace behaviour via `frappe.override_whitelisted_method` or hooks later.
Default implementations are no-ops so governance services can call them unconditionally.
"""

from __future__ import annotations

from typing import Any


def emit_complaint_hold_signal(*, complaint: str, action: str, context: dict[str, Any] | None = None) -> None:
	"""Notify downstream systems when a complaint-driven procurement hold is applied or released.

	:param complaint: Complaint name
	:param action: ``apply`` | ``release``
	:param context: Optional flags such as ``affects_award_process``, ``affects_contract_execution``
	"""


def emit_complaint_action_signal(*, complaint: str, decision: str, action: str) -> None:
	"""Notify downstream systems after complaint decision execution milestones.

	:param complaint: Complaint name
	:param decision: Complaint Decision name
	:param action: e.g. ``execute_complete``
	"""
