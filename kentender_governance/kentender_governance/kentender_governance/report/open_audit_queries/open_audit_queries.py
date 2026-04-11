# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.audit_reporting_queries import (
	get_open_audit_queries,
	open_audit_queries_columns,
	open_audit_queries_row_values,
)


def execute(filters=None):
	rows = get_open_audit_queries()
	data = [open_audit_queries_row_values(r) for r in rows]
	return open_audit_queries_columns(), data
