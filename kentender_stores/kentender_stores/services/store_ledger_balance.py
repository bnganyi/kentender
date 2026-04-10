# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""OPS-STORY-011: derive on-hand quantities from **Store Ledger Entry** (no stored running balance)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe import _
from frappe.utils import flt, get_datetime

SLE = "Store Ledger Entry"
STORE = "Store"


def _balance_where(
	store: str,
	*,
	item_reference: str | None,
	as_of_datetime: datetime | str | None,
) -> tuple[str, dict[str, Any]]:
	conds = ["store = %(store)s"]
	params: dict[str, Any] = {"store": store}
	if item_reference:
		conds.append("item_reference = %(item)s")
		params["item"] = item_reference.strip()
	if as_of_datetime:
		conds.append("posting_datetime <= %(as_of)s")
		params["as_of"] = get_datetime(as_of_datetime)
	return " AND ".join(conds), params


def get_item_balance(
	store: str,
	item_reference: str,
	*,
	as_of_datetime: datetime | str | None = None,
) -> float:
	"""Net quantity for one **item_reference** at **store** (In − Out)."""
	rows = get_store_balances(
		store, item_reference=item_reference, as_of_datetime=as_of_datetime, include_zero=True
	)
	if not rows:
		return 0.0
	return flt(rows[0].get("quantity"))


def get_store_balances(
	store: str,
	*,
	item_reference: str | None = None,
	as_of_datetime: datetime | str | None = None,
	include_zero: bool = False,
) -> list[dict[str, Any]]:
	"""Roll up ledger lines by **item_reference**; **quantity** is signed on-hand (In − Out).

	:param as_of_datetime: If set, only lines with ``posting_datetime`` on or before this instant.
	:param include_zero: If False, omit rows where balance is (approximately) zero.
	"""
	if not frappe.db.exists(STORE, store):
		frappe.throw(_("Store not found."), frappe.ValidationError)

	where_sql, params = _balance_where(store, item_reference=item_reference, as_of_datetime=as_of_datetime)

	agg = frappe.db.sql(
		f"""
		SELECT
			item_reference,
			SUM(IF(entry_direction = 'In', quantity, -quantity)) AS balance
		FROM `tabStore Ledger Entry`
		WHERE {where_sql}
		GROUP BY item_reference
		ORDER BY item_reference
		""",
		params,
		as_dict=True,
	)

	out: list[dict[str, Any]] = []
	for row in agg or []:
		q = flt(row.get("balance"))
		if not include_zero and abs(q) < 1e-9:
			continue
		w2, p2 = _balance_where(store, item_reference=row.get("item_reference"), as_of_datetime=as_of_datetime)
		uom_row = frappe.db.sql(
			f"""
			SELECT unit_of_measure
			FROM `tabStore Ledger Entry`
			WHERE {w2}
			ORDER BY posting_datetime DESC, name DESC
			LIMIT 1
			""",
			p2,
		)
		uom = uom_row[0][0] if uom_row else ""
		out.append(
			{
				"item_reference": row.get("item_reference"),
				"quantity": q,
				"unit_of_measure": uom or "",
			}
		)
	return out


@frappe.whitelist()
def get_store_balances_api(
	store: str | None = None,
	item_reference: str | None = None,
	as_of_datetime: str | None = None,
	include_zero: int | bool = 0,
):
	if not store:
		frappe.throw(_("store is required."), frappe.ValidationError)
	return get_store_balances(
		store,
		item_reference=item_reference or None,
		as_of_datetime=as_of_datetime or None,
		include_zero=bool(include_zero),
	)


@frappe.whitelist()
def get_item_balance_api(
	store: str | None = None,
	item_reference: str | None = None,
	as_of_datetime: str | None = None,
):
	if not store or not item_reference:
		frappe.throw(_("store and item_reference are required."), frappe.ValidationError)
	return {"quantity": get_item_balance(store, item_reference, as_of_datetime=as_of_datetime or None)}
