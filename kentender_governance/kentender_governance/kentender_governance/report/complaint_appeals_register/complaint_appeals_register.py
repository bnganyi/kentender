# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.complaint_queue_queries import (
	complaint_appeals_report_columns,
	complaint_appeals_row_values,
	get_complaint_appeals_register,
)


def execute(filters=None):
	rows = get_complaint_appeals_register()
	data = [complaint_appeals_row_values(r) for r in rows]
	return complaint_appeals_report_columns(), data
