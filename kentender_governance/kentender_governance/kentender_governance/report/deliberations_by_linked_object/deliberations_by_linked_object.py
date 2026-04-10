# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.deliberation_queue_queries import (
	deliberation_report_entity_filter,
	deliberations_linked_extra_filters,
	deliberations_linked_row_values,
	deliberations_linked_report_columns,
	get_deliberations_by_linked_object,
)


def execute(filters=None):
	filters = filters or {}
	ldt = (filters.get("linked_doctype") or "").strip()
	ldn = (filters.get("linked_docname") or "").strip()
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_deliberations_by_linked_object(
		linked_doctype=ldt,
		linked_docname=ldn,
		procuring_entity=entity or None,
	)
	data = [deliberations_linked_row_values(r) for r in rows]
	return deliberations_linked_report_columns(), data


def get_filters():
	return deliberations_linked_extra_filters() + deliberation_report_entity_filter()
