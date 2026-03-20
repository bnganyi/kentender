from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from kentender_phase1.utils import create_revision_snapshot, supersede_previous_plan_version


def validate(doc, method=None):
    if not doc.parent_plan:
        frappe.throw(_("Parent Plan is required."))
    if not doc.reason:
        frappe.throw(_("Reason is required."))


def on_submit(doc, method=None):
    doc.db_set("submitted_on", now_datetime(), update_modified=False)
    create_revision_snapshot(doc)
    supersede_previous_plan_version(doc.parent_plan)
