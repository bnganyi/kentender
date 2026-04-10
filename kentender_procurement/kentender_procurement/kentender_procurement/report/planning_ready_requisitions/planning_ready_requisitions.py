# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.requisition_queue_queries import (
	get_planning_ready_requisitions,
	requisition_report_columns,
	requisition_report_entity_filter,
	requisition_report_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_planning_ready_requisitions(procuring_entity=entity or None)
	data = [requisition_report_row_values(r) for r in rows]
	return requisition_report_columns(), data


def get_filters():
	return requisition_report_entity_filter()
