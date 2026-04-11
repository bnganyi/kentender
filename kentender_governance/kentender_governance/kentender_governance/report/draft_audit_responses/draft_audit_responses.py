# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_governance.services.audit_reporting_queries import (
	draft_audit_responses_columns,
	draft_audit_responses_row_values,
	get_draft_audit_responses,
)


def execute(filters=None):
	rows = get_draft_audit_responses()
	data = [draft_audit_responses_row_values(r) for r in rows]
	return draft_audit_responses_columns(), data
