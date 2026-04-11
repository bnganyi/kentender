# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_assets.services.asset_tracking_queries import (
	draft_disposals_columns,
	draft_disposals_row_values,
	get_draft_disposal_records,
)


def execute(filters=None):
	rows = get_draft_disposal_records()
	data = [draft_disposals_row_values(r) for r in rows]
	return draft_disposals_columns(), data
