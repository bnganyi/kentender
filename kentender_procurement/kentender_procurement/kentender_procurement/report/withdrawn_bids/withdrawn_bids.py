# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.bid_queue_queries import (
	bid_queue_report_columns,
	bid_queue_row_values,
	bid_report_entity_filter,
	get_withdrawn_bids,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_withdrawn_bids(procuring_entity=entity or None)
	data = [bid_queue_row_values(r) for r in rows]
	return bid_queue_report_columns(), data


def get_filters():
	return bid_report_entity_filter()
