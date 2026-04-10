# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.inspection_queue_queries import (
	get_non_conformance_register_rows,
	inspection_report_entity_filter,
	non_conformance_register_report_columns,
	non_conformance_register_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_non_conformance_register_rows(procuring_entity=entity or None)
	data = [non_conformance_register_row_values(r) for r in rows]
	return non_conformance_register_report_columns(), data


def get_filters():
	return inspection_report_entity_filter()
