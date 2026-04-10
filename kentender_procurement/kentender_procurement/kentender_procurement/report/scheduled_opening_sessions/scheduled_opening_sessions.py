# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.opening_queue_queries import (
	get_scheduled_opening_sessions,
	opening_report_entity_filter,
	opening_session_report_columns,
	opening_session_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_scheduled_opening_sessions(procuring_entity=entity or None)
	data = [opening_session_row_values(r) for r in rows]
	return opening_session_report_columns(), data


def get_filters():
	return opening_report_entity_filter()
