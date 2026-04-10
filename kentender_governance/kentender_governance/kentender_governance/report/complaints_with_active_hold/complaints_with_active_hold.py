# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.complaint_queue_queries import (
	complaints_active_hold_columns,
	complaints_active_hold_row_values,
	get_complaints_with_active_hold,
)


def execute(filters=None):
	rows = get_complaints_with_active_hold()
	data = [complaints_active_hold_row_values(r) for r in rows]
	return complaints_active_hold_columns(), data
