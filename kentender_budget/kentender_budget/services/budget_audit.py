# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Central audit logging for KenTender budget actions (BUD-015).

Wraps :func:`kentender.services.audit_event_service.log_audit_event` with ``source_module="kentender_budget"``.
"""

from __future__ import annotations

import json
from typing import Any

from kentender.services.audit_event_service import log_audit_event


def log_budget_audit(
	event_type: str,
	*,
	procuring_entity: str | None = None,
	target_doctype: str | None = None,
	target_docname: str | None = None,
	business_id: str | None = None,
	payload: dict[str, Any] | None = None,
) -> None:
	log_audit_event(
		event_type=event_type,
		source_module="kentender_budget",
		procuring_entity=procuring_entity,
		target_doctype=target_doctype,
		target_docname=target_docname,
		business_id=business_id,
		new_state=json.dumps(payload, sort_keys=True, default=str) if payload else None,
	)
