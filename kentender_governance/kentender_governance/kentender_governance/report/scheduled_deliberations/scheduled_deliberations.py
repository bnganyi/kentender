# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.deliberation_queue_queries import (
	deliberation_report_entity_filter,
	get_scheduled_deliberations,
	scheduled_deliberation_row_values,
	scheduled_deliberations_report_columns,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_scheduled_deliberations(procuring_entity=entity or None)
	data = [scheduled_deliberation_row_values(r) for r in rows]
	return scheduled_deliberations_report_columns(), data


def get_filters():
	return deliberation_report_entity_filter()
