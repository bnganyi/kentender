import frappe


def execute(filters=None):
    """CLM Hub report: provides one-page navigation to key CLM record lists.

    This is an interim UI grouping so users can test end-to-end flows from the Desk
    even before a full eProcurement navigation/profile is completed.
    """

    def _desk_list_url(doctype: str) -> str:
        # Doctype list routes are handled by the desk hash router.
        return f"/desk#List/{doctype}"

    sections = [
        (
            "Contracts",
            ["Contract", "Task (Milestones)", "Governance Session", "Contract Closeout Archive"],
        ),
        (
            "Milestones (Tasks)",
            ["Task"],
        ),
        (
            "Inspection, Tests, Certificates",
            [
                "Quality Inspection",
                "Inspection Test Plan",
                "Inspection Report",
                "Acceptance Certificate",
            ],
        ),
        (
            "Invoices, Payment, Retention",
            ["Purchase Invoice", "Payment Entry", "Retention Ledger", "Monthly Contract Monitoring Report"],
        ),
        (
            "Variations, Claims, Disputes, Stop Work",
            ["Contract Variation", "Claim", "Dispute Case"],
        ),
        (
            "Termination, DLP",
            ["Termination Record", "Defect Liability Case"],
        ),
    ]

    # Render as a simple HTML list of links.
    data = []
    for title, items in sections:
        parts = []
        for label in items:
            # Allow labels like "Task (Milestones)" to map to doctype Task.
            doctype = label.split(" (")[0].strip()
            parts.append(f'<li><a href="{_desk_list_url(doctype)}">{frappe.utils.escape_html(label)}</a></li>')
        html = "<ul>" + "".join(parts) + "</ul>"
        data.append({"section": title, "links": html})

    columns = [
        {"label": "Section", "fieldname": "section", "fieldtype": "Data", "width": 220},
        {"label": "Links", "fieldname": "links", "fieldtype": "HTML"},
    ]

    return columns, data

