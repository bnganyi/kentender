# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from frappe.utils import cint

from kentender_procurement.services.tender_queue_queries import (
	get_tenders_closing_soon,
	tender_closing_soon_extra_filters,
	tender_queue_report_columns,
	tender_queue_row_values,
	tender_report_entity_filter,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	days = cint(filters.get("days_ahead")) or 14
	rows = get_tenders_closing_soon(procuring_entity=entity or None, days_ahead=max(1, days))
	data = [tender_queue_row_values(r) for r in rows]
	return tender_queue_report_columns(), data


def get_filters():
	return tender_report_entity_filter() + tender_closing_soon_extra_filters()
