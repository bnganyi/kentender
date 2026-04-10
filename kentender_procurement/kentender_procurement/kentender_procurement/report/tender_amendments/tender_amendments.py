# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.tender_queue_queries import (
	get_tender_amendments_for_queue,
	tender_amendment_queue_columns,
	tender_amendment_queue_row_values,
	tender_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_tender_amendments_for_queue(procuring_entity=entity or None)
	data = [tender_amendment_queue_row_values(r) for r in rows]
	return tender_amendment_queue_columns(), data


def get_filters():
	return tender_report_entity_filter()
