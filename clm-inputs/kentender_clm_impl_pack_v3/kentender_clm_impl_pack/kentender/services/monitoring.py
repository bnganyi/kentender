import frappe

def score_risk_level(risks):
    n = len(risks)
    if n <= 1: return "Low"
    if n <= 3: return "Medium"
    if n <= 5: return "High"
    return "Critical"

def get_milestone_metrics(contract_name):
    tasks = frappe.get_all("Task", filters={"contract": contract_name, "is_contract_milestone": 1},
                           fields=["name","milestone_status","exp_end_date"])
    total = len(tasks)
    accepted = sum(1 for t in tasks if t.milestone_status == "Accepted")
    overdue = sum(1 for t in tasks if t.exp_end_date and t.exp_end_date < frappe.utils.nowdate()
                  and t.milestone_status not in ("Accepted","Payment Eligible"))
    progress = (accepted / total * 100) if total else 0
    return {"total": total, "accepted": accepted, "overdue": overdue, "progress_percent": progress}

def get_payment_metrics(contract_name):
    invoices = frappe.get_all("Purchase Invoice", filters={"contract": contract_name, "docstatus": 1},
                              fields=["name","grand_total","outstanding_amount"])
    amount_invoiced = sum(float(i.grand_total or 0) for i in invoices)
    outstanding = sum(float(i.outstanding_amount or 0) for i in invoices)
    return {"amount_invoiced": amount_invoiced, "amount_paid": amount_invoiced - outstanding, "outstanding_amount": outstanding}

def get_outstanding_obligations(contract_name):
    obligations = []
    overdue_tasks = frappe.get_all("Task", filters={"contract": contract_name, "is_contract_milestone": 1},
                                   fields=["name","subject","exp_end_date","milestone_status"])
    for t in overdue_tasks:
        if t.exp_end_date and t.exp_end_date < frappe.utils.nowdate() and t.milestone_status not in ("Accepted","Payment Eligible"):
            obligations.append(f"Overdue milestone: {t.subject}")
    unpaid = frappe.get_all("Purchase Invoice", filters={"contract": contract_name, "docstatus": 1, "outstanding_amount": [">", 0]}, fields=["name"])
    for inv in unpaid:
        obligations.append(f"Outstanding payment on invoice: {inv.name}")
    return obligations

def get_contract_risks(contract_name):
    risks = []
    contract = frappe.get_doc("Contract", contract_name)
    if contract.status == "Suspended":
        risks.append("Contract is suspended")
    return risks

def build_monthly_report(contract_name, company, report_month):
    from kentender.services.retention_workflow import get_contract_retention_balance
    milestone = get_milestone_metrics(contract_name)
    payment = get_payment_metrics(contract_name)
    obligations = get_outstanding_obligations(contract_name)
    risks = get_contract_risks(contract_name)
    return frappe.get_doc({
        "doctype": "Monthly Contract Monitoring Report",
        "contract": contract_name,
        "company": company,
        "report_month": report_month,
        "prepared_on": frappe.utils.now_datetime(),
        "milestone_summary": f"Accepted {milestone['accepted']} of {milestone['total']} milestones. Overdue: {milestone['overdue']}.",
        "payment_summary": f"Invoiced: {payment['amount_invoiced']}, Paid: {payment['amount_paid']}, Outstanding: {payment['outstanding_amount']}.",
        "outstanding_obligations": "\n".join(obligations),
        "contract_risks": "\n".join(risks),
        "progress_percent": milestone["progress_percent"],
        "amount_invoiced": payment["amount_invoiced"],
        "amount_paid": payment["amount_paid"],
        "outstanding_amount": payment["outstanding_amount"],
        "retention_balance": get_contract_retention_balance(contract_name),
        "open_claims_count": frappe.db.count("Claim", {"contract": contract_name, "status": ["not in", ["Settled","Rejected"]]}),
        "open_disputes_count": frappe.db.count("Dispute Case", {"contract": contract_name, "status": ["in", ["Open","In Progress"]]}),
        "open_defects_count": frappe.db.count("Defect Liability Case", {"contract": contract_name, "status": ["in", ["Open","Under Review","Assigned","Under Remedy","Escalated"]]}),
        "overall_risk_level": score_risk_level(risks)
    })

def create_monthly_contract_monitoring_reports():
    contracts = frappe.get_all("Contract", filters={"status": ["in", ["Active","Suspended"]]}, fields=["name","company"])
    report_month = frappe.utils.get_first_day(frappe.utils.nowdate())
    for c in contracts:
        existing = frappe.db.get_value("Monthly Contract Monitoring Report", {"contract": c.name, "report_month": report_month}, "name")
        if not existing:
            build_monthly_report(c.name, c.company, report_month).insert(ignore_permissions=True)
