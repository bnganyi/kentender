# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.complaint_queue_queries import (
	complaints_under_review_columns,
	complaints_under_review_row_values,
	get_complaints_under_review,
)


def execute(filters=None):
	rows = get_complaints_under_review()
	data = [complaints_under_review_row_values(r) for r in rows]
	return complaints_under_review_columns(), data
