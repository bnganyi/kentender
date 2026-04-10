# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Apply approved budget revisions to line envelopes (BUD-013).

- Adjusts ``Budget Line.allocated_amount`` only (no new **Budget Ledger Entry** rows).
- Creates **Budget Allocation** rows (status Applied) and audit events.
- Decreases / transfer-out enforce ``minimum_allocated_envelope`` from ledger semantics.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, today

from kentender_budget.services.budget_audit import log_budget_audit
from kentender_budget.services.budget_availability import minimum_allocated_envelope
from kentender_budget.services.budget_ledger_posting import lock_budget_line_for_update
from kentender_budget.services.budget_line_derived_totals import on_budget_ledger_post_recalculate_line

BA = "Budget Allocation"
BL = "Budget Line"
BR = "Budget Revision"


def apply_budget_revision(revision_id: str) -> None:
	"""Apply an **Approved** revision once; sets status to **Applied**."""
	if not revision_id or not frappe.db.exists(BR, revision_id):
		frappe.throw(_("Budget Revision not found."), frappe.DoesNotExistError)
	rev = frappe.get_doc(BR, revision_id)
	st = (rev.status or "").strip()
	if st == "Applied":
		frappe.throw(_("This revision has already been applied."), frappe.ValidationError, title=_("Invalid status"))
	if st != "Approved":
		frappe.throw(
			_("Only Approved revisions can be applied."),
			frappe.ValidationError,
			title=_("Invalid status"),
		)
	for row in rev.lines:
		_apply_revision_line(rev, row)
	rev.db_set("status", "Applied", update_modified=True)
	log_budget_audit(
		"kt.budget.revision.applied",
		procuring_entity=rev.procuring_entity,
		target_doctype=BR,
		target_docname=rev.name,
		payload={
			"budget": rev.budget,
			"lines": [
				{
					"change_type": r.change_type,
					"change_amount": flt(r.change_amount),
					"source": r.source_budget_line,
					"target": r.target_budget_line,
				}
				for r in rev.lines
			],
		},
	)


def _line_ctx(line_name: str) -> dict:
	row = frappe.db.get_value(
		BL,
		line_name,
		["budget", "procuring_entity", "fiscal_year", "currency", "allocated_amount"],
		as_dict=True,
	)
	if not row:
		frappe.throw(_("Budget Line not found."), frappe.DoesNotExistError)
	return row


def _set_allocated(line_name: str, new_amount: float) -> None:
	frappe.db.set_value(
		BL,
		line_name,
		{"allocated_amount": flt(new_amount)},
		update_modified=True,
	)
	on_budget_ledger_post_recalculate_line(line_name)


def _assert_can_decrease(line_name: str, decrease_by: float) -> None:
	floor_amt = minimum_allocated_envelope(line_name)
	row = frappe.db.get_value(BL, line_name, "allocated_amount")
	cur = flt(row)
	new_a = cur - flt(decrease_by)
	if new_a + 1e-9 < floor_amt:
		frappe.throw(
			_(
				"Cannot decrease below minimum envelope ({0}); would leave {1} but floor is {2}."
			).format(frappe.bold(line_name), new_a, floor_amt),
			frappe.ValidationError,
			title=_("Exposure conflict"),
		)


def _create_allocation(
	*,
	budget_line: str,
	budget: str,
	entity: str,
	fiscal_year: str,
	currency: str,
	amount: float,
	allocation_type: str,
	revision_name: str,
) -> None:
	doc = frappe.get_doc(
		{
			"doctype": BA,
			"name": f"KT-BA-{frappe.generate_hash(length=14)}",
			"budget_line": budget_line,
			"budget": budget,
			"procuring_entity": entity,
			"fiscal_year": fiscal_year,
			"currency": currency,
			"allocation_date": today(),
			"allocation_amount": flt(amount),
			"allocation_type": allocation_type,
			"allocation_reference": revision_name,
			"status": "Applied",
		}
	)
	doc.insert(ignore_permissions=True)
	log_budget_audit(
		"kt.budget.allocation.applied",
		procuring_entity=entity,
		target_doctype=BA,
		target_docname=doc.name,
		payload={
			"budget_line": budget_line,
			"allocation_type": allocation_type,
			"amount": flt(amount),
			"revision": revision_name,
		},
	)


def _apply_revision_line(rev: frappe.model.document.Document, row) -> None:
	ct = (row.change_type or "").strip()
	amt = flt(row.change_amount)
	rev_name = rev.name
	budget = rev.budget
	entity = rev.procuring_entity

	if ct == "Increase":
		tgt = row.target_budget_line
		lock_budget_line_for_update(tgt)
		ctx = _line_ctx(tgt)
		new_a = flt(ctx.allocated_amount) + amt
		_set_allocated(tgt, new_a)
		_create_allocation(
			budget_line=tgt,
			budget=budget,
			entity=entity,
			fiscal_year=ctx.fiscal_year,
			currency=ctx.currency,
			amount=amt,
			allocation_type="Revision Apply",
			revision_name=rev_name,
		)
	elif ct == "Decrease":
		src = row.source_budget_line
		lock_budget_line_for_update(src)
		_assert_can_decrease(src, amt)
		ctx = _line_ctx(src)
		new_a = flt(ctx.allocated_amount) - amt
		_set_allocated(src, new_a)
		_create_allocation(
			budget_line=src,
			budget=budget,
			entity=entity,
			fiscal_year=ctx.fiscal_year,
			currency=ctx.currency,
			amount=amt,
			allocation_type="Revision Apply",
			revision_name=rev_name,
		)
	elif ct == "Transfer":
		src = row.source_budget_line
		tgt = row.target_budget_line
		for lid in sorted([src, tgt]):
			lock_budget_line_for_update(lid)
		_assert_can_decrease(src, amt)
		ctx_s = _line_ctx(src)
		ctx_t = _line_ctx(tgt)
		_set_allocated(src, flt(ctx_s.allocated_amount) - amt)
		_set_allocated(tgt, flt(ctx_t.allocated_amount) + amt)
		_create_allocation(
			budget_line=src,
			budget=budget,
			entity=entity,
			fiscal_year=ctx_s.fiscal_year,
			currency=ctx_s.currency,
			amount=amt,
			allocation_type="Transfer Out",
			revision_name=rev_name,
		)
		_create_allocation(
			budget_line=tgt,
			budget=budget,
			entity=entity,
			fiscal_year=ctx_t.fiscal_year,
			currency=ctx_t.currency,
			amount=amt,
			allocation_type="Transfer In",
			revision_name=rev_name,
		)
