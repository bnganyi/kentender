# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_assets.services.asset_tracking_queries import (
	get_open_maintenance_records,
	open_maintenance_columns,
	open_maintenance_row_values,
)


def execute(filters=None):
	rows = get_open_maintenance_records()
	data = [open_maintenance_row_values(r) for r in rows]
	return open_maintenance_columns(), data
