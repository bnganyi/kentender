# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.contract_queue_queries import (
	contract_entity_filter,
	contract_queue_report_columns,
	contract_queue_row_values,
	get_variations_awaiting_action,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_variations_awaiting_action(procuring_entity=entity or None)
	keys = [
		"name",
		"business_id",
		"procurement_contract",
		"variation_no",
		"status",
		"variation_type",
		"modified",
	]
	data = [contract_queue_row_values(r, keys) for r in rows]
	return contract_queue_report_columns(keys), data


def get_filters():
	return contract_entity_filter()
