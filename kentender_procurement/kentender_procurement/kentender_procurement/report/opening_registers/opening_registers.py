# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.opening_queue_queries import (
	get_opening_registers,
	opening_register_report_columns,
	opening_register_row_values,
	opening_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_opening_registers(procuring_entity=entity or None)
	data = [opening_register_row_values(r) for r in rows]
	return opening_register_report_columns(), data


def get_filters():
	return opening_report_entity_filter()
