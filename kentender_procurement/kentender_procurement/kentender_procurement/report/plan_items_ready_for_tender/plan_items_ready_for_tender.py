# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.procurement_plan_queue_queries import (
	get_plan_items_ready_for_tender,
	plan_item_tender_ready_columns,
	procurement_plan_report_entity_filter,
	plan_item_tender_ready_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_plan_items_ready_for_tender(procuring_entity=entity or None)
	data = [plan_item_tender_ready_row_values(r) for r in rows]
	return plan_item_tender_ready_columns(), data


def get_filters():
	return procurement_plan_report_entity_filter()
