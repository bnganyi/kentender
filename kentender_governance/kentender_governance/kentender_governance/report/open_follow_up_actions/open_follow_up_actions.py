# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.deliberation_queue_queries import (
	deliberation_report_entity_filter,
	get_open_follow_up_actions,
	open_follow_up_actions_report_columns,
	open_follow_up_row_values,
)


def execute(filters=None):
	filters = filters or {}
	entity = (filters.get("procuring_entity") or "").strip()
	rows = get_open_follow_up_actions(procuring_entity=entity or None)
	data = [open_follow_up_row_values(r) for r in rows]
	return open_follow_up_actions_report_columns(), data


def get_filters():
	return deliberation_report_entity_filter()
