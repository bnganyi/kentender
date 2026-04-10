# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.award_queue_queries import (
	award_entity_filter,
	award_queue_report_columns,
	award_queue_row_values,
	get_award_deviation_register,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_award_deviation_register(procuring_entity=entity or None)
	keys = [
		"name",
		"award_decision",
		"deviation_type",
		"status",
		"recommended_supplier",
		"approved_supplier",
		"modified",
	]
	data = [award_queue_row_values(r, keys) for r in rows]
	return award_queue_report_columns(keys), data


def get_filters():
	return award_entity_filter()
