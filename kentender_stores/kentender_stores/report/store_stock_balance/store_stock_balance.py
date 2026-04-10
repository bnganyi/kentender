# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _

from kentender_stores.services.store_ledger_balance import get_store_balances


def _filter_store_value(filters: dict) -> str | None:
	raw = filters.get("store") or filters.get("name")
	if raw is None:
		return None
	if isinstance(raw, (list, tuple)):
		return raw[-1] if raw else None
	return raw


def execute(filters=None):
	filters = filters or {}
	store = _filter_store_value(filters)
	if not store:
		frappe.throw(_("Set the **Store** filter to run this report."))

	rows = get_store_balances(store, include_zero=False)
	columns = [
		_("Item Reference") + ":Data:200",
		_("On Hand") + ":Float:120",
		_("UOM") + ":Data:80",
	]
	data = [[r.get("item_reference"), r.get("quantity"), r.get("unit_of_measure")] for r in rows]
	return columns, data
