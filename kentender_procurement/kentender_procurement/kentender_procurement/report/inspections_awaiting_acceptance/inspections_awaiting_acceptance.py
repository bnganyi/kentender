# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.inspection_queue_queries import (
	awaiting_acceptance_report_columns,
	awaiting_acceptance_row_values,
	get_inspections_awaiting_acceptance,
	inspection_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_inspections_awaiting_acceptance(procuring_entity=entity or None)
	data = [awaiting_acceptance_row_values(r) for r in rows]
	return awaiting_acceptance_report_columns(), data


def get_filters():
	return inspection_report_entity_filter()
