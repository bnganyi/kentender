import frappe
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent.parent

def import_json(path):
    with open(path) as f:
        doc = frappe.get_doc(json.load(f))
    if frappe.db.exists(doc.doctype, doc.name):
        existing = frappe.get_doc(doc.doctype, doc.name)
        existing.update(doc.as_dict())
        existing.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def execute():
    for folder in ["workspaces", "sidebars", "desktop_icons"]:
        for path in sorted((BASE / folder).glob("*.json")):
            import_json(path)
    frappe.clear_cache()
