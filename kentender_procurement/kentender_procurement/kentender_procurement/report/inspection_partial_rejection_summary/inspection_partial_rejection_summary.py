# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.inspection_queue_queries import (
	get_partial_or_rejected_acceptance_rows,
	inspection_report_entity_filter,
	partial_rejection_report_columns,
	partial_rejection_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_partial_or_rejected_acceptance_rows(procuring_entity=entity or None)
	data = [partial_rejection_row_values(r) for r in rows]
	return partial_rejection_report_columns(), data


def get_filters():
	return inspection_report_entity_filter()
