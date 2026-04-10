# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.evaluation_queue_queries import (
	evaluation_queue_report_columns,
	evaluation_queue_row_values,
	evaluation_report_entity_filter,
	get_evaluation_sessions_in_progress,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_evaluation_sessions_in_progress(procuring_entity=entity or None)
	keys = [
		"name",
		"business_id",
		"tender",
		"status",
		"workflow_state",
		"procuring_entity",
		"modified",
	]
	data = [evaluation_queue_row_values(r, keys) for r in rows]
	return evaluation_queue_report_columns(keys), data


def get_filters():
	return evaluation_report_entity_filter()
