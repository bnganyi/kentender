# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.complaint_queue_queries import (
	complaints_awaiting_admissibility_columns,
	complaints_awaiting_admissibility_row_values,
	get_complaints_awaiting_admissibility,
)


def execute(filters=None):
	rows = get_complaints_awaiting_admissibility()
	data = [complaints_awaiting_admissibility_row_values(r) for r in rows]
	return complaints_awaiting_admissibility_columns(), data
