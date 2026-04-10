# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.deliberation_queue_queries import (
	deliberation_report_entity_filter,
	get_resolution_register_rows,
	resolution_register_report_columns,
	resolution_register_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_resolution_register_rows(procuring_entity=entity or None)
	data = [resolution_register_row_values(r) for r in rows]
	return resolution_register_report_columns(), data


def get_filters():
	return deliberation_report_entity_filter()
