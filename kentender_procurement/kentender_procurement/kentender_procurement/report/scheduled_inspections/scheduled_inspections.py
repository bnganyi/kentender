# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.inspection_queue_queries import (
	get_scheduled_inspections,
	inspection_report_entity_filter,
	scheduled_inspection_row_values,
	scheduled_inspections_report_columns,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_scheduled_inspections(procuring_entity=entity or None)
	data = [scheduled_inspection_row_values(r) for r in rows]
	return scheduled_inspections_report_columns(), data


def get_filters():
	return inspection_report_entity_filter()
