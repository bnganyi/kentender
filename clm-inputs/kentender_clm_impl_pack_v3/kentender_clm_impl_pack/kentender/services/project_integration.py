import frappe

def create_project_for_contract(contract_name: str) -> str:
    contract = frappe.get_doc("Contract", contract_name)
    existing = frappe.db.get_value("Project", {"contract": contract.name}, "name")
    if existing:
        return existing
    project = frappe.get_doc({
        "doctype": "Project",
        "project_name": contract.contract_title,
        "company": contract.company,
        "status": "Open",
        "contract": contract.name,
    })
    project.insert(ignore_permissions=True)
    return project.name
