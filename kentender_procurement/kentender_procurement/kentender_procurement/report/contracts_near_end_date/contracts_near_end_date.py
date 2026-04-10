# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.contract_queue_queries import (
	contracts_near_end_date_filter,
	contract_queue_report_columns,
	contract_queue_row_values,
	get_contracts_near_end_date,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	days = int(filters.get("days_ahead") or 90)
	rows = get_contracts_near_end_date(procuring_entity=entity or None, days_ahead=days)
	keys = [
		"name",
		"business_id",
		"contract_title",
		"tender",
		"contract_end_date",
		"status",
		"modified",
	]
	data = [contract_queue_row_values(r, keys) for r in rows]
	return contract_queue_report_columns(keys), data


def get_filters():
	return contracts_near_end_date_filter()
