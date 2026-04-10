# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.procurement_plan_queue_queries import (
	get_active_procurement_plans,
	procurement_plan_report_columns,
	procurement_plan_report_entity_filter,
	procurement_plan_report_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_active_procurement_plans(procuring_entity=entity or None)
	data = [procurement_plan_report_row_values(r) for r in rows]
	return procurement_plan_report_columns(), data


def get_filters():
	return procurement_plan_report_entity_filter()
