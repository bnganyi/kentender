# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Backfill evaluation_order on KenTender Workflow Policy after WF-007 field add."""

from __future__ import annotations

import frappe


def execute():
	frappe.db.sql(
		"""
		UPDATE `tabKenTender Workflow Policy`
		SET evaluation_order = 100
		WHERE evaluation_order IS NULL OR evaluation_order = 0
		"""
	)
