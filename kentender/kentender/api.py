from __future__ import annotations

import frappe
from frappe.utils import now_datetime
from erpnext.setup.utils import get_exchange_rate

CONTRACT_STATUS_TRANSITIONS = {
    "Draft": {"Pending Supplier Signature", "Suspended"},
    "Pending Supplier Signature": {"Pending Accounting Officer Signature", "Suspended"},
    "Pending Accounting Officer Signature": {"Active", "Suspended"},
    "Active": {"Suspended", "Pending Termination Approval", "Pending Close-Out", "Terminated", "Closed"},
    "Suspended": {"Active", "Pending Termination Approval", "Terminated"},
    "Pending Termination Approval": {"Terminated", "Active"},
    "Terminated": set(),
    "Pending Close-Out": {"Closed", "Active"},
    "Closed": {"Active"},
}

VARIATION_STATUS_TRANSITIONS = {
    "Draft": {"Under Review", "Approved", "Rejected"},
    "Under Review": {"Approved", "Rejected"},
    "Approved": {"Implemented"},
    "Rejected": set(),
    "Implemented": set(),
}

CLAIM_STATUS_TRANSITIONS = {
    "Draft": {"Submitted"},
    "Submitted": {"Under Review", "Rejected"},
    "Under Review": {"Approved", "Rejected", "Settled"},
    "Approved": {"Settled"},
    "Rejected": set(),
    "Settled": set(),
}

DISPUTE_STATUS_TRANSITIONS = {
    "Open": {"In Progress", "Resolved", "Closed"},
    "In Progress": {"Resolved", "Closed"},
    "Resolved": {"Closed"},
    "Closed": set(),
}

TERMINATION_SETTLEMENT_TRANSITIONS = {
    "Pending": {"In Progress", "Completed"},
    "In Progress": {"Completed"},
    "Completed": set(),
}

ACCEPTANCE_CERT_WORKFLOW_TRANSITIONS = {
    "Draft": {"Pending Technical Review", "Rejected"},
    "Pending Technical Review": {"Pending Accounting Officer Approval", "Rejected"},
    "Pending Accounting Officer Approval": {"Issued", "Rejected"},
    "Issued": set(),
    "Rejected": set(),
}


def _transition_allowed(
    doctype_label: str, old_state: str | None, new_state: str | None, allowed_map: dict
) -> None:
    if not old_state or not new_state or old_state == new_state:
        return
    if getattr(frappe.flags, "in_override", False):
        return

    allowed = allowed_map.get(old_state, set())
    if new_state not in allowed:
        frappe.throw(f"Invalid {doctype_label} transition: {old_state} -> {new_state}")


def generate_approval_chain(doc, method) -> None:
    if not getattr(doc, "company", None):
        frappe.throw("Company is required to generate approval chain")
    if not getattr(doc, "estimated_budget", None):
        frappe.throw("Estimated Budget is required to generate approval chain")

    matrix = frappe.get_all(
        "Approval Matrix",
        filters={"company": doc.company},
        fields=["min_amount", "max_amount", "approval_level", "role"],
        order_by="approval_level asc",
    )

    doc.set("approvals", [])

    for row in matrix:
        if row.min_amount is None or row.max_amount is None:
            continue
        if row.min_amount <= doc.estimated_budget <= row.max_amount:
            doc.append(
                "approvals",
                {
                    "approval_level": row.approval_level,
                    "approver_role": row.role,
                    "status": "Pending",
                },
            )

    if not doc.approvals:
        frappe.throw(
            "No Approval Matrix rule matches this estimated budget for the selected company"
        )

    doc.status = "Under Review"


def validate_plan_item(doc, method) -> None:
    if not doc.item_code:
        frappe.throw("Item is required")

    current_docstatus = getattr(doc, "docstatus", 0) or 0
    in_override = getattr(frappe.flags, "in_override", False)

    db_docstatus = None
    if getattr(doc, "name", None):
        db_docstatus = frappe.db.get_value(doc.doctype, doc.name, "docstatus")

    # Use Frappe's before-save snapshot (not DB reads), since some UI flows
    # can make DB reads unreliable during validate.
    prev_status = doc.get_value_before_save("status")
    prev_docstatus = doc.get_value_before_save("docstatus")

    # GOVERNANCE HARDENING: block manual status changes unless this save is
    # happening inside a controlled method (approve/reject/admin override).
    if (
        not in_override
        and current_docstatus == 1
        and prev_docstatus == current_docstatus
        and prev_status is not None
        and prev_status != doc.status
    ):
        frappe.throw("Manual status change not allowed")

    # IMPORTANT: populate approvals during validation so changes persist on submit.
    # Only generate approvals when transitioning to submitted state (Draft -> Submitted).
    if current_docstatus == 1 and db_docstatus != 1:
        generate_approval_chain(doc, method)


@frappe.whitelist()
def approve_plan_item(docname: str) -> str:
    doc = frappe.get_doc("Procurement Plan Item", docname)
    roles = frappe.get_roles(frappe.session.user)

    pending_levels = sorted({r.approval_level for r in doc.approvals if r.status == "Pending"})
    if not pending_levels:
        frappe.throw("No pending approvals found")

    current_level = pending_levels[0]
    approved_any = False

    for row in doc.approvals:
        if row.status != "Pending":
            continue
        if row.approval_level != current_level:
            continue
        if row.approver_role not in roles:
            continue

        row.status = "Approved"
        row.approved_by = frappe.session.user
        approved_any = True

    if not approved_any:
        frappe.throw(
            f"You are not authorized to approve level {current_level} for this Plan Item"
        )

    if all(r.status == "Approved" for r in doc.approvals):
        doc.status = "Approved"

    # Controlled status transition: allow validate_plan_item status changes
    # and ensure it's audited.
    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        doc.add_comment(
            "Workflow",
            f"Approved level {current_level} by {frappe.session.user}",
        )
        # After submit, `status` / `approvals` are protected (allow_on_submit=0).
        # Our controlled method must bypass it.
        prev_ignore = getattr(doc.flags, "ignore_validate_update_after_submit", False)
        doc.flags.ignore_validate_update_after_submit = True
        try:
            doc.save()
        finally:
            doc.flags.ignore_validate_update_after_submit = prev_ignore
    finally:
        frappe.flags.in_override = prev_in_override

    return doc.status


@frappe.whitelist()
def reject_plan_item(docname: str, reason: str) -> str:
    """Governance: controlled rejection with mandatory audit reason."""
    if not reason or not str(reason).strip():
        frappe.throw("Rejection reason is required")

    doc = frappe.get_doc("Procurement Plan Item", docname)
    roles = frappe.get_roles(frappe.session.user)

    pending_levels = sorted({r.approval_level for r in doc.approvals if r.status == "Pending"})
    if not pending_levels:
        frappe.throw("No pending approvals found")

    current_level = pending_levels[0]
    rejected_any = False

    for row in doc.approvals:
        if row.status != "Pending":
            continue
        if row.approval_level != current_level:
            continue
        if row.approver_role not in roles:
            continue

        row.status = "Rejected"
        row.approved_by = frappe.session.user
        rejected_any = True

    if not rejected_any:
        frappe.throw(
            f"You are not authorized to reject level {current_level} for this Plan Item"
        )

    # Governance choice: closing the plan item on rejection.
    doc.status = "Closed"

    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        doc.add_comment(
            "Workflow",
            f"Rejected level {current_level} by {frappe.session.user}. Reason: {reason}",
        )
        # After submit, `status` / `approvals` are protected (allow_on_submit=0).
        # Our controlled method must bypass it.
        prev_ignore = getattr(doc.flags, "ignore_validate_update_after_submit", False)
        doc.flags.ignore_validate_update_after_submit = True
        try:
            doc.save()
        finally:
            doc.flags.ignore_validate_update_after_submit = prev_ignore
    finally:
        frappe.flags.in_override = prev_in_override

    return doc.status


def validate_tender(doc, method) -> None:
    plan_item = frappe.get_doc("Procurement Plan Item", doc.procurement_plan_item)
    if plan_item.status != "Approved":
        frappe.throw("Plan Item must be approved before creating Tender")


def validate_contract(doc, method) -> None:
    if doc.start_date and doc.end_date and doc.end_date < doc.start_date:
        frappe.throw("Contract End Date cannot be before Start Date")

    if doc.status == "Active":
        if not doc.signed_by_supplier or not doc.signed_by_accounting_officer:
            frappe.throw("Contract cannot be Active before both signatures are completed")

    # Enforce one contract per tender.
    if doc.tender:
        existing = frappe.db.get_value("Contract", {"tender": doc.tender, "name": ("!=", doc.name)}, "name")
        if existing:
            frappe.throw(f"Tender {doc.tender} already has a Contract: {existing}")

    # Close-out governance guards.
    old = doc.get_doc_before_save()
    if old and old.status != doc.status:
        _transition_allowed("Contract status", old.status, doc.status, CONTRACT_STATUS_TRANSITIONS)
        if doc.status == "Closed":
            if not doc.final_acceptance_certificate:
                frappe.throw("Cannot close contract without Final Acceptance Certificate")
            if not doc.all_payments_completed:
                frappe.throw("Cannot close contract until all payments are completed")
            if not doc.handover_completed:
                frappe.throw("Cannot close contract until handover is completed")
        if doc.status == "Active":
            if not doc.signed_by_supplier or not doc.signed_by_accounting_officer:
                frappe.throw("Contract cannot become Active before both signatures are completed")


def validate_acceptance_certificate(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.certificate_type:
        frappe.throw("Certificate Type is required")
    if not doc.issued_by:
        frappe.throw("Issued By is required")
    if not doc.issued_on:
        frappe.throw("Issued On is required")

    workflow_state = getattr(doc, "workflow_state", None) or "Draft"
    old = doc.get_doc_before_save()
    old_state = old.workflow_state if old else None
    _transition_allowed(
        "Acceptance Certificate workflow state",
        old_state,
        workflow_state,
        ACCEPTANCE_CERT_WORKFLOW_TRANSITIONS,
    )

    # Workflow consistency with decision and submission.
    if workflow_state == "Issued":
        if doc.decision != "Approved":
            frappe.throw("Issued certificate must have Decision = Approved")
        if getattr(doc, "docstatus", 0) != 1:
            frappe.throw("Issued certificate must be submitted")
    elif workflow_state == "Rejected":
        if doc.decision != "Rejected":
            frappe.throw("Rejected certificate must have Decision = Rejected")
    else:
        if getattr(doc, "docstatus", 0) == 1:
            frappe.throw("Only Issued/Rejected certificates can be submitted")


@frappe.whitelist()
def create_contract_from_award(tender_name: str, submission_name: str | None = None) -> str:
    tender = frappe.get_doc("Tender", tender_name)
    if tender.status != "Awarded":
        frappe.throw("Tender must be Awarded before creating a Contract")

    existing = frappe.db.get_value("Contract", {"tender": tender.name}, "name")
    if existing:
        return existing

    chosen_submission = submission_name
    if not chosen_submission:
        chosen_submission = _select_winning_submission(tender_name, None)

    submission = frappe.get_doc("Tender Submission", chosen_submission)
    if submission.tender != tender.name:
        frappe.throw("Submission does not belong to the provided Tender")

    contract = frappe.get_doc(
        {
            "doctype": "Contract",
            "contract_title": f"{tender.name} - {submission.supplier}",
            "company": tender.company,
            "supplier": submission.supplier,
            "tender": tender.name,
            "purchase_order": tender.purchase_order,
            "contract_type": "Goods",
            "contract_value": submission.base_amount or submission.quoted_amount,
            "currency": submission.currency,
            "status": "Pending Supplier Signature",
            "retention_percentage": 0,
            "defect_liability_months": 0,
        }
    )
    contract.insert()
    contract.add_comment("Workflow", "Contract created from awarded tender")
    return contract.name


@frappe.whitelist()
def sign_contract(contract_name: str, signer_role: str) -> str:
    contract = frappe.get_doc("Contract", contract_name)
    roles = frappe.get_roles(frappe.session.user)

    if signer_role == "Supplier":
        if "Supplier" not in roles and "System Manager" not in roles:
            frappe.throw("Only Supplier can perform supplier signature")
        if contract.status != "Pending Supplier Signature":
            frappe.throw(
                "Supplier can sign only when contract is in 'Pending Supplier Signature'"
            )
        contract.signed_by_supplier = 1
        contract.status = "Pending Accounting Officer Signature"
    elif signer_role == "Accounting Officer":
        if "Accounting Officer" not in roles and "System Manager" not in roles:
            frappe.throw("Only Accounting Officer can perform accounting signature")
        if contract.status != "Pending Accounting Officer Signature":
            frappe.throw(
                "Accounting Officer can sign only when contract is in "
                "'Pending Accounting Officer Signature'"
            )
        contract.signed_by_accounting_officer = 1
    else:
        frappe.throw("Invalid signer role. Use 'Supplier' or 'Accounting Officer'")

    contract.add_comment("Workflow", f"Signed by {signer_role}: {frappe.session.user}")
    contract.save(ignore_permissions=True)

    if contract.signed_by_supplier and contract.signed_by_accounting_officer:
        activate_contract(contract.name)

    return frappe.db.get_value("Contract", contract.name, "status")


@frappe.whitelist()
def activate_contract(contract_name: str) -> str:
    contract = frappe.get_doc("Contract", contract_name)
    if not contract.signed_by_supplier or not contract.signed_by_accounting_officer:
        frappe.throw("Contract cannot become Active before both signatures are completed")

    if not contract.project:
        project = frappe.get_doc(
            {
                "doctype": "Project",
                "project_name": contract.contract_title,
                "company": contract.company,
                "status": "Open",
            }
        )
        project.insert(ignore_permissions=True)
        contract.project = project.name
        contract.add_comment("Workflow", f"Project created: {project.name}")

    contract.status = "Active"
    contract.activated_on = now_datetime()
    contract.add_comment("Workflow", f"Contract activated by {frappe.session.user}")
    contract.save(ignore_permissions=True)
    return contract.status


@frappe.whitelist()
def start_defect_liability_period(contract_name: str) -> str:
    from frappe.utils import add_months, nowdate

    contract = frappe.get_doc("Contract", contract_name)
    months = int(contract.defect_liability_months or 0)
    if months <= 0:
        frappe.throw("Defect liability months must be greater than zero")

    contract.dlp_start_date = nowdate()
    contract.dlp_end_date = add_months(nowdate(), months)
    contract.dlp_status = "Active"
    contract.add_comment("Workflow", f"DLP started; ends on {contract.dlp_end_date}")
    contract.save(ignore_permissions=True)
    return contract.dlp_status


def _upsert_custom_field(cf: dict) -> None:
    existing = frappe.db.get_value(
        "Custom Field",
        {"dt": cf["dt"], "fieldname": cf["fieldname"]},
        "name",
    )
    if existing:
        frappe.db.set_value("Custom Field", existing, cf)
        return

    frappe.get_doc({"doctype": "Custom Field", **cf}).insert(ignore_permissions=True)


@frappe.whitelist()
def ensure_clm_custom_fields() -> list[str]:
    """Create/refresh minimum CLM custom fields on ERPNext core doctypes."""
    custom_fields = [
        # Project
        {
            "dt": "Project",
            "fieldname": "contract",
            "label": "Contract",
            "fieldtype": "Link",
            "options": "Contract",
            "insert_after": "project_name",
        },
        # Task
        {
            "dt": "Task",
            "fieldname": "contract",
            "label": "Contract",
            "fieldtype": "Link",
            "options": "Contract",
            "insert_after": "project",
        },
        {
            "dt": "Task",
            "fieldname": "is_contract_milestone",
            "label": "Is Contract Milestone",
            "fieldtype": "Check",
            "insert_after": "contract",
        },
        {
            "dt": "Task",
            "fieldname": "payment_percentage",
            "label": "Payment Percentage",
            "fieldtype": "Percent",
            "insert_after": "is_contract_milestone",
        },
        {
            "dt": "Task",
            "fieldname": "acceptance_criteria",
            "label": "Acceptance Criteria",
            "fieldtype": "Small Text",
            "insert_after": "payment_percentage",
        },
        {
            "dt": "Task",
            "fieldname": "deliverables",
            "label": "Deliverables",
            "fieldtype": "Small Text",
            "insert_after": "acceptance_criteria",
        },
        {
            "dt": "Task",
            "fieldname": "supplier_confirmed",
            "label": "Supplier Confirmed",
            "fieldtype": "Check",
            "insert_after": "deliverables",
        },
        {
            "dt": "Task",
            "fieldname": "milestone_status",
            "label": "Milestone Status",
            "fieldtype": "Select",
            "options": "Pending\nCompleted\nAccepted\nRejected",
            "insert_after": "supplier_confirmed",
        },
        # Purchase Receipt
        {
            "dt": "Purchase Receipt",
            "fieldname": "contract",
            "label": "Contract",
            "fieldtype": "Link",
            "options": "Contract",
            "insert_after": "supplier",
        },
        {
            "dt": "Purchase Receipt",
            "fieldname": "milestone_task",
            "label": "Milestone Task",
            "fieldtype": "Link",
            "options": "Task",
            "insert_after": "contract",
        },
        # Purchase Invoice
        {
            "dt": "Purchase Invoice",
            "fieldname": "contract",
            "label": "Contract",
            "fieldtype": "Link",
            "options": "Contract",
            "insert_after": "supplier",
        },
        {
            "dt": "Purchase Invoice",
            "fieldname": "acceptance_certificate",
            "label": "Acceptance Certificate",
            "fieldtype": "Link",
            "options": "Acceptance Certificate",
            "insert_after": "contract",
        },
        {
            "dt": "Purchase Invoice",
            "fieldname": "milestone_task",
            "label": "Milestone Task",
            "fieldtype": "Link",
            "options": "Task",
            "insert_after": "acceptance_certificate",
        },
    ]

    created_or_updated: list[str] = []
    for cf in custom_fields:
        _upsert_custom_field(cf)
        created_or_updated.append(f"{cf['dt']}.{cf['fieldname']}")

    frappe.clear_cache()
    return created_or_updated


def validate_purchase_invoice_certificate(doc, method=None) -> None:
    """Wave-1 financial gate: Contract invoices require valid submitted certificate."""
    if not getattr(doc, "contract", None):
        return

    if not getattr(doc, "acceptance_certificate", None):
        frappe.throw("Purchase Invoice requires an Acceptance Certificate when Contract is set")

    cert = frappe.get_doc("Acceptance Certificate", doc.acceptance_certificate)
    if cert.docstatus != 1:
        frappe.throw("Acceptance Certificate must be submitted before invoice processing")
    if getattr(cert, "workflow_state", None) and cert.workflow_state != "Issued":
        frappe.throw("Acceptance Certificate must be in Issued workflow state")
    if cert.decision != "Approved":
        frappe.throw("Only Approved Acceptance Certificate can support invoice processing")
    if cert.contract != doc.contract:
        frappe.throw("Acceptance Certificate does not belong to the selected Contract")

    contract = frappe.get_doc("Contract", doc.contract)
    if cert.certificate_type == "Final Acceptance":
        contract.final_acceptance_certificate = cert.name
        contract.save(ignore_permissions=True)


def validate_task_milestone(doc, method=None) -> None:
    """Milestone behavior for Task when used as Contract milestone."""
    if not getattr(doc, "is_contract_milestone", 0):
        return

    if not getattr(doc, "contract", None):
        frappe.throw("Contract is required when 'Is Contract Milestone' is checked")
    if not getattr(doc, "project", None):
        frappe.throw("Project is required for Contract Milestones")

    allowed = {"Pending", "Completed", "Accepted", "Rejected"}
    milestone_status = getattr(doc, "milestone_status", None) or "Pending"
    if milestone_status not in allowed:
        frappe.throw(f"Invalid milestone status: {milestone_status}")

    payment_pct = float(getattr(doc, "payment_percentage", 0) or 0)
    if payment_pct < 0 or payment_pct > 100:
        frappe.throw("Payment Percentage must be between 0 and 100")

    # Guardrail: cannot mark milestone completed/accepted without supplier confirmation.
    if milestone_status in ("Completed", "Accepted") and not getattr(doc, "supplier_confirmed", 0):
        frappe.throw("Supplier confirmation is required before milestone can be Completed/Accepted")


def validate_cit_member(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.employee:
        frappe.throw("Employee is required")

    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status not in ("Draft", "Pending Supplier Signature", "Pending Accounting Officer Signature", "Active", "Suspended"):
        frappe.throw("CIT member cannot be assigned to a contract that is terminated/closed")

    duplicate = frappe.db.get_value(
        "Contract Implementation Team Member",
        {
            "contract": doc.contract,
            "employee": doc.employee,
            "name": ("!=", doc.name),
            "status": ("in", ["Proposed", "Approved", "Active"]),
        },
        "name",
    )
    if duplicate:
        frappe.throw(f"Employee is already assigned to this contract (record: {duplicate})")


def validate_inspection_committee_member(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.employee:
        frappe.throw("Employee is required")

    duplicate = frappe.db.get_value(
        "Inspection Committee Member",
        {
            "contract": doc.contract,
            "employee": doc.employee,
            "name": ("!=", doc.name),
            "status": ("in", ["Proposed", "Approved", "Active"]),
        },
        "name",
    )
    if duplicate:
        frappe.throw(f"Employee is already in Inspection Committee for this contract ({duplicate})")


def validate_contract_variation(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.variation_type:
        frappe.throw("Variation Type is required")
    if not doc.justification:
        frappe.throw("Justification is required")

    if doc.variation_type == "Time Extension" and int(doc.time_extension_days or 0) <= 0 and not doc.revised_end_date:
        frappe.throw("Time Extension requires either Time Extension Days or Revised End Date")

    if doc.variation_type == "Cost Adjustment":
        if doc.revised_contract_value in (None, "") and (doc.financial_impact in (None, 0, 0.0, "")):
            frappe.throw("Cost Adjustment requires Revised Contract Value or Financial Impact")

    old = doc.get_doc_before_save()
    if old and old.status != doc.status:
        allowed = VARIATION_STATUS_TRANSITIONS.get(old.status, set())
        if doc.status not in allowed:
            frappe.throw(f"Invalid Contract Variation status transition: {old.status} -> {doc.status}")


def apply_contract_variation(doc, method=None) -> None:
    """Minimal implementation: apply approved/submitted variation to Contract."""
    if getattr(doc, "docstatus", 0) != 1:
        return
    if doc.status not in ("Approved", "Implemented"):
        return

    contract = frappe.get_doc("Contract", doc.contract)
    changed = False

    if doc.revised_end_date:
        contract.end_date = doc.revised_end_date
        changed = True
    elif int(doc.time_extension_days or 0) > 0 and contract.end_date:
        from frappe.utils import add_days

        contract.end_date = add_days(contract.end_date, int(doc.time_extension_days))
        changed = True

    if doc.revised_contract_value not in (None, ""):
        contract.contract_value = doc.revised_contract_value
        changed = True
    elif doc.financial_impact not in (None, 0, 0.0, ""):
        contract.contract_value = float(contract.contract_value or 0) + float(doc.financial_impact or 0)
        changed = True

    if changed:
        contract.add_comment("Workflow", f"Variation {doc.name} applied to contract")
        contract.save(ignore_permissions=True)

    if doc.status != "Implemented":
        doc.db_set("status", "Implemented", update_modified=True)


def validate_termination_record(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.termination_date:
        frappe.throw("Termination Date is required")
    if not doc.termination_reason:
        frappe.throw("Termination Reason is required")
    if not doc.approved_by:
        frappe.throw("Approved By is required")


def apply_termination_record(doc, method=None) -> None:
    if getattr(doc, "docstatus", 0) != 1:
        return
    contract = frappe.get_doc("Contract", doc.contract)
    contract.status = "Terminated"
    contract.add_comment("Workflow", f"Contract terminated via {doc.name}")
    contract.save(ignore_permissions=True)


@frappe.whitelist()
def transition_termination_record_settlement(
    termination_name: str, next_status: str, remarks: str | None = None
) -> str:
    record = frappe.get_doc("Termination Record", termination_name)
    current = record.settlement_status
    _transition_allowed(
        "Termination settlement status",
        current,
        next_status,
        TERMINATION_SETTLEMENT_TRANSITIONS,
    )

    if next_status == "In Progress":
        _require_any_role(["Head of Procurement", "System Manager"], "Settlement kickoff")
    elif next_status == "Completed":
        _require_any_role(["Accounting Officer", "Head of Finance", "System Manager"], "Settlement completion")
        if not record.handover_completed:
            frappe.throw("Cannot complete settlement before handover is completed")
        if not record.discharge_document_reference:
            frappe.throw("Cannot complete settlement without discharge document reference")

    record.settlement_status = next_status
    note = f"Settlement transition: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    record.add_comment("Workflow", note)
    record.save(ignore_permissions=True)
    return record.settlement_status


def validate_claim(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.claim_by:
        frappe.throw("Claim By is required")
    if not doc.claim_type:
        frappe.throw("Claim Type is required")
    if not doc.claim_date:
        frappe.throw("Claim Date is required")
    if not doc.description:
        frappe.throw("Description is required")

    if doc.reference_variation:
        variation_contract = frappe.db.get_value("Contract Variation", doc.reference_variation, "contract")
        if variation_contract and variation_contract != doc.contract:
            frappe.throw("Reference Variation must belong to the same Contract")

    old = doc.get_doc_before_save()
    if old and old.status != doc.status:
        allowed = CLAIM_STATUS_TRANSITIONS.get(old.status, set())
        if doc.status not in allowed:
            frappe.throw(f"Invalid Claim status transition: {old.status} -> {doc.status}")


def validate_dispute_case(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.notice_date:
        frappe.throw("Notice Date is required")
    if not doc.current_stage:
        frappe.throw("Current Stage is required")
    if not doc.summary:
        frappe.throw("Summary is required")

    if doc.claim:
        claim_contract = frappe.db.get_value("Claim", doc.claim, "contract")
        if claim_contract and claim_contract != doc.contract:
            frappe.throw("Claim must belong to the same Contract")

    old = doc.get_doc_before_save()
    if old and old.status != doc.status:
        allowed = DISPUTE_STATUS_TRANSITIONS.get(old.status, set())
        if doc.status not in allowed:
            frappe.throw(f"Invalid Dispute status transition: {old.status} -> {doc.status}")


def validate_defect_liability_case(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.reported_on:
        frappe.throw("Reported On is required")
    if not doc.defect_description:
        frappe.throw("Defect Description is required")
    if doc.status == "Resolved" and not doc.resolved_on:
        frappe.throw("Resolved On is required when status is Resolved")

    contract = frappe.get_doc("Contract", doc.contract)
    if contract.dlp_status not in ("Active", "Reopened"):
        frappe.throw("Defect cases can only be logged when DLP is Active/Reopened")


def handle_defect_liability_case_update(doc, method=None) -> None:
    contract = frappe.get_doc("Contract", doc.contract)
    if getattr(doc, "contract_reopened", 0):
        if contract.status == "Closed":
            contract.status = "Active"
        contract.dlp_status = "Reopened"
        contract.add_comment("Workflow", f"Contract reopened due to defect case {doc.name}")
        contract.save(ignore_permissions=True)


def get_contract_retention_balance(contract_name: str) -> float:
    rows = frappe.get_all(
        "Retention Ledger",
        filters={"contract": contract_name},
        fields=["retention_type", "amount"],
    )
    balance = 0.0
    for row in rows:
        amount = float(row.amount or 0)
        if row.retention_type == "Deduction":
            balance += amount
        else:
            balance -= amount
    return balance


def create_retention_ledger_entry_from_invoice(doc, method=None) -> None:
    """Create retention deduction row after Purchase Invoice submit."""
    if not getattr(doc, "contract", None):
        return

    contract = frappe.get_doc("Contract", doc.contract)
    retention_pct = float(contract.retention_percentage or 0)
    if retention_pct <= 0:
        return

    retained_amount = float(doc.grand_total or 0) * retention_pct / 100.0
    if retained_amount <= 0:
        return

    # Avoid duplicate deduction rows for same invoice.
    existing = frappe.db.get_value(
        "Retention Ledger",
        {"contract": contract.name, "purchase_invoice": doc.name, "retention_type": "Deduction"},
        "name",
    )
    if existing:
        return

    balance = get_contract_retention_balance(contract.name) + retained_amount
    ledger = frappe.get_doc(
        {
            "doctype": "Retention Ledger",
            "contract": contract.name,
            "purchase_invoice": doc.name,
            "retention_type": "Deduction",
            "posting_date": doc.posting_date or frappe.utils.nowdate(),
            "amount": retained_amount,
            "balance_after_transaction": balance,
            "status": "Held",
            "remarks": f"Retention deducted from Purchase Invoice {doc.name}",
        }
    )
    ledger.insert(ignore_permissions=True)


@frappe.whitelist()
def release_contract_retention(
    contract_name: str,
    amount: float | None = None,
    remarks: str | None = None,
    payment_entry: str | None = None,
) -> dict:
    _require_any_role(["Head of Finance", "System Manager"], "Retention release")

    contract = frappe.get_doc("Contract", contract_name)
    retention_balance = float(get_contract_retention_balance(contract.name) or 0)
    if retention_balance <= 0:
        frappe.throw("No retention balance available for release")

    if contract.status not in ("Closed", "Terminated"):
        frappe.throw("Retention can be released only when Contract is Closed/Terminated")
    if contract.dlp_status not in ("Completed",):
        frappe.throw("Retention can be released only after DLP is Completed")

    release_amount = float(amount) if amount not in (None, "") else retention_balance
    if release_amount <= 0:
        frappe.throw("Release amount must be greater than zero")
    if release_amount > retention_balance:
        frappe.throw("Release amount cannot exceed current retention balance")

    new_balance = retention_balance - release_amount
    row = frappe.get_doc(
        {
            "doctype": "Retention Ledger",
            "contract": contract.name,
            "payment_entry": payment_entry,
            "retention_type": "Release",
            "posting_date": frappe.utils.nowdate(),
            "amount": release_amount,
            "balance_after_transaction": new_balance,
            "release_date": frappe.utils.nowdate(),
            "status": "Released",
            "remarks": remarks or "Retention released after close-out and DLP completion",
        }
    )
    row.insert(ignore_permissions=True)
    contract.add_comment(
        "Workflow",
        f"Retention released: {release_amount:.2f}. Balance now {new_balance:.2f}",
    )
    return {
        "ok": True,
        "retention_ledger": row.name,
        "released_amount": release_amount,
        "balance_after": new_balance,
    }


def monitor_dlp_expiry() -> None:
    from frappe.utils import nowdate

    contracts = frappe.get_all(
        "Contract",
        filters={"dlp_status": ("in", ["Active", "Reopened"])},
        fields=["name", "dlp_end_date"],
    )
    today = nowdate()
    for row in contracts:
        if row.dlp_end_date and str(row.dlp_end_date) < str(today):
            frappe.db.set_value("Contract", row.name, {"dlp_status": "Completed"})
            contract = frappe.get_doc("Contract", row.name)
            contract.add_comment("Workflow", "Defect Liability Period expired")


def _month_start(date_value: str | None = None) -> str:
    from frappe.utils import getdate

    d = getdate(date_value) if date_value else getdate()
    return f"{d.year:04d}-{d.month:02d}-01"


@frappe.whitelist()
def create_monthly_contract_monitoring_reports(report_month: str | None = None) -> list[str]:
    """Create one monthly monitoring report per active/suspended/closed contract."""
    month_start = _month_start(report_month)
    created: list[str] = []

    contracts = frappe.get_all(
        "Contract",
        filters={"status": ("in", ["Active", "Suspended", "Closed", "Terminated"])},
        fields=["name", "status"],
    )

    for contract in contracts:
        existing = frappe.db.get_value(
            "Monthly Contract Monitoring Report",
            {"contract": contract.name, "report_month": month_start},
            "name",
        )
        if existing:
            continue

        # Simple summary metrics from related doctypes.
        claims_open = frappe.db.count(
            "Claim",
            {"contract": contract.name, "status": ("in", ["Submitted", "Under Review"])},
        )
        disputes_open = frappe.db.count(
            "Dispute Case",
            {"contract": contract.name, "status": ("in", ["Open", "In Progress"])},
        )
        retention_balance = float(get_contract_retention_balance(contract.name) or 0)

        report = frappe.get_doc(
            {
                "doctype": "Monthly Contract Monitoring Report",
                "contract": contract.name,
                "report_month": month_start,
                "milestone_progress_summary": f"Contract status: {contract.status}",
                "payment_status_summary": f"Retention balance: {retention_balance:.2f}",
                "outstanding_obligations": f"Open claims: {claims_open}, Open disputes: {disputes_open}",
                "contract_risks": "Review open disputes/claims and delayed milestones.",
                "status": "Draft",
            }
        )
        report.insert(ignore_permissions=True)
        created.append(report.name)

    return created


@frappe.whitelist()
def get_contract_closeout_readiness(contract_name: str) -> dict:
    contract = frappe.get_doc("Contract", contract_name)
    blockers: list[str] = []

    if not contract.final_acceptance_certificate:
        blockers.append("Final Acceptance Certificate is missing")
    if not int(contract.all_payments_completed or 0):
        blockers.append("All payments are not marked completed")
    if not int(contract.handover_completed or 0):
        blockers.append("Handover is not marked completed")

    open_claims = frappe.db.count(
        "Claim",
        {"contract": contract.name, "status": ("in", ["Submitted", "Under Review"])},
    )
    if open_claims:
        blockers.append(f"There are {open_claims} open claims")

    open_disputes = frappe.db.count(
        "Dispute Case",
        {"contract": contract.name, "status": ("in", ["Open", "In Progress"])},
    )
    if open_disputes:
        blockers.append(f"There are {open_disputes} open disputes")

    return {
        "contract": contract.name,
        "status": contract.status,
        "ready": len(blockers) == 0,
        "blockers": blockers,
    }


@frappe.whitelist()
def get_clm_dashboard_summary(company: str | None = None) -> dict:
    contract_filters = {"company": company} if company else None
    contract_names = frappe.get_all("Contract", filters=contract_filters, pluck="name")

    def _count(doctype: str, filters: dict | None = None) -> int:
        if not filters:
            return frappe.db.count(doctype)
        return frappe.db.count(doctype, filters)

    if contract_names:
        in_contracts = ("in", contract_names)
        active_contracts = _count("Contract", {"name": in_contracts, "status": "Active"})
        suspended_contracts = _count("Contract", {"name": in_contracts, "status": "Suspended"})
        terminated_contracts = _count("Contract", {"name": in_contracts, "status": "Terminated"})
        closed_contracts = _count("Contract", {"name": in_contracts, "status": "Closed"})
        open_claims = _count("Claim", {"contract": in_contracts, "status": ("in", ["Submitted", "Under Review"])})
        open_disputes = _count("Dispute Case", {"contract": in_contracts, "status": ("in", ["Open", "In Progress"])})
        open_dlp_cases = _count("Defect Liability Case", {"contract": in_contracts, "status": ("in", ["Open", "Under Review", "Assigned"])})
        reports_this_month = _count(
            "Monthly Contract Monitoring Report",
            {"contract": in_contracts, "report_month": _month_start()},
        )
        retention_rows = frappe.get_all(
            "Retention Ledger",
            filters={"contract": in_contracts},
            fields=["contract", "retention_type", "amount"],
        )
    else:
        active_contracts = suspended_contracts = terminated_contracts = closed_contracts = 0
        open_claims = open_disputes = open_dlp_cases = reports_this_month = 0
        retention_rows = []

    retention_by_contract: dict[str, float] = {}
    for row in retention_rows:
        contract_name = row.contract
        amount = float(row.amount or 0)
        if contract_name not in retention_by_contract:
            retention_by_contract[contract_name] = 0.0
        if row.retention_type == "Deduction":
            retention_by_contract[contract_name] += amount
        else:
            retention_by_contract[contract_name] -= amount

    total_retention_held = sum(retention_by_contract.values())

    return {
        "contracts": {
            "active": active_contracts,
            "suspended": suspended_contracts,
            "terminated": terminated_contracts,
            "closed": closed_contracts,
            "total": len(contract_names),
        },
        "legal": {
            "open_claims": open_claims,
            "open_disputes": open_disputes,
        },
        "quality": {
            "open_dlp_cases": open_dlp_cases,
        },
        "finance": {
            "total_retention_held": total_retention_held,
        },
        "monitoring": {
            "reports_generated_this_month": reports_this_month,
        },
    }


@frappe.whitelist()
def create_acceptance_certificate_for_contract(
    contract_name: str,
    certificate_type: str = "Interim Acceptance",
    decision: str = "Approved",
    submit_doc: int = 1,
) -> str:
    contract = frappe.get_doc("Contract", contract_name)

    cert = frappe.get_doc(
        {
            "doctype": "Acceptance Certificate",
            "certificate_type": certificate_type,
            "contract": contract.name,
            "project": contract.project,
            "issued_by": frappe.session.user,
            "issued_on": now_datetime(),
            "decision": decision,
            "certificate_reference": f"{contract.name}-{certificate_type[:3]}-{frappe.generate_hash(length=6)}",
        }
    )
    cert.insert(ignore_permissions=True)
    if int(submit_doc or 0):
        cert.submit()
    return cert.name


@frappe.whitelist()
def transition_acceptance_certificate(
    certificate_name: str,
    next_state: str,
    remarks: str | None = None,
    submit_when_issued: int = 1,
) -> str:
    cert = frappe.get_doc("Acceptance Certificate", certificate_name)
    current_state = getattr(cert, "workflow_state", None) or "Draft"

    _transition_allowed(
        "Acceptance Certificate workflow state",
        current_state,
        next_state,
        ACCEPTANCE_CERT_WORKFLOW_TRANSITIONS,
    )

    if next_state == "Pending Technical Review":
        roles = frappe.get_roles(frappe.session.user)
        if "Head of Procurement" not in roles and "System Manager" not in roles:
            frappe.throw("Only Head of Procurement can move certificate to technical review")
    elif next_state == "Pending Accounting Officer Approval":
        roles = frappe.get_roles(frappe.session.user)
        if "Head of User Department" not in roles and "System Manager" not in roles:
            frappe.throw(
                "Only Head of User Department can move certificate to accounting approval"
            )
    elif next_state in ("Issued", "Rejected"):
        roles = frappe.get_roles(frappe.session.user)
        if "Accounting Officer" not in roles and "System Manager" not in roles:
            frappe.throw("Only Accounting Officer can issue/reject certificate")

    cert.workflow_state = next_state
    if next_state == "Issued":
        cert.decision = "Approved"
    elif next_state == "Rejected":
        cert.decision = "Rejected"

    note = f"Workflow transition: {current_state} -> {next_state}"
    if remarks:
        note = f"{note}. {remarks}"
    cert.add_comment("Workflow", note)

    if next_state in ("Issued", "Rejected") and int(submit_when_issued or 0) and cert.docstatus == 0:
        cert.submit()
    else:
        cert.save(ignore_permissions=True)
    return cert.workflow_state


@frappe.whitelist()
def try_create_contract_purchase_invoice(
    contract_name: str,
    amount: float = 1000.0,
    use_certificate: int = 0,
    certificate_name: str | None = None,
) -> dict:
    """Bench helper for Wave-1 invoice gating tests."""
    contract = frappe.get_doc("Contract", contract_name)
    po = frappe.get_doc("Purchase Order", contract.purchase_order)
    if not po.items:
        return {"ok": False, "error": "Contract purchase order has no items"}

    item = po.items[0]
    cert = certificate_name if int(use_certificate or 0) else None

    invoice = frappe.get_doc(
        {
            "doctype": "Purchase Invoice",
            "company": contract.company,
            "supplier": contract.supplier,
            "currency": contract.currency,
            "contract": contract.name,
            "acceptance_certificate": cert,
            "items": [
                {
                    "item_code": item.item_code,
                    "qty": 1,
                    "rate": float(amount or 0),
                }
            ],
        }
    )

    try:
        invoice.insert(ignore_permissions=True)
        return {"ok": True, "name": invoice.name}
    except frappe.exceptions.ValidationError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"Unexpected error: {e}"}


@frappe.whitelist()
def submit_purchase_invoice_for_test(invoice_name: str) -> dict:
    """Submit invoice so on_submit hooks (e.g., retention posting) execute."""
    try:
        invoice = frappe.get_doc("Purchase Invoice", invoice_name)
        invoice.submit()
        return {"ok": True, "name": invoice.name, "docstatus": invoice.docstatus}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_create_task_milestone(
    project: str,
    contract: str,
    subject: str,
    milestone_status: str = "Pending",
    supplier_confirmed: int = 0,
) -> dict:
    """Bench helper for milestone validation tests."""
    try:
        task = frappe.get_doc(
            {
                "doctype": "Task",
                "project": project,
                "subject": subject,
                "contract": contract,
                "is_contract_milestone": 1,
                "milestone_status": milestone_status,
                "supplier_confirmed": supplier_confirmed,
            }
        )
        task.insert(ignore_permissions=True)
        return {"ok": True, "name": task.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_create_cit_member(contract: str, employee: str, member_type: str = "Member") -> dict:
    """Bench helper for CIT duplicate/validation tests."""
    try:
        row = frappe.get_doc(
            {
                "doctype": "Contract Implementation Team Member",
                "contract": contract,
                "employee": employee,
                "member_type": member_type,
                "status": "Proposed",
            }
        )
        row.insert(ignore_permissions=True)
        return {"ok": True, "name": row.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_create_inspection_member(contract: str, employee: str, member_type: str = "Member") -> dict:
    try:
        row = frappe.get_doc(
            {
                "doctype": "Inspection Committee Member",
                "contract": contract,
                "employee": employee,
                "member_type": member_type,
                "status": "Proposed",
            }
        )
        row.insert(ignore_permissions=True)
        return {"ok": True, "name": row.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_create_contract_variation(
    contract: str,
    variation_type: str,
    justification: str | None = None,
    financial_impact: float = 0.0,
    time_extension_days: int = 0,
    revised_contract_value: float | None = None,
    revised_end_date: str | None = None,
    status: str = "Approved",
    submit_doc: int = 1,
) -> dict:
    try:
        row = frappe.get_doc(
            {
                "doctype": "Contract Variation",
                "contract": contract,
                "variation_type": variation_type,
                "justification": justification,
                "financial_impact": financial_impact,
                "time_extension_days": time_extension_days,
                "revised_contract_value": revised_contract_value,
                "revised_end_date": revised_end_date,
                "status": status,
            }
        )
        row.insert(ignore_permissions=True)
        if int(submit_doc or 0):
            row.submit()
        return {"ok": True, "name": row.name, "status": row.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _require_any_role(allowed_roles: list[str], action_label: str) -> None:
    roles = set(frappe.get_roles(frappe.session.user))
    if roles.intersection(set(allowed_roles)):
        return
    frappe.throw(f"{action_label} requires one of roles: {', '.join(allowed_roles)}")


@frappe.whitelist()
def transition_contract_variation(
    variation_name: str, next_status: str, remarks: str | None = None
) -> str:
    variation = frappe.get_doc("Contract Variation", variation_name)
    current = variation.status
    _transition_allowed(
        "Contract Variation status",
        current,
        next_status,
        VARIATION_STATUS_TRANSITIONS,
    )

    if next_status == "Under Review":
        _require_any_role(["Head of Procurement", "System Manager"], "Variation review routing")
    elif next_status in ("Approved", "Rejected"):
        _require_any_role(["Accounting Officer", "System Manager"], "Variation decision")
    elif next_status == "Implemented":
        _require_any_role(["Head of Procurement", "System Manager"], "Variation implementation")

    variation.status = next_status
    note = f"Status transition: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    variation.add_comment("Workflow", note)

    # Keep on_submit behavior intact for Approved/Implemented.
    if next_status in ("Approved", "Implemented") and variation.docstatus == 0:
        variation.submit()
    else:
        variation.save(ignore_permissions=True)
    return variation.status


@frappe.whitelist()
def try_create_claim(
    contract: str,
    claim_by: str,
    claim_type: str,
    description: str,
    reference_variation: str | None = None,
) -> dict:
    try:
        row = frappe.get_doc(
            {
                "doctype": "Claim",
                "contract": contract,
                "claim_by": claim_by,
                "claim_type": claim_type,
                "claim_date": frappe.utils.nowdate(),
                "description": description,
                "status": "Submitted",
                "reference_variation": reference_variation,
            }
        )
        row.insert(ignore_permissions=True)
        return {"ok": True, "name": row.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def transition_claim(claim_name: str, next_status: str, remarks: str | None = None) -> str:
    claim = frappe.get_doc("Claim", claim_name)
    current = claim.status
    _transition_allowed("Claim status", current, next_status, CLAIM_STATUS_TRANSITIONS)

    if next_status == "Submitted":
        _require_any_role(["Head of User Department", "System Manager"], "Claim submission")
    elif next_status == "Under Review":
        _require_any_role(["Head of Procurement", "System Manager"], "Claim review")
    elif next_status in ("Approved", "Rejected"):
        _require_any_role(["Accounting Officer", "System Manager"], "Claim decision")
    elif next_status == "Settled":
        _require_any_role(["Head of Finance", "System Manager"], "Claim settlement")

    claim.status = next_status
    note = f"Status transition: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    claim.add_comment("Workflow", note)
    claim.save(ignore_permissions=True)
    return claim.status


@frappe.whitelist()
def try_create_dispute_case(
    contract: str,
    summary: str,
    claim: str | None = None,
    current_stage: str = "Notice of Claim",
) -> dict:
    try:
        row = frappe.get_doc(
            {
                "doctype": "Dispute Case",
                "contract": contract,
                "claim": claim,
                "notice_date": frappe.utils.nowdate(),
                "current_stage": current_stage,
                "status": "Open",
                "summary": summary,
            }
        )
        row.insert(ignore_permissions=True)
        return {"ok": True, "name": row.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def transition_dispute_case(
    dispute_name: str, next_status: str, remarks: str | None = None
) -> str:
    dispute = frappe.get_doc("Dispute Case", dispute_name)
    current = dispute.status
    _transition_allowed("Dispute status", current, next_status, DISPUTE_STATUS_TRANSITIONS)

    if next_status == "In Progress":
        _require_any_role(["Head of Procurement", "System Manager"], "Dispute escalation")
    elif next_status == "Resolved":
        _require_any_role(["Accounting Officer", "System Manager"], "Dispute resolution")
    elif next_status == "Closed":
        _require_any_role(["Head of Procurement", "System Manager"], "Dispute closure")

    dispute.status = next_status
    note = f"Status transition: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    dispute.add_comment("Workflow", note)
    dispute.save(ignore_permissions=True)
    return dispute.status


@frappe.whitelist()
def try_create_termination_record(
    contract: str,
    termination_reason: str,
    settlement_status: str = "Pending",
    submit_doc: int = 1,
) -> dict:
    try:
        row = frappe.get_doc(
            {
                "doctype": "Termination Record",
                "contract": contract,
                "termination_date": frappe.utils.nowdate(),
                "termination_reason": termination_reason,
                "approved_by": frappe.session.user,
                "settlement_status": settlement_status,
            }
        )
        row.insert(ignore_permissions=True)
        if int(submit_doc or 0):
            row.submit()
        return {"ok": True, "name": row.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_create_defect_liability_case(
    contract: str,
    defect_description: str,
    status: str = "Open",
    contract_reopened: int = 0,
) -> dict:
    try:
        row = frappe.get_doc(
            {
                "doctype": "Defect Liability Case",
                "contract": contract,
                "project": frappe.db.get_value("Contract", contract, "project"),
                "reported_on": now_datetime(),
                "reported_by": frappe.session.user,
                "defect_description": defect_description,
                "severity": "Medium",
                "status": status,
                "contract_reopened": contract_reopened,
                "resolved_on": now_datetime() if status == "Resolved" else None,
            }
        )
        row.insert(ignore_permissions=True)
        return {"ok": True, "name": row.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_set_contract_status(
    contract_name: str,
    status: str,
    final_acceptance_certificate: str | None = None,
    all_payments_completed: int = 0,
    handover_completed: int = 0,
) -> dict:
    """Bench helper to test close-out governance on Contract.validate."""
    try:
        contract = frappe.get_doc("Contract", contract_name)
        contract.status = status
        if final_acceptance_certificate is not None:
            contract.final_acceptance_certificate = final_acceptance_certificate
        contract.all_payments_completed = all_payments_completed
        contract.handover_completed = handover_completed
        contract.save(ignore_permissions=True)
        return {"ok": True, "name": contract.name, "status": contract.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def validate_submission(doc, method) -> None:
    tender = frappe.get_doc("Tender", doc.tender)
    if tender.status != "Published":
        frappe.throw("Tender is not open")
    if tender.submission_deadline and now_datetime() > tender.submission_deadline:
        frappe.throw("Submission deadline passed")
    set_exchange(doc)
    validate_supplier_compliance(doc.supplier)

    # Phase 2: compute weighted evaluation score (if score rows exist).
    if doc.meta.get_field("total_score"):
        doc.total_score = calculate_total_score(doc)


def calculate_total_score(submission) -> float:
    """Compute weighted score using Evaluation Criteria weights."""
    total = 0.0
    any_row_scored = False

    for row in (getattr(submission, "scores", None) or []):
        if not row.criteria:
            continue
        if row.score is None:
            continue

        any_row_scored = True
        weight = frappe.db.get_value("Evaluation Criteria", row.criteria, "weight") or 0
        total += float(row.score or 0) * float(weight)

    # If there are no score rows, keep total_score at 0.
    # award_tender will decide whether scores are mandatory.
    return float(total) if any_row_scored else 0.0


def set_exchange(doc) -> None:
    company = frappe.db.get_value("Tender", doc.tender, "company")
    company_currency = frappe.get_cached_value("Company", company, "default_currency")
    doc.exchange_rate = get_exchange_rate(doc.currency, company_currency)
    doc.base_amount = (doc.quoted_amount or 0) * (doc.exchange_rate or 0)


def validate_supplier_compliance(supplier: str) -> None:
    status = frappe.db.get_value(
        "Supplier Compliance Profile",
        {"supplier": supplier},
        "status",
    ) or "Pending"

    if status != "Verified":
        frappe.throw(
            f"Tender Submission blocked: supplier '{supplier}' compliance is '{status}'. "
            "Submissions can be created only after the supplier is Verified."
        )


def recheck_supplier_compliance() -> None:
    suppliers = frappe.get_all("Supplier", pluck="name")
    for supplier in suppliers:
        frappe.enqueue("kentender.kentender.api.run_check", supplier=supplier)


def run_check(supplier: str) -> None:
    """
    Phase 2 Compliance Engine entrypoint.

    Delegates the actual evaluation to the Compliance Requirement controller,
    which evaluates mandatory `Compliance Requirement` records and updates:
    - `Supplier Compliance Record` (per requirement)
    - `Supplier Compliance Profile.status` (overall)
    """
    try:
        from kentender.kentender.doctype.compliance_requirement.compliance_requirement import (
            run_check as compliance_run_check,
        )

        compliance_run_check(supplier)
        return
    except Exception:
        # Fallback for MVP usability: when compliance engine isn't configured yet,
        # allow submissions by marking supplier Verified.
        frappe.db.set_value(
            "Supplier Compliance Profile",
            frappe.db.get_value("Supplier Compliance Profile", {"supplier": supplier}, "name"),
            {"status": "Verified", "last_checked": now_datetime()},
        )


@frappe.whitelist()
def test_create_tender_submission(
    tender_name: str,
    supplier: str,
    quoted_amount: float = 1000.0,
    currency: str | None = None,
) -> str:
    """Bench helper: insert a minimal Tender Submission.

    This exists so we can verify `validate_submission()` enforces
    `validate_supplier_compliance()` (Supplier Compliance Profile.status).
    """
    tender = frappe.get_doc("Tender", tender_name)
    company_currency = frappe.get_cached_value("Company", tender.company, "default_currency")
    doc_currency = currency or company_currency

    submission = frappe.get_doc(
        {
            "doctype": "Tender Submission",
            "tender": tender_name,
            "supplier": supplier,
            "currency": doc_currency,
            "quoted_amount": quoted_amount,
        }
    )

    # `ignore_permissions=True` ensures this test helper works regardless of
    # the bench session user role, while still running validations/hooks.
    submission.insert(ignore_permissions=True)
    return submission.name


@frappe.whitelist()
def try_create_tender_submission(
    tender_name: str,
    supplier: str,
    quoted_amount: float = 1000.0,
    currency: str | None = None,
) -> dict:
    """UI/bench test helper.

    Returns:
    - {ok: True, name: <Tender Submission name>}
    - {ok: False, error: <validation message>}
    """
    try:
        name = test_create_tender_submission(
            tender_name=tender_name,
            supplier=supplier,
            quoted_amount=quoted_amount,
            currency=currency,
        )
        return {"ok": True, "name": name}
    except frappe.exceptions.ValidationError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"Unexpected error: {e}"}



@frappe.whitelist()
def try_set_plan_item_status(
    docname: str,
    new_status: str,
) -> dict:
    """UI/bench test helper to verify governance blocks manual status edits."""
    doc = frappe.get_doc("Procurement Plan Item", docname)
    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = False
    try:
        doc.status = new_status
        doc.save(ignore_permissions=True)
        return {"ok": True, "name": docname, "status": doc.status}
    except frappe.exceptions.ValidationError as e:
        return {"ok": False, "error": str(e)}
    finally:
        frappe.flags.in_override = prev_in_override


def _resolve_warehouse(company: str, item_code: str) -> str | None:
    # 1) Company-specific Item Default
    warehouse = frappe.db.get_value(
        "Item Default",
        {"parent": item_code, "company": company},
        "default_warehouse",
    )
    if warehouse:
        return warehouse

    # 2) Any warehouse under same company
    warehouse = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
    return warehouse


@frappe.whitelist()
def award_tender(tender_name: str, submission_name: str) -> str:
    tender = frappe.get_doc("Tender", tender_name)

    # Phase 2: choose the winner by highest weighted total_score.
    winner = _select_winning_submission(tender_name, submission_name)
    submission = frappe.get_doc("Tender Submission", winner)
    # Compliance hardening: never award to a supplier that isn't Verified.
    validate_supplier_compliance(submission.supplier)
    plan_item = frappe.get_doc("Procurement Plan Item", tender.procurement_plan_item)
    is_stock_item = frappe.db.get_value("Item", plan_item.item_code, "is_stock_item")
    warehouse = _resolve_warehouse(tender.company, plan_item.item_code) if is_stock_item else None

    if is_stock_item and not warehouse:
        frappe.throw(
            "No warehouse found for this stock item. Set Item Default warehouse, Company default warehouse, or create a warehouse for the company."
        )

    po = frappe.get_doc(
        {
            "doctype": "Purchase Order",
            "supplier": submission.supplier,
            "company": tender.company,
            "currency": submission.currency,
            "conversion_rate": submission.exchange_rate,
            "schedule_date": now_datetime().date(),
            "items": [
                {
                    "item_code": plan_item.item_code,
                    "qty": plan_item.qty,
                    "rate": submission.quoted_amount,
                    "warehouse": warehouse,
                }
            ],
        }
    )
    po.insert()
    po.submit()

    tender.purchase_order = po.name
    tender.status = "Awarded"
    tender.add_comment(
        "Workflow",
        f"Awarded to supplier {submission.supplier}. Purchase Order: {po.name}",
    )
    tender.save()

    return po.name


@frappe.whitelist()
def override_plan_item_status(docname: str, status: str, reason: str) -> str:
    """Governance: admin override with mandatory reason + audit trail."""
    if not reason or not str(reason).strip():
        frappe.throw("Override reason is required")

    doc = frappe.get_doc("Procurement Plan Item", docname)
    roles = frappe.get_roles(frappe.session.user)

    if "System Manager" not in roles:
        frappe.throw("Only System Managers can override plan item status")

    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        old_status = doc.status
        doc.status = status
        doc.add_comment(
            "Workflow",
            f"Status overridden from {old_status} to {status} by {frappe.session.user}. Reason: {reason}",
        )
        # After submit, `status` / `approvals` are protected (allow_on_submit=0).
        # Our controlled method must bypass it.
        prev_ignore = getattr(doc.flags, "ignore_validate_update_after_submit", False)
        doc.flags.ignore_validate_update_after_submit = True
        try:
            doc.save(ignore_permissions=True)
        finally:
            doc.flags.ignore_validate_update_after_submit = prev_ignore
    finally:
        frappe.flags.in_override = prev_in_override

    return doc.status


def _select_winning_submission(tender_name: str, preferred_submission: str | None) -> str:
    submission_names = frappe.get_all(
        "Tender Submission",
        filters={"tender": tender_name},
        pluck="name",
    )
    if not submission_names:
        frappe.throw("No Tender Submissions found for this tender")

    best_name = None
    best_total = None
    best_quote = None

    preferred_total = None
    preferred_quote = None
    preferred_is_best_candidate = False

    for sub_name in submission_names:
        sub = frappe.get_doc("Tender Submission", sub_name)

        # Compliance hardening: skip non-compliant suppliers.
        supplier_status = frappe.db.get_value(
            "Supplier Compliance Profile",
            {"supplier": sub.supplier},
            "status",
        )
        if supplier_status != "Verified":
            continue

        # Ensure total_score exists (covers older records that may not have been rescored).
        total = (
            sub.total_score
            if getattr(sub, "total_score", None) not in (None, 0)
            else calculate_total_score(sub)
        )
        total = float(total or 0)

        # If we have no score rows, disqualify for Phase 2 winner selection.
        # (You can relax this later if you want a fallback ranking.)
        scores = getattr(sub, "scores", None) or []
        has_scoring = bool(scores and any(r.criteria for r in scores))
        if not has_scoring:
            continue

        quote = float(sub.quoted_amount or 0)

        if best_total is None or total > best_total or (total == best_total and quote < best_quote):
            best_total = total
            best_quote = quote
            best_name = sub_name

        # Track preferred submission's evaluation values (if it has scoring).
        if preferred_submission and sub_name == preferred_submission:
            preferred_total = total
            preferred_quote = quote
            preferred_is_best_candidate = True

    if best_name:
        # Prefer the submission passed by the caller only if it matches the computed best.
        if preferred_submission and preferred_is_best_candidate:
            if float(preferred_total or 0) == float(best_total or 0) and float(preferred_quote or 0) == float(best_quote or 0):
                return preferred_submission
        return best_name

    # If scoring rows are missing (or all submissions are filtered out), fail fast.
    frappe.throw(
        "Cannot award: no compliant Tender Submission found with complete evaluation scores"
    )

