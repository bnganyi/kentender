# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.award_queue_queries import (
	award_entity_filter,
	award_queue_report_columns,
	award_queue_row_values,
	get_standstill_active_awards,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_standstill_active_awards(procuring_entity=entity or None)
	keys = [
		"name",
		"award_decision",
		"tender",
		"start_datetime",
		"end_datetime",
		"complaint_hold_flag",
		"modified",
	]
	data = [award_queue_row_values(r, keys) for r in rows]
	return award_queue_report_columns(keys), data


def get_filters():
	return award_entity_filter()
