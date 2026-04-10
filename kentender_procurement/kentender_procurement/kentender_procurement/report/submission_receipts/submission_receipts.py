# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.bid_queue_queries import (
	bid_receipt_report_columns,
	bid_receipt_row_values,
	bid_report_entity_filter,
	get_submission_receipts,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_submission_receipts(procuring_entity=entity or None)
	data = [bid_receipt_row_values(r) for r in rows]
	return bid_receipt_report_columns(), data


def get_filters():
	return bid_report_entity_filter()
