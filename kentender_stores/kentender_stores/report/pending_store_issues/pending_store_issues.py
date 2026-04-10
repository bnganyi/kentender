# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_stores.services.store_queue_queries import (
	get_pending_store_issues,
	pending_store_issues_columns,
	pending_store_issues_row_values,
)


def execute(filters=None):
	rows = get_pending_store_issues()
	data = [pending_store_issues_row_values(r) for r in rows]
	return pending_store_issues_columns(), data
