# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from kentender_stores.services.store_queue_queries import (
	get_open_stock_movements,
	open_stock_movements_columns,
	open_stock_movements_row_values,
)


def execute(filters=None):
	rows = get_open_stock_movements()
	data = [open_stock_movements_row_values(r) for r in rows]
	return open_stock_movements_columns(), data
