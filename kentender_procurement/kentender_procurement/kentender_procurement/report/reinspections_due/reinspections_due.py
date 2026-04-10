# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.inspection_queue_queries import (
	get_reinspections_due_rows,
	inspection_report_entity_filter,
	reinspections_due_report_columns,
	reinspections_due_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_reinspections_due_rows(procuring_entity=entity or None)
	data = [reinspections_due_row_values(r) for r in rows]
	return reinspections_due_report_columns(), data


def get_filters():
	return inspection_report_entity_filter()
