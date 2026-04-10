# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.procurement_plan_queue_queries import (
	fragmentation_alert_report_columns,
	fragmentation_alert_report_row_values,
	get_open_fragmentation_alerts,
	procurement_plan_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_open_fragmentation_alerts(procuring_entity=entity or None)
	data = [fragmentation_alert_report_row_values(r) for r in rows]
	return fragmentation_alert_report_columns(), data


def get_filters():
	return procurement_plan_report_entity_filter()
