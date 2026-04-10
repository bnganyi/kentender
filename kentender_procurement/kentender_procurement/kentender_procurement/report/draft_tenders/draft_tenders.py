# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_procurement.services.tender_queue_queries import (
	get_draft_tenders,
	tender_queue_report_columns,
	tender_queue_row_values,
	tender_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_draft_tenders(procuring_entity=entity or None)
	data = [tender_queue_row_values(r) for r in rows]
	return tender_queue_report_columns(), data


def get_filters():
	return tender_report_entity_filter()
