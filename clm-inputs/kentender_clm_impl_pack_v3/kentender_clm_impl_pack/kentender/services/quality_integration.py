import frappe
from frappe import _

def create_quality_inspection_for_task(task_name: str) -> str:
    task = frappe.get_doc("Task", task_name)
    qi = frappe.get_doc({
        "doctype": "Quality Inspection",
        "inspection_type": "Incoming",
        "reference_type": "Task",
        "reference_name": task.name,
        "report_date": frappe.utils.nowdate(),
    })
    qi.insert(ignore_permissions=True)
    return qi.name
