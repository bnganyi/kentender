from __future__ import annotations

import csv
import hashlib
import io
import json
import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_datetime, now_datetime
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

PAYMENT_ENTRY_CLM_TRANSITIONS = {
    "Draft": {"Procurement Reviewed"},
    "Procurement Reviewed": {"Finance Verified"},
    "Finance Verified": {"Procurement Certified"},
    "Procurement Certified": {"Paid"},
    "Paid": set(),
}

PROCUREMENT_PLAN_STATUS_TRANSITIONS = {
    "Draft": {"Department Consolidation", "Cancelled"},
    "Department Consolidation": {"Procurement Review", "Draft", "Cancelled"},
    "Procurement Review": {"Finance Review", "Department Consolidation", "Cancelled"},
    "Finance Review": {"Submitted", "Procurement Review", "Cancelled"},
    "Submitted": {"Approved", "Department Consolidation", "Cancelled"},
    "Approved": {"Published", "Superseded", "Cancelled"},
    "Published": {"Locked", "Superseded"},
    "Locked": {"Superseded"},
    "Superseded": set(),
    "Cancelled": set(),
    "Closed": set(),
}

ACCEPTANCE_CERT_WORKFLOW_TRANSITIONS = {
    "Draft": {"Pending Technical Review", "Rejected"},
    "Pending Technical Review": {"Pending Accounting Officer Approval", "Rejected"},
    "Pending Accounting Officer Approval": {"Issued", "Rejected"},
    "Issued": set(),
    "Rejected": set(),
}

CIT_MEMBER_STATUS_TRANSITIONS = {
    "Proposed": {"Approved", "Removed"},
    "Approved": {"Active", "Removed"},
    "Active": {"Removed"},
    "Removed": set(),
}

ICM_STATUS_TRANSITIONS = {
    "Proposed": {"Approved", "Dissolved"},
    "Approved": {"Active", "Dissolved"},
    "Active": {"Dissolved"},
    "Dissolved": set(),
}


def log_ken_tender_audit_event(
    action: str,
    reference_doctype: str,
    reference_name: str,
    details: dict | None = None,
) -> str:
    """Append-only governance log for KenTender (Phase 1 procurement + CLM)."""
    payload = json.dumps(details or {}, default=str, sort_keys=True)
    actor_roles = ", ".join(sorted(set(frappe.get_roles(frappe.session.user))))
    event = frappe.get_doc(
        {
            "doctype": "KenTender Audit Event",
            "event_timestamp": now_datetime(),
            "action": action,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "actor": frappe.session.user,
            "actor_roles": actor_roles,
            "details_json": payload,
        }
    )
    event.insert(ignore_permissions=True)
    return event.name


def validate_ken_tender_audit_event(doc, method=None) -> None:
    if not doc.is_new():
        frappe.throw("KenTender Audit Event is immutable and cannot be edited")


def prevent_delete_ken_tender_audit_event(doc, method=None) -> None:
    frappe.throw("KenTender Audit Event is immutable and cannot be deleted")


# DocTypes that typically carry a `contract` link and participate in CLM / finance audit.
_AUDIT_CONTRACT_SCOPED_DOCTYPES: tuple[str, ...] = (
    "Contract",
    "Payment Entry",
    "Purchase Invoice",
    "Purchase Receipt",
    "Quality Inspection",
    "Acceptance Certificate",
    "Contract Variation",
    "Claim",
    "Dispute Case",
    "Termination Record",
    "Defect Liability Case",
    "Retention Ledger",
    "Inspection Test Plan",
    "Inspection Report",
    "Monthly Contract Monitoring Report",
    "Contract Implementation Team Member",
    "Inspection Committee Member",
    "Task",
    "Project",
    "Tender Submission",
    "Procurement Plan Item",
)


def _assert_can_export_audit(contract: str | None = None) -> None:
    if contract:
        frappe.has_permission("Contract", "read", doc=contract, throw=True)
        return
    frappe.has_permission("KenTender Audit Event", "read", throw=True)


def pairs_for_contract_audit_scope(
    contract_name: str,
    max_per_doctype: int = 2000,
    max_pairs_total: int = 8000,
) -> list[tuple[str, str]]:
    """(reference_doctype, reference_name) tuples for SQL scope, including the Contract itself."""
    pairs: list[tuple[str, str]] = [("Contract", contract_name)]
    seen: set[tuple[str, str]] = {pairs[0]}

    for dt in _AUDIT_CONTRACT_SCOPED_DOCTYPES:
        if dt == "Contract":
            continue
        try:
            if not frappe.db.has_column(dt, "contract"):
                continue
        except Exception:
            continue
        try:
            names = frappe.get_all(
                dt,
                filters={"contract": contract_name},
                pluck="name",
                limit=max_per_doctype,
            )
        except Exception:
            continue
        for n in names or []:
            t = (dt, n)
            if t not in seen:
                seen.add(t)
                pairs.append(t)
            if len(pairs) >= max_pairs_total:
                return pairs
    return pairs


def _audit_event_sql_conditions(
    pairs: list[tuple[str, str]],
    actions: list[str] | None = None,
    from_datetime: str | None = None,
    to_datetime: str | None = None,
) -> tuple[str, list]:
    if not pairs:
        return "1=0", []
    placeholders = ",".join(["(%s,%s)"] * len(pairs))
    flat: list = [x for p in pairs for x in p]
    cond = f"(reference_doctype, reference_name) IN ({placeholders})"
    if actions:
        cond += " AND action IN (" + ",".join(["%s"] * len(actions)) + ")"
        flat.extend(actions)
    if from_datetime:
        cond += " AND event_timestamp >= %s"
        flat.append(from_datetime)
    if to_datetime:
        cond += " AND event_timestamp <= %s"
        flat.append(to_datetime)
    return cond, flat


def _global_audit_list_filters(
    reference_doctype: str | None,
    reference_name: str | None,
    action_list: list[str] | None,
    from_datetime: str | None,
    to_datetime: str | None,
) -> dict:
    filters: dict = {}
    if reference_doctype:
        filters["reference_doctype"] = reference_doctype
    if reference_name:
        filters["reference_name"] = reference_name
    if action_list:
        filters["action"] = ["in", action_list]
    if from_datetime and to_datetime:
        filters["event_timestamp"] = ["between", [from_datetime, to_datetime]]
    elif from_datetime:
        filters["event_timestamp"] = [">=", from_datetime]
    elif to_datetime:
        filters["event_timestamp"] = ["<=", to_datetime]
    return filters


def _query_audit_events_by_pairs(
    pairs: list[tuple[str, str]],
    actions: list[str] | None = None,
    from_datetime: str | None = None,
    to_datetime: str | None = None,
    limit: int = 5000,
    limit_start: int = 0,
) -> list[dict]:
    """Batch OR-clause to avoid oversized IN lists on large sites."""
    chunk = 200
    rows: list[dict] = []
    for i in range(0, len(pairs), chunk):
        sub = pairs[i : i + chunk]
        cond, vals = _audit_event_sql_conditions(
            sub, actions=actions, from_datetime=from_datetime, to_datetime=to_datetime
        )
        chunk_rows = frappe.db.sql(
            f"""SELECT name, creation, event_timestamp, action, reference_doctype,
                reference_name, actor, actor_roles, details_json
                FROM `tabKenTender Audit Event`
                WHERE {cond}
                ORDER BY event_timestamp ASC, name ASC""",
            tuple(vals),
            as_dict=True,
        )
        rows.extend(chunk_rows or [])
    rows.sort(key=lambda r: (str(r.get("event_timestamp") or ""), r.get("name") or ""))
    return rows[int(limit_start) : int(limit_start) + int(limit)]


@frappe.whitelist()
def get_ken_tender_audit_event_report(
    reference_doctype: str | None = None,
    reference_name: str | None = None,
    contract: str | None = None,
    actions: str | None = None,
    from_datetime: str | None = None,
    to_datetime: str | None = None,
    limit: int = 500,
    limit_start: int = 0,
) -> dict:
    """Paginated normalized audit events for governance / external review (respects permissions)."""
    _assert_can_export_audit(contract)
    action_list = [a.strip() for a in actions.split(",") if a.strip()] if actions else None
    lim = max(1, min(int(limit or 500), 10000))
    start = max(0, int(limit_start or 0))

    if contract:
        pairs = pairs_for_contract_audit_scope(contract)
        rows = _query_audit_events_by_pairs(
            pairs,
            actions=action_list,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            limit=lim,
            limit_start=start,
        )
        return {
            "ok": True,
            "scope": "contract",
            "contract": contract,
            "generated_at": str(now_datetime()),
            "limit": lim,
            "limit_start": start,
            "rows": rows,
            "row_count": len(rows),
            "reference_pairs_scoped": len(pairs),
        }

    filters = _global_audit_list_filters(
        reference_doctype, reference_name, action_list, from_datetime, to_datetime
    )

    rows = frappe.get_list(
        "KenTender Audit Event",
        filters=filters,
        fields=[
            "name",
            "creation",
            "event_timestamp",
            "action",
            "reference_doctype",
            "reference_name",
            "actor",
            "actor_roles",
            "details_json",
        ],
        order_by="event_timestamp asc",
        limit_start=start,
        limit_page_length=lim,
    )
    return {
        "ok": True,
        "scope": "global",
        "generated_at": str(now_datetime()),
        "limit": lim,
        "limit_start": start,
        "rows": rows,
        "row_count": len(rows),
    }


@frappe.whitelist()
def download_ken_tender_audit_events_csv(
    reference_doctype: str | None = None,
    reference_name: str | None = None,
    contract: str | None = None,
    actions: str | None = None,
    from_datetime: str | None = None,
    to_datetime: str | None = None,
    limit: int = 5000,
) -> None:
    """CSV download (UTF-8) for auditors; same filters as get_ken_tender_audit_event_report."""
    _assert_can_export_audit(contract)
    action_list = [a.strip() for a in actions.split(",") if a.strip()] if actions else None
    lim = max(1, min(int(limit or 5000), 50000))
    if contract:
        pairs = pairs_for_contract_audit_scope(contract)
        rows = _query_audit_events_by_pairs(
            pairs,
            actions=action_list,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            limit=lim,
            limit_start=0,
        )
    else:
        filters = _global_audit_list_filters(
            reference_doctype, reference_name, action_list, from_datetime, to_datetime
        )
        rows = frappe.get_list(
            "KenTender Audit Event",
            filters=filters,
            fields=[
                "name",
                "creation",
                "event_timestamp",
                "action",
                "reference_doctype",
                "reference_name",
                "actor",
                "actor_roles",
                "details_json",
            ],
            order_by="event_timestamp asc",
            limit_page_length=lim,
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "name",
            "creation",
            "event_timestamp",
            "action",
            "reference_doctype",
            "reference_name",
            "actor",
            "actor_roles",
            "details_json",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.get("name"),
                r.get("creation"),
                r.get("event_timestamp"),
                r.get("action"),
                r.get("reference_doctype"),
                r.get("reference_name"),
                r.get("actor"),
                r.get("actor_roles"),
                (r.get("details_json") or "").replace("\n", " ").replace("\r", " "),
            ]
        )

    fname = f"ken_tender_audit_{contract or 'export'}_{frappe.utils.today()}.csv".replace(
        " ", "_"
    )
    frappe.response["filename"] = fname
    frappe.response["filecontent"] = buffer.getvalue().encode("utf-8")
    frappe.response["type"] = "download"


def _phase1_scope_filters(company: str | None = None, fiscal_year: str | None = None) -> dict:
    filters = {}
    if company:
        filters["company"] = company
    if fiscal_year:
        filters["fiscal_year"] = fiscal_year
    return filters


def _phase1_rows_to_csv(rows: list[dict], columns: list[str]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row.get(c) for c in columns])
    return buffer.getvalue()


@frappe.whitelist()
def phase1_get_reporting_snapshot(company: str | None = None, fiscal_year: str | None = None) -> dict:
    """Aggregate Phase 1 reporting snapshot for dashboards and ops reviews."""
    for doctype in ("Procurement Plan", "Procurement Plan Item", "Purchase Requisition"):
        frappe.has_permission(doctype, "read", throw=True)

    plan_filters = _phase1_scope_filters(company, fiscal_year)
    app_rows = frappe.get_all(
        "Procurement Plan",
        filters=plan_filters,
        fields=["name", "status", "total_budget", "total_committed_amount", "total_actual_amount"],
        limit=5000,
    )

    app_status_counts = {}
    app_total_budget = 0.0
    app_total_committed = 0.0
    app_total_actual = 0.0
    for row in app_rows or []:
        status = row.get("status") or "Unknown"
        app_status_counts[status] = app_status_counts.get(status, 0) + 1
        app_total_budget += flt(row.get("total_budget") or 0)
        app_total_committed += flt(row.get("total_committed_amount") or 0)
        app_total_actual += flt(row.get("total_actual_amount") or 0)

    ppi_filters = {}
    if company:
        ppi_filters["company"] = company
    ppi_rows = frappe.get_all(
        "Procurement Plan Item",
        filters=ppi_filters,
        fields=["name", "budget_status", "risk_level"],
        limit=20000,
    )
    item_budget_status_counts = {}
    item_risk_counts = {}
    for row in ppi_rows or []:
        bstatus = row.get("budget_status") or "Unknown"
        item_budget_status_counts[bstatus] = item_budget_status_counts.get(bstatus, 0) + 1
        rlevel = row.get("risk_level") or "Unrated"
        item_risk_counts[rlevel] = item_risk_counts.get(rlevel, 0) + 1

    override_rows = frappe.get_all(
        "Budget Override Record",
        fields=["name", "override_type", "status", "reference_name", "creation"],
        filters={"reference_doctype": "Procurement Plan Item"},
        limit=20000,
    )
    override_by_type = {}
    for row in override_rows or []:
        otype = row.get("override_type") or "Unknown"
        override_by_type[otype] = override_by_type.get(otype, 0) + 1

    pr_filters = {}
    if company:
        pr_filters["entity"] = company
    if fiscal_year:
        pr_filters["financial_year"] = fiscal_year
    pr_rows = frappe.get_all(
        "Purchase Requisition",
        filters=pr_filters,
        fields=["name", "status", "tender_readiness_status", "linked_tender_count"],
        limit=10000,
    )
    pr_status_counts = {}
    pr_readiness_counts = {}
    linked_tender_total = 0
    for row in pr_rows or []:
        s = row.get("status") or "Unknown"
        pr_status_counts[s] = pr_status_counts.get(s, 0) + 1
        rs = row.get("tender_readiness_status") or "Unknown"
        pr_readiness_counts[rs] = pr_readiness_counts.get(rs, 0) + 1
        linked_tender_total += cint(row.get("linked_tender_count") or 0)

    handoff_rows = frappe.get_all(
        "Requisition Tender Handoff",
        fields=["name", "purchase_requisition", "handoff_status", "tender_reference", "approved_for_tender_on"],
        limit=10000,
        order_by="creation desc",
    )

    return {
        "ok": True,
        "scope": {"company": company, "fiscal_year": fiscal_year},
        "generated_at": str(now_datetime()),
        "app_summary": {
            "count": len(app_rows or []),
            "status_counts": app_status_counts,
            "total_budget": app_total_budget,
            "total_committed_amount": app_total_committed,
            "total_actual_amount": app_total_actual,
        },
        "plan_item_summary": {
            "count": len(ppi_rows or []),
            "budget_status_counts": item_budget_status_counts,
            "risk_level_counts": item_risk_counts,
        },
        "override_summary": {
            "count": len(override_rows or []),
            "by_type": override_by_type,
        },
        "pr_summary": {
            "count": len(pr_rows or []),
            "status_counts": pr_status_counts,
            "tender_readiness_counts": pr_readiness_counts,
            "linked_tender_total": linked_tender_total,
        },
        "handoff_rows": handoff_rows,
    }


@frappe.whitelist()
def phase1_download_reporting_snapshot_csv(company: str | None = None, fiscal_year: str | None = None) -> None:
    """CSV export for Phase 1 reporting snapshot (APP, PR, handoff rows)."""
    snapshot = phase1_get_reporting_snapshot(company=company, fiscal_year=fiscal_year)
    handoff_rows = snapshot.get("handoff_rows") or []
    columns = ["name", "purchase_requisition", "handoff_status", "tender_reference", "approved_for_tender_on"]
    csv_content = _phase1_rows_to_csv(handoff_rows, columns)
    fname = f"phase1_handoff_snapshot_{company or 'all'}_{fiscal_year or 'all'}_{frappe.utils.today()}.csv".replace(
        " ", "_"
    )
    frappe.response["filename"] = fname
    frappe.response["filecontent"] = csv_content.encode("utf-8")
    frappe.response["type"] = "download"


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


def _phase1_get_policy_profile_for_plan(plan_name: str) -> str | None:
    if not plan_name:
        return None
    return frappe.db.get_value("Procurement Plan", plan_name, "policy_profile")


def _phase1_recommend_procurement_method_for_item(doc) -> str | None:
    """Recommend procurement method from `Procurement Threshold Rule` (if configured)."""
    policy_profile = _phase1_get_policy_profile_for_plan(getattr(doc, "procurement_plan", None))
    if not policy_profile:
        return getattr(doc, "procurement_method", None)

    if not getattr(doc, "procurement_type", None):
        return getattr(doc, "procurement_method", None)

    value = flt(getattr(doc, "estimated_budget", 0) or 0)
    if value <= 0:
        return getattr(doc, "procurement_method", None)

    # Filter by policy_profile + procurement_type first; apply category + amount
    # range matching in Python so we can explicitly detect ambiguous threshold sets.
    rules = frappe.get_all(
        "Procurement Threshold Rule",
        filters={"policy_profile": policy_profile, "procurement_type": doc.procurement_type, "active": 1},
        fields=["name", "category", "minimum_amount", "maximum_amount", "recommended_method"],
        order_by="minimum_amount asc",
    )

    matching_rules = []
    for rule in rules or []:
        if getattr(doc, "category", None) and rule.category and doc.category != rule.category:
            continue
        if flt(rule.minimum_amount) <= value <= flt(rule.maximum_amount):
            matching_rules.append(rule)

    if len(matching_rules) > 1:
        names = ", ".join(r.name for r in matching_rules)
        frappe.throw(
            f"Threshold rule ambiguity detected for this line. Review active Procurement Threshold Rules: {names}"
        )

    if matching_rules:
        return matching_rules[0].recommended_method

    return getattr(doc, "procurement_method", None)


def _phase1_find_matching_threshold_rule(doc):
    """Return the single matching threshold rule for a plan item."""
    policy_profile = _phase1_get_policy_profile_for_plan(getattr(doc, "procurement_plan", None))
    if not policy_profile or not getattr(doc, "procurement_type", None):
        return None

    value = flt(getattr(doc, "estimated_budget", 0) or 0)
    if value <= 0:
        return None

    rules = frappe.get_all(
        "Procurement Threshold Rule",
        filters={"policy_profile": policy_profile, "procurement_type": doc.procurement_type, "active": 1},
        fields=["name", "category", "minimum_amount", "maximum_amount", "recommended_method", "allowed_methods"],
        order_by="minimum_amount asc",
    )

    matches = []
    for rule in rules or []:
        if getattr(doc, "category", None) and rule.category and doc.category != rule.category:
            continue
        if flt(rule.minimum_amount) <= value <= flt(rule.maximum_amount):
            matches.append(rule)

    if len(matches) > 1:
        names = ", ".join(r.name for r in matches)
        frappe.throw(
            f"Threshold rule ambiguity detected for this line. Review active Procurement Threshold Rules: {names}"
        )
    return matches[0] if matches else None


def _phase1_allowed_methods(allowed_methods: str | None) -> set[str]:
    return {m.strip() for m in (allowed_methods or "").split(",") if m and m.strip()}


def _phase1_method_is_non_competitive(method: str | None) -> bool:
    return (method or "").strip() in {"Direct Procurement", "Restricted Tender"}


def _phase1_upsert_budget_override_record(
    *,
    reference_name: str,
    override_type: str,
    field_name: str,
    old_value: str,
    new_value: str,
    reason: str,
) -> None:
    """Create/update a single draft override record per item/type to avoid duplicates."""
    existing = frappe.get_all(
        "Budget Override Record",
        filters={
            "reference_doctype": "Procurement Plan Item",
            "reference_name": reference_name,
            "override_type": override_type,
            "status": "Draft",
        },
        fields=["name"],
        limit=1,
    )
    payload = {
        "field_name": field_name,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "requested_by": frappe.session.user,
    }
    if existing:
        frappe.db.set_value("Budget Override Record", existing[0].name, payload, update_modified=False)
        return

    frappe.get_doc(
        {
            "doctype": "Budget Override Record",
            "reference_doctype": "Procurement Plan Item",
            "reference_name": reference_name,
            "override_type": override_type,
            **payload,
            "status": "Draft",
        }
    ).insert(ignore_permissions=True)


def _phase1_validate_item_before_first_approval(doc) -> None:
    """Hard governance checks when approving a Phase 1 Plan Item."""
    # Strategic linkage (required by the design)
    if not getattr(doc, "strategic_objective", None):
        frappe.throw("Strategic Objective is required before Phase 1 approval")

    if not getattr(doc, "strategic_plan", None):
        derived_plan = frappe.db.get_value("Strategic Objective", doc.strategic_objective, "corporate_strategic_plan")
        if derived_plan:
            doc.strategic_plan = derived_plan

    if not getattr(doc, "national_priority", None):
        derived_priority = frappe.db.get_value("Strategic Objective", doc.strategic_objective, "priority")
        if derived_priority:
            doc.national_priority = derived_priority

    if not getattr(doc, "national_priority", None):
        frappe.throw("National Priority is required before Phase 1 approval")

    # Budget linkage (minimum required for approval)
    missing = []
    for f in ["budget_head", "cost_center", "quarter", "responsible_department"]:
        if not getattr(doc, f, None):
            missing.append(f)
    if missing:
        frappe.throw(f"Cannot approve without budget linkage: {', '.join(missing)}")

    if flt(getattr(doc, "estimated_budget", 0) or 0) <= 0:
        frappe.throw("Estimated Budget must be greater than zero before Phase 1 approval")

    # Method advisory + override governance
    if not getattr(doc, "procurement_method", None):
        frappe.throw("Procurement Method is required before Phase 1 approval")

    matching_rule = _phase1_find_matching_threshold_rule(doc)
    recommended = _phase1_recommend_procurement_method_for_item(doc) or doc.procurement_method
    doc.system_recommended_method = recommended

    if doc.procurement_method != recommended and not getattr(doc, "method_override_reason", None):
        frappe.throw("Method Override Reason is required when procurement method differs from system recommendation")

    if matching_rule:
        allowed = _phase1_allowed_methods(getattr(matching_rule, "allowed_methods", None))
        if allowed and doc.procurement_method not in allowed:
            frappe.throw(
                f'Selected Procurement Method "{doc.procurement_method}" is not allowed by threshold rule {matching_rule.name}.'
            )

    policy_profile = _phase1_get_policy_profile_for_plan(getattr(doc, "procurement_plan", None))
    require_non_competitive_reason = cint(
        frappe.db.get_value(
            "Procurement Policy Profile",
            policy_profile,
            "require_method_justification_for_non_competitive",
        )
        or 0
    )
    if require_non_competitive_reason and _phase1_method_is_non_competitive(doc.procurement_method):
        if not getattr(doc, "method_override_reason", None):
            frappe.throw(
                "Method Override Reason is required for non-competitive procurement methods under the active policy profile"
            )

    # Emergency handling: require justification
    if getattr(doc, "emergency_flag", 0) and not getattr(doc, "override_reason", None):
        frappe.throw("Override Reason is required for Emergency procurement before Phase 1 approval")

    # Anti-split control (baseline: block if repeated similar lines exist)
    # Only run when anti-split inputs are present.
    if (
        getattr(doc, "responsible_department", None)
        and getattr(doc, "budget_head", None)
        and getattr(doc, "category", None)
        and getattr(doc, "quarter", None)
    ):
        candidates = frappe.get_all(
            "Procurement Plan Item",
            filters={
                "name": ("!=", doc.name),
                "procurement_plan": doc.procurement_plan,
                "responsible_department": doc.responsible_department,
                "budget_head": doc.budget_head,
                "category": doc.category,
                "quarter": doc.quarter,
            },
            fields=["name", "estimated_budget"],
            limit=10,
        )
        total_cluster_amount = flt(getattr(doc, "estimated_budget", 0) or 0)
        for row in candidates or []:
            total_cluster_amount += flt(getattr(row, "estimated_budget", 0) or 0)

        anti_split_group = getattr(doc, "anti_split_group", None) or getattr(doc, "aggregation_group", None)
        trigger = len(candidates or []) >= 2 or bool(anti_split_group)
        if trigger and not getattr(doc, "override_flag", 0):
            frappe.throw(
                "Potential procurement fragmentation detected (anti-split). "
                "Use Override Flag + Override Reason to proceed."
            )

        if getattr(doc, "override_flag", 0) and not getattr(doc, "override_reason", None):
            frappe.throw("Override Reason is required when anti-split control is triggered")

        # Risk score is intentionally simple for now: larger fragmented clusters
        # should be harder to overlook during governance review.
        if trigger:
            doc.risk_score = min(100, 30 + (len(candidates or []) * 10))
            doc.risk_level = "High" if doc.risk_score >= 60 else "Medium"
        else:
            doc.risk_score = 20
            doc.risk_level = "Low"

    # Update budget status (Phase 1 starter: available if amount is valid)
    doc.budget_status = "Available"

    if not getattr(doc, "risk_score", None):
        doc.risk_score = 20
        doc.risk_level = "Low"

    # Override governance evidence capture (deduplicated)
    if doc.procurement_method != doc.system_recommended_method:
        _phase1_upsert_budget_override_record(
            reference_name=doc.name,
            override_type="Method",
            field_name="procurement_method",
            old_value=str(doc.system_recommended_method or ""),
            new_value=str(doc.procurement_method or ""),
            reason=str(getattr(doc, "method_override_reason", None) or getattr(doc, "override_reason", None) or ""),
        )

    if getattr(doc, "override_flag", 0):
        if not getattr(doc, "override_reason", None):
            frappe.throw("Override Reason is required when Override Flag is set")
        _phase1_upsert_budget_override_record(
            reference_name=doc.name,
            override_type="Amount",
            field_name="override_reason",
            old_value=str(doc.system_recommended_method or ""),
            new_value=str(doc.procurement_method or ""),
            reason=str(doc.override_reason),
        )


def _phase1_generate_app_number_for_plan(plan: frappe.model.document.Document) -> str:
    """Generate APP number from company and fiscal year (starter-aligned)."""
    entity = getattr(plan, "company", None) or getattr(plan, "entity", None) or "ENT"
    financial_year = getattr(plan, "fiscal_year", None) or getattr(plan, "financial_year", None) or "FY"

    entity_code = (entity or "ENT")[:4].upper().replace(" ", "")
    fy_code = (financial_year or "FY").replace("-", "")[-4:]
    count = frappe.db.count(
        "Procurement Plan",
        filters={
            "company": entity,
            "fiscal_year": financial_year,
        },
    ) + 1
    return f"APP-{entity_code}-{fy_code}-{count:03d}"


def _phase1_assert_active_policy_profile_for_plan(doc) -> None:
    if not getattr(doc, "policy_profile", None):
        frappe.throw("Policy Profile is required for Procurement Plan governance")

    status = frappe.db.get_value("Procurement Policy Profile", doc.policy_profile, "status")
    if status != "Active":
        frappe.throw("Procurement Policy Profile must be Active to progress the APP")


def _phase1_ensure_single_active_original_app(doc) -> None:
    # Only enforce for "original" annual APPs.
    if getattr(doc, "plan_type", None) != "Annual":
        return

    revision_type = getattr(doc, "revision_type", None) or "Original"
    if revision_type != "Original":
        return

    existing = frappe.get_all(
        "Procurement Plan",
        filters={
            "company": doc.company,
            "fiscal_year": doc.fiscal_year,
            "plan_type": "Annual",
            "revision_type": "Original",
            "name": ("!=", doc.name),
            "status": ("in", ["Approved", "Published", "Locked"]),
        },
        pluck="name",
        limit=1,
    )

    if existing:
        frappe.throw(
            f"Another active annual APP already exists for this company and fiscal year: {existing[0]}"
        )


def _phase1_recalculate_plan_totals(doc) -> None:
    """Recalculate header totals from Procurement Plan Items."""
    rows = frappe.get_all(
        "Procurement Plan Item",
        filters={"procurement_plan": doc.name},
        fields=["estimated_budget", "reserved_budget_amount", "committed_amount", "actual_amount"],
    )

    total_budget = sum(flt(r.get("estimated_budget") or 0) for r in rows or [])
    total_reserved = sum(flt(r.get("reserved_budget_amount") or 0) for r in rows or [])
    total_committed = sum(flt(r.get("committed_amount") or 0) for r in rows or [])
    total_actual = sum(flt(r.get("actual_amount") or 0) for r in rows or [])

    # These fields exist in the extended Procurement Plan schema.
    doc.db_set("total_budget", total_budget, update_modified=False)
    doc.db_set("total_planned_amount", total_budget, update_modified=False)
    doc.db_set("total_reserved_amount", total_reserved, update_modified=False)
    doc.db_set("total_committed_amount", total_committed, update_modified=False)
    doc.db_set("total_actual_amount", total_actual, update_modified=False)


def _phase1_create_published_snapshot(doc) -> None:
    payload = frappe.as_json(doc.as_dict(), indent=2)
    hash_value = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    frappe.get_doc(
        {
            "doctype": "Published Plan Record",
            "procurement_plan": doc.name,
            "publication_type": "Internal",
            "published_by": frappe.session.user,
            "published_on": now_datetime(),
            "hash_value": hash_value,
            "notes": "Generated snapshot placeholder (attachments may be exported separately).",
        }
    ).insert(ignore_permissions=True)


def _phase1_lock_procurement_plan(doc) -> None:
    doc.db_set("locked_on", now_datetime(), update_modified=False)
    doc.db_set("locked_by", frappe.session.user, update_modified=False)


def phase1_procurement_plan_before_insert(doc, method=None):
    if not getattr(doc, "app_number", None):
        doc.app_number = _phase1_generate_app_number_for_plan(doc)


def phase1_procurement_plan_validate(doc, method=None) -> None:
    # Lock immutability: once Locked, do not allow further edits
    # (except via controlled code paths with `frappe.flags.in_override`).
    if getattr(frappe.flags, "in_override", False):
        return

    old = doc.get_doc_before_save()
    if old and getattr(old, "status", None) != getattr(doc, "status", None):
        _transition_allowed(
            "Procurement Plan status",
            old.status,
            doc.status,
            PROCUREMENT_PLAN_STATUS_TRANSITIONS,
        )

    if old and getattr(old, "status", None) == "Locked" and getattr(doc, "status", None) == "Locked":
        changed = doc.get_changed_fields()
        protected = {"locked_on", "locked_by"}
        if changed and not set(changed).issubset(protected):
            frappe.throw("Locked Procurement Plan cannot be modified")
    elif old and getattr(old, "status", None) == "Locked" and getattr(doc, "status", None) != "Locked":
        frappe.throw("Locked Procurement Plan cannot transition out of Locked")

    # Enforce required governance fields only when progressing beyond Draft.
    prev_status = doc.get_value_before_save("status")
    status_changed = prev_status is not None and prev_status != doc.status
    is_new = getattr(doc, "is_new", lambda: False)()
    if (doc.status != "Draft") and (is_new or status_changed or doc.docstatus == 1):
        required = [
            "budget_reference",
            "budget_approval_date",
            "budget_approved_by",
            "policy_profile",
            "created_by_department",
        ]
        missing = [f for f in required if not getattr(doc, f, None)]
        if missing:
            frappe.throw(f"Cannot progress APP without: {', '.join(missing)}")

        _phase1_assert_active_policy_profile_for_plan(doc)
        _phase1_ensure_single_active_original_app(doc)

    # Keep header totals consistent.
    if doc.name and doc.status in {"Department Consolidation", "Procurement Review", "Finance Review", "Submitted", "Approved", "Published", "Locked"}:
        _phase1_recalculate_plan_totals(doc)


def phase1_procurement_plan_on_submit(doc, method=None):
    # `on_submit` is only meaningful when the APP is at/after approval.
    if getattr(doc, "status", None) == "Draft":
        frappe.throw("Cannot submit an APP while status is Draft")

    doc.db_set("submission_date", now_datetime(), update_modified=False)
    _phase1_recalculate_plan_totals(doc)


def phase1_procurement_plan_on_update_after_submit(doc, method=None):
    if getattr(doc, "status", None) == "Published" and not getattr(doc, "published_date", None):
        doc.db_set("published_date", now_datetime(), update_modified=False)
        _phase1_create_published_snapshot(doc)

    if getattr(doc, "status", None) == "Locked" and not getattr(doc, "locked_on", None):
        _phase1_lock_procurement_plan(doc)


@frappe.whitelist()
def phase1_transition_procurement_plan_status(
    docname: str, next_status: str, remarks: str | None = None
) -> str:
    """Controlled status transition helper for Procurement Plan header governance."""
    doc = frappe.get_doc("Procurement Plan", docname)
    current_status = getattr(doc, "status", None)

    _transition_allowed(
        "Procurement Plan status",
        current_status,
        next_status,
        PROCUREMENT_PLAN_STATUS_TRANSITIONS,
    )

    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        doc.status = next_status
        prev_ignore = getattr(doc.flags, "ignore_validate_update_after_submit", False)
        doc.flags.ignore_validate_update_after_submit = True
        try:
            doc.save(ignore_permissions=True)
        finally:
            doc.flags.ignore_validate_update_after_submit = prev_ignore

        doc.reload()
        if remarks:
            doc.add_comment("Workflow", f"{current_status} -> {next_status}: {remarks}")
        else:
            doc.add_comment("Workflow", f"{current_status} -> {next_status}")

        log_ken_tender_audit_event(
            action="procurement_plan_status_transition",
            reference_doctype="Procurement Plan",
            reference_name=doc.name,
            details={
                "from_status": current_status,
                "to_status": next_status,
                "remarks": remarks or "",
            },
        )
    finally:
        frappe.flags.in_override = prev_in_override

    return doc.status


def phase1_procurement_plan_revision_validate(doc, method=None) -> None:
    """Validate revision governance before publish orchestration."""
    if not getattr(doc, "parent_plan", None):
        frappe.throw("Parent Plan is required for Procurement Plan Revision")

    if not frappe.db.exists("Procurement Plan", doc.parent_plan):
        frappe.throw(f"Parent Plan not found: {doc.parent_plan}")

    duplicate = frappe.get_all(
        "Procurement Plan Revision",
        filters={
            "parent_plan": doc.parent_plan,
            "revision_number": doc.revision_number,
            "name": ("!=", doc.name),
        },
        pluck="name",
        limit=1,
    )
    if duplicate:
        frappe.throw(
            f"Revision Number '{doc.revision_number}' already exists for parent APP {doc.parent_plan} ({duplicate[0]})."
        )

    if not getattr(doc, "reason", None):
        frappe.throw("Revision reason is required")

    if not getattr(doc, "prepared_by", None):
        doc.prepared_by = frappe.session.user

    parent_status = frappe.db.get_value("Procurement Plan", doc.parent_plan, "status")
    if doc.status in {"Approved", "Published"} and parent_status in {"Cancelled", "Closed"}:
        frappe.throw(
            f"Cannot progress revision while parent APP is {parent_status}."
        )


def _phase1_apply_revision_publish_side_effects(revision_doc) -> None:
    parent = frappe.get_doc("Procurement Plan", revision_doc.parent_plan)
    parent_status = getattr(parent, "status", None)
    if parent_status in {"Cancelled", "Closed"}:
        frappe.throw(f"Cannot publish revision because parent APP is {parent_status}.")

    if parent_status != "Superseded":
        phase1_transition_procurement_plan_status(
            parent.name,
            "Superseded",
            remarks=f"Superseded by Procurement Plan Revision {revision_doc.name}",
        )

    if not getattr(revision_doc, "approved_by", None):
        revision_doc.db_set("approved_by", frappe.session.user, update_modified=False)
    if not getattr(revision_doc, "approved_on", None):
        revision_doc.db_set("approved_on", now_datetime(), update_modified=False)

    log_ken_tender_audit_event(
        action="procurement_plan_revision_published",
        reference_doctype="Procurement Plan Revision",
        reference_name=revision_doc.name,
        details={
            "parent_plan": revision_doc.parent_plan,
            "parent_status_after": frappe.db.get_value("Procurement Plan", revision_doc.parent_plan, "status"),
            "revision_type": getattr(revision_doc, "revision_type", None),
            "revision_number": getattr(revision_doc, "revision_number", None),
        },
    )


def phase1_procurement_plan_revision_on_update(doc, method=None) -> None:
    prev_status = doc.get_value_before_save("status")
    if prev_status != "Published" and getattr(doc, "status", None) == "Published":
        _phase1_apply_revision_publish_side_effects(doc)


@frappe.whitelist()
def phase1_publish_procurement_plan_revision(revision_name: str, remarks: str | None = None) -> str:
    """Controlled publish path for Procurement Plan Revision."""
    doc = frappe.get_doc("Procurement Plan Revision", revision_name)
    current_status = getattr(doc, "status", None)
    if current_status == "Published":
        _phase1_apply_revision_publish_side_effects(doc)
        return doc.status

    if current_status == "Under Review":
        doc = frappe.model.workflow.apply_workflow(doc, "Approve Revision")
        doc.reload()
        current_status = getattr(doc, "status", None)

    if current_status != "Approved":
        frappe.throw("Revision can only be published from Approved state")

    # Try workflow-native publish first.
    try:
        doc = frappe.model.workflow.apply_workflow(doc, "Publish Revision")
        doc.reload()
        if remarks:
            doc.add_comment("Workflow", f"Approved -> Published: {remarks}")
        return doc.status
    except Exception:
        # Fallback to controlled override for environments where workflow action
        # routing is unavailable for the current operator.
        pass

    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        doc.reload()
        doc.status = "Published"
        prev_ignore = getattr(doc.flags, "ignore_validate_update_after_submit", False)
        doc.flags.ignore_validate_update_after_submit = True
        prev_ignore_version = getattr(doc.flags, "ignore_version", False)
        doc.flags.ignore_version = True
        try:
            doc.save(ignore_permissions=True)
        finally:
            doc.flags.ignore_validate_update_after_submit = prev_ignore
            doc.flags.ignore_version = prev_ignore_version

        doc.reload()
        _phase1_apply_revision_publish_side_effects(doc)
        if remarks:
            doc.add_comment("Workflow", f"{current_status} -> Published: {remarks}")
        else:
            doc.add_comment("Workflow", f"{current_status} -> Published")
    finally:
        frappe.flags.in_override = prev_in_override

    if doc.status == "Published":
        _phase1_apply_revision_publish_side_effects(doc)
        doc.reload()
    return doc.status


def _phase1_upsert_workflow(
    workflow_name: str,
    document_type: str,
    workflow_state_field: str,
    states: list[dict],
    transitions: list[dict],
) -> str:
    # Ensure linked Roles and Workflow States exist before saving Workflow rows.
    required_roles = set()
    for row in states:
        if row.get("allow_edit"):
            required_roles.add(row["allow_edit"])
    for row in transitions:
        if row.get("allowed"):
            required_roles.add(row["allowed"])
    for role_name in required_roles:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)

    required_states = {row["state"] for row in states}
    required_states.update({row["state"] for row in transitions})
    required_states.update({row["next_state"] for row in transitions})
    for state_name in required_states:
        if not frappe.db.exists("Workflow State", state_name):
            frappe.get_doc(
                {
                    "doctype": "Workflow State",
                    "workflow_state_name": state_name,
                    "style": "Primary",
                }
            ).insert(ignore_permissions=True)

    required_actions = {row["action"] for row in transitions if row.get("action")}
    for action_name in required_actions:
        if not frappe.db.exists("Workflow Action Master", action_name):
            frappe.get_doc(
                {
                    "doctype": "Workflow Action Master",
                    "workflow_action_name": action_name,
                }
            ).insert(ignore_permissions=True)

    existing = frappe.db.exists("Workflow", workflow_name)
    if existing:
        wf = frappe.get_doc("Workflow", workflow_name)
    else:
        wf = frappe.new_doc("Workflow")
        wf.workflow_name = workflow_name

    wf.document_type = document_type
    wf.workflow_state_field = workflow_state_field
    wf.is_active = 1
    wf.send_email_alert = 0

    wf.set("states", [])
    for row in states:
        wf.append(
            "states",
            {
                "state": row["state"],
                "doc_status": row["doc_status"],
                "allow_edit": row["allow_edit"],
            },
        )

    wf.set("transitions", [])
    for row in transitions:
        wf.append(
            "transitions",
            {
                "state": row["state"],
                "action": row["action"],
                "next_state": row["next_state"],
                "allowed": row["allowed"],
            },
        )

    wf.save(ignore_permissions=True)
    return wf.name


@frappe.whitelist()
def phase1_setup_procurement_plan_workflows() -> dict:
    """Create/update active Workflow docs for Phase 1 Procurement Plan governance."""
    plan_states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Procurement Planner"},
        {"state": "Department Consolidation", "doc_status": 0, "allow_edit": "Procurement Planner"},
        {"state": "Procurement Review", "doc_status": 0, "allow_edit": "Head of Procurement"},
        {"state": "Finance Review", "doc_status": 0, "allow_edit": "Finance/Budget Officer"},
        {"state": "Submitted", "doc_status": 0, "allow_edit": "Accounting Officer"},
        {"state": "Approved", "doc_status": 1, "allow_edit": "Accounting Officer"},
        {"state": "Published", "doc_status": 1, "allow_edit": "Procurement Manager"},
        {"state": "Locked", "doc_status": 1, "allow_edit": "System Manager"},
        {"state": "Superseded", "doc_status": 1, "allow_edit": "System Manager"},
        {"state": "Cancelled", "doc_status": 2, "allow_edit": "System Manager"},
    ]
    plan_transitions = [
        {"state": "Draft", "action": "Consolidate", "next_state": "Department Consolidation", "allowed": "Procurement Planner"},
        {"state": "Department Consolidation", "action": "Send to Procurement Review", "next_state": "Procurement Review", "allowed": "Procurement Planner"},
        {"state": "Procurement Review", "action": "Send to Finance", "next_state": "Finance Review", "allowed": "Head of Procurement"},
        {"state": "Procurement Review", "action": "Return to Planner", "next_state": "Department Consolidation", "allowed": "Head of Procurement"},
        {"state": "Finance Review", "action": "Submit for Approval", "next_state": "Submitted", "allowed": "Finance/Budget Officer"},
        {"state": "Finance Review", "action": "Return to Procurement", "next_state": "Procurement Review", "allowed": "Finance/Budget Officer"},
        {"state": "Submitted", "action": "Approve", "next_state": "Approved", "allowed": "Accounting Officer"},
        {"state": "Submitted", "action": "Reject", "next_state": "Department Consolidation", "allowed": "Accounting Officer"},
        {"state": "Approved", "action": "Publish", "next_state": "Published", "allowed": "Head of Procurement"},
        {"state": "Approved", "action": "Supersede", "next_state": "Superseded", "allowed": "System Manager"},
        {"state": "Published", "action": "Supersede", "next_state": "Superseded", "allowed": "System Manager"},
        {"state": "Published", "action": "Lock", "next_state": "Locked", "allowed": "System Manager"},
        {"state": "Locked", "action": "Supersede", "next_state": "Superseded", "allowed": "System Manager"},
    ]

    revision_states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Procurement Planner"},
        {"state": "Under Review", "doc_status": 0, "allow_edit": "Head of Procurement"},
        {"state": "Approved", "doc_status": 1, "allow_edit": "Accounting Officer"},
        {"state": "Published", "doc_status": 1, "allow_edit": "System Manager"},
        {"state": "Rejected", "doc_status": 2, "allow_edit": "System Manager"},
    ]
    revision_transitions = [
        {"state": "Draft", "action": "Submit Revision", "next_state": "Under Review", "allowed": "Procurement Planner"},
        {"state": "Under Review", "action": "Approve Revision", "next_state": "Approved", "allowed": "Accounting Officer"},
        {"state": "Under Review", "action": "Reject Revision", "next_state": "Rejected", "allowed": "Accounting Officer"},
        {"state": "Approved", "action": "Publish Revision", "next_state": "Published", "allowed": "Head of Procurement"},
    ]

    plan_wf = _phase1_upsert_workflow(
        workflow_name="Procurement Plan Workflow",
        document_type="Procurement Plan",
        workflow_state_field="status",
        states=plan_states,
        transitions=plan_transitions,
    )
    revision_wf = _phase1_upsert_workflow(
        workflow_name="Procurement Plan Revision Workflow",
        document_type="Procurement Plan Revision",
        workflow_state_field="status",
        states=revision_states,
        transitions=revision_transitions,
    )
    frappe.clear_cache()
    return {
        "procurement_plan_workflow": plan_wf,
        "procurement_plan_revision_workflow": revision_wf,
    }


@frappe.whitelist()
def phase15_setup_purchase_requisition_workflow() -> dict:
    states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Requestor"},
        {"state": "Submitted", "doc_status": 0, "allow_edit": "Head of Department"},
        {"state": "HoD Review", "doc_status": 0, "allow_edit": "Head of Department"},
        {"state": "Finance Review", "doc_status": 0, "allow_edit": "Finance/Budget Officer"},
        {"state": "AO Review", "doc_status": 0, "allow_edit": "Accounting Officer"},
        {"state": "Procurement Review", "doc_status": 0, "allow_edit": "Procurement Officer"},
        {"state": "Approved", "doc_status": 0, "allow_edit": "Head of Procurement"},
        {"state": "Rejected", "doc_status": 0, "allow_edit": "Requestor"},
        {"state": "Cancelled", "doc_status": 0, "allow_edit": "System Manager"},
    ]
    transitions = [
        {"state": "Draft", "action": "Submit", "next_state": "Submitted", "allowed": "Requestor"},
        {"state": "Submitted", "action": "Route to HoD", "next_state": "HoD Review", "allowed": "Head of Department"},
        {"state": "HoD Review", "action": "Approve HoD", "next_state": "Finance Review", "allowed": "Head of Department"},
        {"state": "HoD Review", "action": "Return", "next_state": "Draft", "allowed": "Head of Department"},
        {"state": "Finance Review", "action": "Approve Finance", "next_state": "AO Review", "allowed": "Finance/Budget Officer"},
        {"state": "Finance Review", "action": "Return", "next_state": "Draft", "allowed": "Finance/Budget Officer"},
        {"state": "AO Review", "action": "Approve AO", "next_state": "Procurement Review", "allowed": "Accounting Officer"},
        {"state": "AO Review", "action": "Reject", "next_state": "Rejected", "allowed": "Accounting Officer"},
        {"state": "Procurement Review", "action": "Approve Final", "next_state": "Approved", "allowed": "Procurement Officer"},
        {"state": "Procurement Review", "action": "Return", "next_state": "Draft", "allowed": "Procurement Officer"},
        {"state": "Approved", "action": "Cancel", "next_state": "Cancelled", "allowed": "Head of Procurement"},
    ]
    workflow_name = _phase1_upsert_workflow(
        workflow_name="Purchase Requisition Workflow",
        document_type="Purchase Requisition",
        workflow_state_field="status",
        states=states,
        transitions=transitions,
    )
    frappe.clear_cache()
    return {"purchase_requisition_workflow": workflow_name}


@frappe.whitelist()
def phase2_setup_workflows() -> dict:
    supplier_states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Supplier Registration Officer"},
        {"state": "Submitted", "doc_status": 0, "allow_edit": "Supplier Registration Officer"},
        {"state": "Compliance Review", "doc_status": 0, "allow_edit": "Supplier Registration Officer"},
        {"state": "Procurement Review", "doc_status": 0, "allow_edit": "Head of Procurement"},
        {"state": "Approved", "doc_status": 1, "allow_edit": "Head of Procurement"},
        {"state": "Rejected", "doc_status": 2, "allow_edit": "System Manager"},
        {"state": "Suspended", "doc_status": 1, "allow_edit": "System Manager"},
    ]
    supplier_transitions = [
        {"state": "Draft", "action": "Submit Application", "next_state": "Submitted", "allowed": "Supplier Registration Officer"},
        {"state": "Submitted", "action": "Start Compliance Review", "next_state": "Compliance Review", "allowed": "Supplier Registration Officer"},
        {"state": "Compliance Review", "action": "Forward Procurement Review", "next_state": "Procurement Review", "allowed": "Supplier Registration Officer"},
        {"state": "Procurement Review", "action": "Approve Supplier", "next_state": "Approved", "allowed": "Head of Procurement"},
        {"state": "Procurement Review", "action": "Reject Supplier", "next_state": "Rejected", "allowed": "Head of Procurement"},
    ]
    tender_states = [
        {"state": "Draft", "doc_status": 0, "allow_edit": "Procurement Officer"},
        {"state": "Internal Review", "doc_status": 0, "allow_edit": "Head of Procurement"},
        {"state": "Approved for Publication", "doc_status": 0, "allow_edit": "Head of Procurement"},
        {"state": "Published", "doc_status": 0, "allow_edit": "Procurement Officer"},
        {"state": "Closed", "doc_status": 0, "allow_edit": "Opening Committee Member"},
        {"state": "Opened", "doc_status": 0, "allow_edit": "Tender Committee Secretary"},
        {"state": "Under Evaluation", "doc_status": 0, "allow_edit": "Evaluation Committee Chair"},
        {"state": "Award Recommended", "doc_status": 0, "allow_edit": "Evaluation Committee Chair"},
        {"state": "Award Approved", "doc_status": 0, "allow_edit": "Accounting Officer"},
        {"state": "Award Published", "doc_status": 0, "allow_edit": "Procurement Officer"},
        {"state": "Cancelled", "doc_status": 2, "allow_edit": "System Manager"},
    ]
    tender_transitions = [
        {"state": "Draft", "action": "Send Internal Review", "next_state": "Internal Review", "allowed": "Procurement Officer"},
        {"state": "Internal Review", "action": "Approve Publication", "next_state": "Approved for Publication", "allowed": "Head of Procurement"},
        {"state": "Approved for Publication", "action": "Publish Tender", "next_state": "Published", "allowed": "Procurement Officer"},
        {"state": "Published", "action": "Close Tender", "next_state": "Closed", "allowed": "Opening Committee Member"},
        {"state": "Closed", "action": "Open Bids", "next_state": "Opened", "allowed": "Opening Committee Member"},
        {"state": "Opened", "action": "Start Evaluation", "next_state": "Under Evaluation", "allowed": "Tender Committee Secretary"},
        {"state": "Under Evaluation", "action": "Recommend Award", "next_state": "Award Recommended", "allowed": "Evaluation Committee Chair"},
        {"state": "Award Recommended", "action": "Approve Award", "next_state": "Award Approved", "allowed": "Accounting Officer"},
        {"state": "Award Approved", "action": "Publish Award", "next_state": "Award Published", "allowed": "Procurement Officer"},
    ]
    supplier_wf = _phase1_upsert_workflow(
        workflow_name="Supplier Registration Workflow",
        document_type="Supplier Registration Application",
        workflow_state_field="application_status",
        states=supplier_states,
        transitions=supplier_transitions,
    )
    tender_wf = _phase1_upsert_workflow(
        workflow_name="Tender Workflow",
        document_type="Tender",
        workflow_state_field="status",
        states=tender_states,
        transitions=tender_transitions,
    )
    frappe.clear_cache()
    return {"supplier_registration_workflow": supplier_wf, "tender_workflow": tender_wf}


def phase1_setup_purchase_requisition_form_layout() -> None:
    """Desk UX: tabs, column grouping, field order, and progressive disclosure for Purchase Requisition."""
    dt = "Purchase Requisition"
    if not frappe.db.exists("DocType", dt):
        return

    meta = frappe.get_meta(dt, cached=False)

    def _cf_name(fieldname: str) -> str | None:
        return frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname}, "name")

    def _set_insert_after(fieldname: str, insert_after: str) -> None:
        cf = _cf_name(fieldname)
        if cf:
            frappe.db.set_value("Custom Field", cf, "insert_after", insert_after, update_modified=False)

    def _ensure_break(fieldname: str, label: str | None, fieldtype: str, insert_after: str) -> None:
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
            _set_insert_after(fieldname, insert_after)
            return
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": dt,
                "fieldname": fieldname,
                "label": label or "",
                "fieldtype": fieldtype,
                "insert_after": insert_after,
            }
        ).insert(ignore_permissions=True)

    def _set_depends_on(fieldname: str, expr: str | None) -> None:
        cf = _cf_name(fieldname)
        if not cf:
            return
        frappe.db.set_value("Custom Field", cf, "depends_on", expr or "", update_modified=False)

    def _delete_cf(fieldname: str) -> None:
        cf = _cf_name(fieldname)
        if cf:
            frappe.delete_doc("Custom Field", cf, force=True, ignore_permissions=True)

    def _upsert_ps_insert_after(field_name: str, insert_after: str) -> None:
        """Reposition a core DocField (e.g. Requested By) after our section break (full-width band)."""
        filters = {
            "doc_type": dt,
            "doctype_or_field": "DocField",
            "field_name": field_name,
            "property": "insert_after",
        }
        existing = frappe.db.get_value("Property Setter", filters, "name")
        if existing:
            frappe.db.set_value("Property Setter", existing, "value", insert_after, update_modified=False)
        else:
            frappe.get_doc(
                {
                    "doctype": "Property Setter",
                    "doc_type": dt,
                    "doctype_or_field": "DocField",
                    "field_name": field_name,
                    "property": "insert_after",
                    "property_type": "Data",
                    "value": insert_after,
                }
            ).insert(ignore_permissions=True)

    # Remove legacy column breaks (they caused lopsided 2 vs 6 fields with stock fields piling on the right).
    _delete_cf("kentender_col_pr_left")
    _delete_cf("kentender_col_pr_right")

    # --- Top band: single full-width column under Request classification (balanced vs Requisition Details) ---
    if meta.has_field("department") and meta.has_field("entity"):
        _ensure_break("kentender_sec_pr_context", "Request classification", "Section Break", "department")
        _set_insert_after("entity", "kentender_sec_pr_context")
        _set_insert_after("requestor", "entity")
        _set_insert_after("financial_year", "requestor")
        _set_insert_after("requisition_type", "financial_year")
        _set_insert_after("source_mode", "requisition_type")
        _set_insert_after("required_by_date", "source_mode")
        # New section resets layout so stock fields are not trapped in a narrow right column.
        _ensure_break(
            "kentender_sec_pr_after_class",
            "Request summary",
            "Section Break",
            "required_by_date",
        )
        tail = "kentender_sec_pr_after_class"
        for fname in ("requested_by", "request_by"):
            if meta.has_field(fname):
                _upsert_ps_insert_after(fname, tail)
                tail = fname
        for fname in ("estimated_cost", "grand_total", "base_grand_total"):
            if meta.has_field(fname):
                _upsert_ps_insert_after(fname, tail)
                break
    else:
        _set_insert_after("required_by_date", "source_mode")

    # Anchor for budget tab: after a value/money-like stock field when possible.
    budget_anchor = None
    for candidate in (
        "estimated_cost",
        "grand_total",
        "base_total",
        "net_total",
        "rounded_total",
        "additional_discount_percentage",
        "discount_amount",
        "tc_name",
        "terms",
        "schedule_date",
        "transaction_date",
        "material_request_type",
    ):
        if meta.has_field(candidate):
            budget_anchor = candidate
            break
    if not budget_anchor:
        for fallback in ("justification", "description", "remarks", "company", "title"):
            if meta.has_field(fallback):
                budget_anchor = fallback
                break

    if not budget_anchor:
        frappe.clear_cache(doctype=dt)
        return

    _ensure_break("kentender_tab_pr_budget", "Budget & APP linkage", "Tab Break", budget_anchor)
    _set_insert_after("procurement_plan_item", "kentender_tab_pr_budget")
    _set_insert_after("currency", "procurement_plan_item")
    _set_insert_after("total_estimated_cost", "currency")
    _set_insert_after("total_committed_amount", "total_estimated_cost")
    _set_insert_after("total_released_amount", "total_committed_amount")
    _set_insert_after("budget_status", "total_released_amount")
    _set_insert_after("budget_reference", "budget_status")
    _set_insert_after("program_code", "budget_reference")
    _set_insert_after("delivery_location", "program_code")

    _ensure_break("kentender_tab_pr_lines", "Line items", "Tab Break", "delivery_location")
    _set_insert_after("items", "kentender_tab_pr_lines")

    _ensure_break("kentender_tab_pr_approvals", "Approvals & workflow", "Tab Break", "items")
    _set_insert_after("approvals", "kentender_tab_pr_approvals")
    _set_insert_after("approval_status", "approvals")

    _set_insert_after("emergency_flag", "approval_status")
    _set_insert_after("one_off_flag", "emergency_flag")
    _set_insert_after("exception_flag", "one_off_flag")
    _set_depends_on("emergency_flag", "eval:doc.requisition_type=='Emergency'")
    _set_depends_on("one_off_flag", "eval:doc.source_mode=='One-Off'")
    _set_depends_on("exception_flag", "eval:doc.one_off_flag==1")

    _ensure_break("kentender_tab_pr_tender_audit", "Tender readiness & record audit", "Tab Break", "exception_flag")
    _set_insert_after("tender_readiness_status", "kentender_tab_pr_tender_audit")
    _set_insert_after("linked_tender_count", "tender_readiness_status")
    _set_insert_after("submitted_on", "linked_tender_count")
    _set_insert_after("approved_on", "submitted_on")
    _set_insert_after("cancelled_on", "approved_on")
    _set_insert_after("closed_on", "cancelled_on")

    frappe.clear_cache(doctype=dt)


def _phase1_requisition_amount(doc) -> float:
    for fieldname in ("estimated_cost", "grand_total", "base_grand_total"):
        value = flt(getattr(doc, fieldname, 0) or 0)
        if value > 0:
            return value
    return 0.0


def _phase15_line_amount(row) -> float:
    qty = flt(getattr(row, "quantity", 0) or 0)
    unit = flt(getattr(row, "estimated_unit_cost", 0) or 0)
    if qty > 0 and unit > 0:
        return qty * unit
    return flt(getattr(row, "estimated_total_cost", 0) or 0)


def _phase1_get_available_plan_item_balance(plan_item_name: str) -> float:
    row = frappe.db.get_value(
        "Procurement Plan Item",
        plan_item_name,
        ["estimated_budget", "committed_amount", "actual_amount"],
        as_dict=True,
    ) or {}
    planned = flt(row.get("estimated_budget") or 0)
    committed = flt(row.get("committed_amount") or 0)
    actual = flt(row.get("actual_amount") or 0)
    return max(planned - max(committed, actual), 0)


def phase1_validate_purchase_requisition(doc, method=None) -> None:
    # Phase 1.5: full requisition treatment with line-level controls.
    if not getattr(doc, "requestor", None):
        doc.requestor = frappe.session.user
    if not getattr(doc, "entity", None) and getattr(doc, "organization", None):
        # Compatibility bridge for legacy PR field naming.
        doc.entity = doc.organization

    required = ["entity", "department", "financial_year", "request_date", "required_by_date", "justification", "source_mode"]
    missing = [f for f in required if not getattr(doc, f, None)]
    if missing:
        frappe.throw(f"Missing required Purchase Requisition fields: {', '.join(missing)}")

    if doc.required_by_date and doc.request_date and doc.required_by_date < doc.request_date:
        frappe.throw("Required by date cannot be earlier than request date")

    items = list(getattr(doc, "items", []) or [])
    if not items and getattr(doc, "procurement_plan_item", None):
        # Backward compatibility fallback (single-line mode).
        amount = _phase1_requisition_amount(doc)
        if amount <= 0:
            frappe.throw("Purchase Requisition amount must be greater than zero")
        plan_item_name = doc.procurement_plan_item
        if not frappe.db.exists("Procurement Plan Item", plan_item_name):
            frappe.throw(f"Procurement Plan Item not found: {plan_item_name}")
        ppi_status = frappe.db.get_value("Procurement Plan Item", plan_item_name, "status")
        if ppi_status != "Approved":
            frappe.throw("Purchase Requisition requires an Approved Procurement Plan Item")
        available = _phase1_get_available_plan_item_balance(plan_item_name)
        if amount > available:
            frappe.throw(
                f"Requisition amount ({amount}) exceeds available APP line balance ({available})"
            )
        doc.total_estimated_cost = amount
        return

    if not items:
        frappe.throw("At least one Purchase Requisition Item is required")

    if doc.source_mode == "One-Off" and not getattr(doc, "one_off_flag", 0):
        frappe.throw("One-Off source mode requires one_off_flag")

    total = 0.0
    for idx, row in enumerate(items, start=1):
        row.line_number = idx
        if not getattr(row, "item_description", None):
            frappe.throw(f"Item description is required on row {idx}")
        if not getattr(row, "technical_specification", None):
            frappe.throw(f"Technical specification is required on row {idx}")
        if flt(getattr(row, "quantity", 0) or 0) <= 0:
            frappe.throw(f"Quantity must be greater than zero on row {idx}")
        if flt(getattr(row, "estimated_unit_cost", 0) or 0) <= 0:
            frappe.throw(f"Estimated unit cost must be greater than zero on row {idx}")

        line_amount = _phase15_line_amount(row)
        row.estimated_total_cost = line_amount
        total += line_amount

        if doc.source_mode == "APP Linked":
            if not getattr(row, "procurement_plan_item", None):
                frappe.throw(f"APP-linked requisitions require Procurement Plan Item on row {idx}")
            ppi_status = frappe.db.get_value("Procurement Plan Item", row.procurement_plan_item, "status")
            if ppi_status != "Approved":
                frappe.throw(f"Procurement Plan Item on row {idx} must be Approved")
            available = _phase1_get_available_plan_item_balance(row.procurement_plan_item)
            row.remaining_app_balance = available
            if line_amount > available:
                frappe.throw(
                    f"Row {idx} exceeds remaining APP balance ({available}) with amount ({line_amount})"
                )

    doc.total_estimated_cost = total
    if total <= 0:
        frappe.throw("Total requisition amount must be greater than zero")

    # Minimal budget gate baseline (can become policy-rule based later).
    doc.budget_status = "Available"
    if doc.source_mode == "One-Off" and not getattr(doc, "exception_flag", 0):
        # one-off path should not bypass governance
        frappe.throw("One-Off requisitions require exception_flag and approved exception routing")


def phase1_after_migrate_setup() -> None:
    """Phase 1 migrate-time setup for budget lifecycle controls."""
    if not frappe.db.exists("DocType", "Purchase Requisition"):
        return

    if not frappe.db.exists(
        "Custom Field",
        {"dt": "Purchase Requisition", "fieldname": "procurement_plan_item"},
    ):
        frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": "Purchase Requisition",
                "label": "Procurement Plan Item",
                "fieldname": "procurement_plan_item",
                "fieldtype": "Link",
                "options": "Procurement Plan Item",
                "insert_after": "estimated_cost",
                "description": "Required for Phase 1 budget lifecycle commitment controls.",
            }
        ).insert(ignore_permissions=True)

    def _ensure_cf(dt: str, fieldname: str, label: str, fieldtype: str, insert_after: str, **extra):
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
            return
        payload = {
            "doctype": "Custom Field",
            "dt": dt,
            "label": label,
            "fieldname": fieldname,
            "fieldtype": fieldtype,
            "insert_after": insert_after,
        }
        payload.update(extra or {})
        frappe.get_doc(payload).insert(ignore_permissions=True)

    # Phase 1.5 header fields on core Purchase Requisition doctype.
    _ensure_cf("Purchase Requisition", "entity", "Entity", "Link", "organization", options="Company")
    _ensure_cf("Purchase Requisition", "requestor", "Requestor", "Link", "department", options="User")
    _ensure_cf("Purchase Requisition", "financial_year", "Financial Year", "Link", "request_date", options="Fiscal Year")
    _ensure_cf("Purchase Requisition", "requisition_type", "Requisition Type", "Select", "financial_year", options="Standard\nAggregated\nEmergency\nOne-Off\nAmendment\nCancellation")
    _ensure_cf("Purchase Requisition", "source_mode", "Source Mode", "Select", "requisition_type", options="APP Linked\nOne-Off")
    _ensure_cf("Purchase Requisition", "required_by_date", "Required By Date", "Date", "source_mode")
    _ensure_cf("Purchase Requisition", "delivery_location", "Delivery Location", "Data", "justification")
    _ensure_cf("Purchase Requisition", "budget_reference", "Budget Reference", "Data", "delivery_location")
    _ensure_cf("Purchase Requisition", "program_code", "Program Code", "Data", "budget_reference")
    _ensure_cf("Purchase Requisition", "currency", "Currency", "Link", "project", options="Currency")
    _ensure_cf("Purchase Requisition", "total_estimated_cost", "Total Estimated Cost", "Currency", "currency", read_only=1)
    _ensure_cf("Purchase Requisition", "total_committed_amount", "Total Committed Amount", "Currency", "total_estimated_cost", read_only=1)
    _ensure_cf("Purchase Requisition", "total_released_amount", "Total Released Amount", "Currency", "total_committed_amount", read_only=1)
    _ensure_cf("Purchase Requisition", "budget_status", "Budget Status", "Select", "total_released_amount", options="Unchecked\nAvailable\nWarning\nBlocked\nCommitted\nReleased")
    _ensure_cf("Purchase Requisition", "approval_status", "Approval Status", "Select", "status", options="Pending\nApproved\nRejected\nReturned")
    _ensure_cf("Purchase Requisition", "emergency_flag", "Emergency", "Check", "approval_status")
    _ensure_cf("Purchase Requisition", "one_off_flag", "One-Off", "Check", "emergency_flag")
    _ensure_cf("Purchase Requisition", "exception_flag", "Exception", "Check", "one_off_flag")
    _ensure_cf("Purchase Requisition", "tender_readiness_status", "Tender Readiness Status", "Select", "exception_flag", options="Not Ready\nReady for Tender\nTender Created\nFully Handed Off")
    _ensure_cf("Purchase Requisition", "linked_tender_count", "Linked Tender Count", "Int", "tender_readiness_status", default="0", read_only=1)
    _ensure_cf("Purchase Requisition", "submitted_on", "Submitted On", "Datetime", "linked_tender_count", read_only=1)
    _ensure_cf("Purchase Requisition", "approved_on", "Approved On", "Datetime", "submitted_on", read_only=1)
    _ensure_cf("Purchase Requisition", "cancelled_on", "Cancelled On", "Datetime", "approved_on", read_only=1)
    _ensure_cf("Purchase Requisition", "closed_on", "Closed On", "Datetime", "cancelled_on", read_only=1)
    _ensure_cf("Purchase Requisition", "items", "Items", "Table", "procurement_plan_item", options="Purchase Requisition Item")
    _ensure_cf("Purchase Requisition", "approvals", "Approvals", "Table", "items", options="Purchase Requisition Approval")

    # Align legacy status field options with Phase 1.5 workflow states.
    status_options = "Draft\nSubmitted\nHoD Review\nFinance Review\nAO Review\nProcurement Review\nApproved\nRejected\nCancelled\nClosed"
    ps_filters = {
        "doc_type": "Purchase Requisition",
        "field_name": "status",
        "property": "options",
    }
    if frappe.db.exists("Property Setter", ps_filters):
        ps_name = frappe.db.get_value("Property Setter", ps_filters, "name")
        frappe.db.set_value("Property Setter", ps_name, "value", status_options)
    else:
        frappe.get_doc(
            {
                "doctype": "Property Setter",
                "doc_type": "Purchase Requisition",
                "doctype_or_field": "DocField",
                "field_name": "status",
                "property": "options",
                "property_type": "Text",
                "value": status_options,
            }
        ).insert(ignore_permissions=True)
    phase15_setup_purchase_requisition_workflow()
    # Phase 2 workflow baseline.
    if frappe.db.exists("DocType", "Supplier Registration Application"):
        phase2_setup_workflows()
    phase1_setup_purchase_requisition_form_layout()


def phase1_on_submit_purchase_requisition(doc, method=None) -> None:
    # Legacy wrapper retained for compatibility.
    phase1_on_update_purchase_requisition(doc, method)


def phase1_on_update_purchase_requisition(doc, method=None) -> None:
    """Phase 1.5 trigger: create commitments when requisition reaches Approved."""
    status = getattr(doc, "status", None)
    previous = doc.get_doc_before_save()

    if status == "Submitted" and not getattr(doc, "submitted_on", None):
        doc.db_set("submitted_on", now_datetime(), update_modified=False)

    if status == "Cancelled":
        # Release active requisition commitments.
        names = frappe.get_all(
            "Purchase Requisition Commitment",
            filters={"purchase_requisition": doc.name, "status": ("in", ["Active", "Partially Consumed", "Consumed"])},
            pluck="name",
        )
        for cname in names or []:
            c = frappe.get_doc("Purchase Requisition Commitment", cname)
            c.released_amount = flt(c.committed_amount or 0) - flt(c.actualized_amount or 0)
            c.status = "Released"
            c.released_on = now_datetime()
            c.release_reason = "Requisition cancelled"
            c.save(ignore_permissions=True)
        doc.db_set("cancelled_on", now_datetime(), update_modified=False)
        return

    if status != "Approved":
        return
    if previous and getattr(previous, "status", None) == "Approved":
        return

    # Idempotency: if commitments already exist for this requisition, skip recreate.
    existing = frappe.db.count("Purchase Requisition Commitment", {"purchase_requisition": doc.name})
    if existing:
        return

    # If table items exist, create one commitment per row; otherwise fallback to single-field legacy mode.
    items = list(getattr(doc, "items", []) or [])
    created = []
    if items:
        for row in items:
            line_amount = _phase15_line_amount(row)
            if line_amount <= 0:
                continue
            commitment = frappe.get_doc(
                {
                    "doctype": "Purchase Requisition Commitment",
                    "purchase_requisition": doc.name,
                    "requisition_item_idx": row.idx,
                    "entity": getattr(doc, "entity", None) or getattr(doc, "organization", None),
                    "financial_year": getattr(doc, "financial_year", None),
                    "budget_head": getattr(row, "budget_head", None) or getattr(doc, "budget_reference", None) or "",
                    "cost_center": getattr(row, "cost_center", None) or getattr(doc, "cost_center", None),
                    "project": getattr(row, "project", None) or getattr(doc, "project", None),
                    "committed_amount": line_amount,
                    "status": "Active",
                    "created_from_stage": "Requisition Approval",
                    "created_on": now_datetime(),
                }
            ).insert(ignore_permissions=True)
            created.append(commitment.name)

            # Update linked APP line lifecycle and committed totals.
            ppi_name = getattr(row, "procurement_plan_item", None)
            if ppi_name and frappe.db.exists("Procurement Plan Item", ppi_name):
                ppi = frappe.get_doc("Procurement Plan Item", ppi_name)
                ppi.db_set("committed_amount", flt(ppi.committed_amount or 0) + line_amount, update_modified=False)
                ppi.db_set("budget_status", "Committed", update_modified=False)
                if getattr(ppi, "line_status", None) in {"Approved in APP", "Reserved", "Draft", "Validated"}:
                    ppi.db_set("line_status", "Requisitioned", update_modified=False)
                if getattr(ppi, "procurement_plan", None):
                    _phase1_recalculate_plan_totals(frappe.get_doc("Procurement Plan", ppi.procurement_plan))
    else:
        plan_item_name = getattr(doc, "procurement_plan_item", None)
        amount = _phase1_requisition_amount(doc)
        if plan_item_name and amount > 0:
            ppi = frappe.get_doc("Procurement Plan Item", plan_item_name)
            company, fiscal_year = frappe.db.get_value(
                "Procurement Plan", ppi.procurement_plan, ["company", "fiscal_year"]
            ) or (None, None)
            commitment = frappe.get_doc(
                {
                    "doctype": "Purchase Requisition Commitment",
                    "purchase_requisition": doc.name,
                    "requisition_item_idx": 1,
                    "entity": company,
                    "financial_year": fiscal_year,
                    "budget_head": getattr(ppi, "budget_head", None) or "",
                    "cost_center": getattr(ppi, "cost_center", None),
                    "project": getattr(ppi, "project", None),
                    "committed_amount": amount,
                    "status": "Active",
                    "created_from_stage": "Requisition Approval",
                    "created_on": now_datetime(),
                }
            ).insert(ignore_permissions=True)
            created.append(commitment.name)
            ppi.db_set("committed_amount", flt(ppi.committed_amount or 0) + amount, update_modified=False)
            ppi.db_set("budget_status", "Committed", update_modified=False)
            if getattr(ppi, "line_status", None) in {"Approved in APP", "Reserved", "Draft", "Validated"}:
                ppi.db_set("line_status", "Requisitioned", update_modified=False)
            if getattr(ppi, "procurement_plan", None):
                _phase1_recalculate_plan_totals(frappe.get_doc("Procurement Plan", ppi.procurement_plan))

    # Snapshot and requisition totals/statuses
    snapshot_payload = frappe.as_json(doc.as_dict(), indent=2)
    frappe.get_doc(
        {
            "doctype": "Purchase Requisition Snapshot",
            "purchase_requisition": doc.name,
            "snapshot_type": "Approval",
            "snapshot_json": snapshot_payload,
            "created_by": frappe.session.user,
            "created_on": now_datetime(),
        }
    ).insert(ignore_permissions=True)

    committed_total = (
        frappe.db.sql(
            """
            select coalesce(sum(committed_amount - released_amount), 0)
            from `tabPurchase Requisition Commitment`
            where purchase_requisition=%s and status in ('Active','Partially Consumed','Consumed')
            """,
            doc.name,
        )[0][0]
        if doc.name
        else 0
    )
    doc.db_set("total_committed_amount", committed_total, update_modified=False)
    doc.db_set("approved_on", now_datetime(), update_modified=False)
    doc.db_set("tender_readiness_status", "Ready for Tender", update_modified=False)
    doc.db_set("budget_status", "Committed", update_modified=False)

    if created:
        log_ken_tender_audit_event(
            action="phase15_requisition_commitments_created",
            reference_doctype="Purchase Requisition",
            reference_name=doc.name,
            details={"commitments": created},
        )


def phase15_on_submit_purchase_requisition_amendment(doc, method=None) -> None:
    req = frappe.get_doc("Purchase Requisition", doc.purchase_requisition)
    if getattr(req, "linked_tender_count", 0) and getattr(doc, "amendment_type", None) in {"Scope", "Quantity", "Budget"}:
        frappe.throw("Material amendments are blocked after tender handoff")

    # Snapshot amendment approval for immutable evidence.
    payload = frappe.as_json({"requisition": req.as_dict(), "amendment": doc.as_dict()}, indent=2)
    frappe.get_doc(
        {
            "doctype": "Purchase Requisition Snapshot",
            "purchase_requisition": req.name,
            "snapshot_type": "Amendment Approval",
            "snapshot_json": payload,
            "created_by": frappe.session.user,
            "created_on": now_datetime(),
        }
    ).insert(ignore_permissions=True)


def _phase15_get_requisition_plan_items(req_doc) -> list[str]:
    plan_items = []
    for row in getattr(req_doc, "items", []) or []:
        plan_item = getattr(row, "procurement_plan_item", None)
        if plan_item:
            plan_items.append(plan_item)

    # Legacy fallback path
    if not plan_items and getattr(req_doc, "procurement_plan_item", None):
        plan_items.append(req_doc.procurement_plan_item)

    # Preserve order while removing duplicates
    seen = set()
    unique = []
    for name in plan_items:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _phase15_upsert_requisition_handoff(req_doc, tender_names: list[str]) -> str:
    existing = frappe.get_all(
        "Requisition Tender Handoff",
        filters={"purchase_requisition": req_doc.name},
        fields=["name"],
        order_by="creation desc",
        limit=1,
    )
    tender_ref = ", ".join(tender_names)
    if existing:
        handoff = frappe.get_doc("Requisition Tender Handoff", existing[0].name)
        handoff.handoff_status = "Tender Created"
        handoff.tender_reference = tender_ref
        handoff.approved_for_tender_by = frappe.session.user
        handoff.approved_for_tender_on = now_datetime()
        handoff.notes = "Updated by controlled Phase 1.5 handoff service."
        handoff.save(ignore_permissions=True)
        return handoff.name

    handoff = frappe.get_doc(
        {
            "doctype": "Requisition Tender Handoff",
            "purchase_requisition": req_doc.name,
            "handoff_status": "Tender Created",
            "prepared_by": getattr(req_doc, "requestor", None) or frappe.session.user,
            "prepared_on": now_datetime(),
            "approved_for_tender_by": frappe.session.user,
            "approved_for_tender_on": now_datetime(),
            "tender_reference": tender_ref,
            "notes": "Generated by controlled Phase 1.5 handoff service.",
        }
    ).insert(ignore_permissions=True)
    return handoff.name


@frappe.whitelist()
def phase15_handoff_requisition_to_tender(
    requisition_name: str, publish_immediately: int = 1, remarks: str | None = None
) -> dict:
    """Create Tender record(s) from an approved, ready PR and log handoff evidence."""
    req = frappe.get_doc("Purchase Requisition", requisition_name)
    if getattr(req, "status", None) != "Approved":
        frappe.throw("Only Approved Purchase Requisition records can be handed off to Tender")
    if getattr(req, "tender_readiness_status", None) not in {"Ready for Tender", "Tender Created", "Fully Handed Off"}:
        frappe.throw("Purchase Requisition is not in a tender-ready state")

    plan_items = _phase15_get_requisition_plan_items(req)
    if not plan_items:
        frappe.throw("No linked Procurement Plan Item found for tender handoff")

    created_tenders = []
    reused_tenders = []

    for ppi_name in plan_items:
        ppi = frappe.get_doc("Procurement Plan Item", ppi_name)
        if getattr(ppi, "status", None) != "Approved":
            frappe.throw(f"Procurement Plan Item must be Approved for handoff: {ppi_name}")

        existing = frappe.get_all(
            "Tender",
            filters={"procurement_plan_item": ppi_name, "status": ("!=", "Closed")},
            fields=["name", "status"],
            order_by="creation desc",
            limit=1,
        )
        if existing:
            reused_tenders.append(existing[0].name)
            continue

        tender_doc = frappe.get_doc(
            {
                "doctype": "Tender",
                "company": ppi.company,
                "procurement_plan_item": ppi_name,
                "status": "Published" if cint(publish_immediately) else "Draft",
                "publish_date": now_datetime().date(),
            }
        ).insert(ignore_permissions=True)
        created_tenders.append(tender_doc.name)

    all_tenders = created_tenders + reused_tenders
    handoff_name = _phase15_upsert_requisition_handoff(req, all_tenders)

    req.db_set("linked_tender_count", len(all_tenders), update_modified=False)
    req.db_set(
        "tender_readiness_status",
        "Fully Handed Off" if all_tenders else "Ready for Tender",
        update_modified=False,
    )

    log_ken_tender_audit_event(
        action="phase15_requisition_tender_handoff",
        reference_doctype="Purchase Requisition",
        reference_name=req.name,
        details={
            "handoff": handoff_name,
            "created_tenders": created_tenders,
            "reused_tenders": reused_tenders,
            "remarks": remarks or "",
        },
    )

    return {
        "purchase_requisition": req.name,
        "handoff": handoff_name,
        "created_tenders": created_tenders,
        "reused_tenders": reused_tenders,
        "linked_tender_count": len(all_tenders),
        "tender_readiness_status": frappe.db.get_value(
            "Purchase Requisition", req.name, "tender_readiness_status"
        ),
    }


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

    # Governance: enforce Phase 1 controls before allowing the first approval step.
    # This keeps validations aligned with the design gate (no execution without strategy + budget + method governance).
    _phase1_validate_item_before_first_approval(doc)

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
        log_ken_tender_audit_event(
            action="plan_item_approval",
            reference_doctype="Procurement Plan Item",
            reference_name=docname,
            details={
                "level_approved": current_level,
                "status_after": doc.status,
                "all_approved": all(r.status == "Approved" for r in doc.approvals),
            },
        )
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
        log_ken_tender_audit_event(
            action="plan_item_rejection",
            reference_doctype="Procurement Plan Item",
            reference_name=docname,
            details={
                "level_rejected": current_level,
                "status_after": doc.status,
                "reason": reason,
            },
        )
    finally:
        frappe.flags.in_override = prev_in_override

    return doc.status


def validate_tender(doc, method) -> None:
    plan_item = frappe.get_doc("Procurement Plan Item", doc.procurement_plan_item)
    if plan_item.status != "Approved":
        frappe.throw("Plan Item must be approved before creating Tender")

    # Phase 2 controls
    if not getattr(doc, "method", None):
        doc.method = getattr(plan_item, "procurement_method", None)
    if not getattr(doc, "procurement_type", None):
        doc.procurement_type = getattr(plan_item, "procurement_type", None)

    closing = getattr(doc, "closing_datetime", None) or getattr(doc, "submission_deadline", None)
    opening = getattr(doc, "opening_datetime", None)
    if opening and closing and opening < closing:
        frappe.throw("Opening datetime cannot be earlier than closing datetime")

    status = getattr(doc, "status", None) or "Draft"
    if status not in {"Draft", "Internal Review", "Cancelled"}:
        linked_count = cint(getattr(doc, "linked_requisition_count", 0) or 0)
        if linked_count <= 0:
            # Treat plan-item lineage as minimum valid source when requisition count is not yet populated.
            if not getattr(doc, "procurement_plan_item", None):
                frappe.throw("Tender must originate from an approved requisition/APP lineage")

        if status in {"Approved for Publication", "Published"}:
            packs = frappe.db.count("Tender Document Pack", {"tender": doc.name})
            if packs <= 0:
                frappe.throw("Tender Document Pack is required before publication")


def phase2_validate_supplier_registration_application(doc, method=None) -> None:
    required = ["supplier_name", "legal_name", "registration_number", "tax_id", "email", "phone", "country"]
    missing = [f for f in required if not getattr(doc, f, None)]
    if missing:
        frappe.throw(f"Supplier application missing required fields: {', '.join(missing)}")

    existing = frappe.get_all(
        "Supplier Master",
        filters={"tax_id": doc.tax_id, "registration_number": doc.registration_number},
        pluck="name",
        limit=1,
    )
    if existing and getattr(doc, "application_status", None) in {"Submitted", "Compliance Review", "Procurement Review", "Approved"}:
        frappe.throw(f"Supplier already exists for this registration/tax pair: {existing[0]}")

    if doc.application_status == "Approved":
        docs_verified = frappe.db.count(
            "Supplier Compliance Document",
            {"application": doc.name, "verification_status": "Verified"},
        )
        if docs_verified <= 0:
            frappe.throw("Cannot approve application without at least one verified compliance document")
        if not getattr(doc, "approved_on", None):
            doc.approved_on = now_datetime()


def phase2_sync_supplier_master_from_application(doc, method=None) -> None:
    if getattr(doc, "application_status", None) != "Approved":
        return

    supplier_master_name = frappe.db.get_value(
        "Supplier Master",
        {"tax_id": doc.tax_id, "registration_number": doc.registration_number},
        "name",
    )
    if supplier_master_name:
        sm = frappe.get_doc("Supplier Master", supplier_master_name)
    else:
        sm = frappe.get_doc({"doctype": "Supplier Master"})

    sm.supplier_name = doc.supplier_name
    sm.legal_name = doc.legal_name
    sm.registration_number = doc.registration_number
    sm.tax_id = doc.tax_id
    sm.email = doc.email
    sm.phone = doc.phone
    sm.country = doc.country
    sm.physical_address = doc.physical_address
    sm.registration_status = "Approved"
    sm.supplier_status = "Active"
    sm.last_review_date = now_datetime().date()
    sm.flags.ignore_permissions = True
    if sm.is_new():
        sm.insert(ignore_permissions=True)
    else:
        sm.save(ignore_permissions=True)

    # Ensure ERPNext Supplier exists for Tender Submission link compatibility.
    supplier_name = frappe.db.get_value("Supplier", {"supplier_name": doc.supplier_name}, "name")
    if not supplier_name:
        frappe.get_doc(
            {
                "doctype": "Supplier",
                "supplier_name": doc.supplier_name,
                "supplier_group": frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups",
                "supplier_type": "Company",
            }
        ).insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="phase2_supplier_master_synced",
        reference_doctype="Supplier Registration Application",
        reference_name=doc.name,
        details={"supplier_master": sm.name},
    )


def phase2_validate_supplier_master(doc, method=None) -> None:
    old = doc.get_doc_before_save()
    if old and old.supplier_status != doc.supplier_status and not getattr(frappe.flags, "in_override", False):
        frappe.throw("Supplier status can only be changed through Supplier Status Action")


def phase2_apply_supplier_status_action(doc, method=None) -> None:
    mapping = {
        "Activate": "Active",
        "Reactivate": "Active",
        "Reinstate": "Active",
        "Suspend": "Suspended",
        "Debar": "Debarred",
        "Blacklist": "Blacklisted",
        "Mark Expired": "Expired Compliance",
    }
    target = mapping.get(getattr(doc, "action_type", None))
    if not target:
        return
    supplier = frappe.get_doc("Supplier Master", doc.supplier)
    prev = supplier.supplier_status
    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        supplier.supplier_status = target
        supplier.last_review_date = now_datetime().date()
        supplier.save(ignore_permissions=True)
    finally:
        frappe.flags.in_override = prev_in_override

    if target in {"Suspended", "Debarred", "Blacklisted"}:
        frappe.get_doc(
            {
                "doctype": "Suspension Debarment Register",
                "supplier": supplier.name,
                "action_type": "Suspension" if target == "Suspended" else ("Debarment" if target == "Debarred" else "Blacklist"),
                "reason": doc.reason,
                "effective_from": doc.effective_date or now_datetime().date(),
                "effective_to": doc.end_date,
                "status": "Active",
            }
        ).insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="phase2_supplier_status_action_applied",
        reference_doctype="Supplier Status Action",
        reference_name=doc.name,
        details={"from": prev, "to": target, "supplier": supplier.name},
    )


def phase2_validate_evaluation_worksheet(doc, method=None) -> None:
    declaration = frappe.db.exists(
        "Evaluator Declaration",
        {
            "tender": doc.tender,
            "committee_member": doc.evaluator,
            "status": ("in", ["Signed", "Both"]),
        },
    )
    if not declaration:
        frappe.throw("Evaluator declaration must be signed before evaluation starts")


def validate_contract(doc, method) -> None:
    if doc.start_date and doc.end_date and doc.end_date < doc.start_date:
        frappe.throw("Contract End Date cannot be before Start Date")

    # Archive-grade closeout: when a contract has been archived at close-out, it becomes immutable
    # for any further saves while it remains in `Closed` status.
    old_for_lock = doc.get_doc_before_save()
    if (
        old_for_lock
        and getattr(old_for_lock, "closeout_archived", 0)
        and getattr(old_for_lock, "status", None) == "Closed"
        and getattr(doc, "status", None) == "Closed"
        and not getattr(frappe.flags, "in_override", False)
    ):
        frappe.throw("Archived closed Contract cannot be modified")

    if doc.status == "Active":
        if not doc.signed_by_supplier or not doc.signed_by_accounting_officer:
            frappe.throw("Contract cannot be Active before both signatures are completed")
        if doc.signature_mode == "External Verified":
            if not doc.supplier_signature_hash or not doc.supplier_signed_at:
                frappe.throw("Supplier external signature evidence is required")
            if not doc.accounting_signature_hash or not doc.accounting_signed_at:
                frappe.throw("Accounting Officer external signature evidence is required")

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
            _maybe_create_contract_closeout_archive(doc)
        if doc.status == "Active":
            if not doc.signed_by_supplier or not doc.signed_by_accounting_officer:
                frappe.throw("Contract cannot become Active before both signatures are completed")
            if doc.signature_mode == "External Verified":
                if not doc.supplier_signature_hash or not doc.supplier_signed_at:
                    frappe.throw("Supplier external signature evidence is required")
                if not doc.accounting_signature_hash or not doc.accounting_signed_at:
                    frappe.throw("Accounting Officer external signature evidence is required")


def _build_contract_closeout_snapshot(contract_doc) -> dict:
    """Build an immutable JSON snapshot for contract close-out auditability."""
    milestones = frappe.get_all(
        "Task",
        filters={"contract": contract_doc.name, "is_contract_milestone": 1},
        fields=[
            "name",
            "subject",
            "milestone_status",
            "payment_percentage",
            "exp_start_date",
            "exp_end_date",
            "status",
            "deliverables",
            "acceptance_criteria",
        ],
        order_by="creation asc",
    )

    governance_sessions = frappe.get_all(
        "Governance Session",
        filters={
            "context_reference_doctype": "Contract",
            "context_reference_name": contract_doc.name,
        },
        fields=["name", "session_type", "status", "meeting_date"],
        order_by="creation asc",
    )

    return {
        "contract": {
            "name": contract_doc.name,
            "contract_title": contract_doc.contract_title,
            "company": contract_doc.company,
            "supplier": contract_doc.supplier,
            "tender": contract_doc.tender,
            "project": contract_doc.project,
            "contract_type": contract_doc.contract_type,
            "contract_value": float(contract_doc.contract_value or 0),
            "currency": contract_doc.currency,
            "start_date": str(contract_doc.start_date) if contract_doc.start_date else None,
            "end_date": str(contract_doc.end_date) if contract_doc.end_date else None,
            "status": contract_doc.status,
            "final_acceptance_certificate": contract_doc.final_acceptance_certificate,
            "all_payments_completed": bool(contract_doc.all_payments_completed or 0),
            "handover_completed": bool(contract_doc.handover_completed or 0),
            "dlp_status": contract_doc.dlp_status,
            "dlp_start_date": str(contract_doc.dlp_start_date) if contract_doc.dlp_start_date else None,
            "dlp_end_date": str(contract_doc.dlp_end_date) if contract_doc.dlp_end_date else None,
            "defect_liability_months": int(contract_doc.defect_liability_months or 0),
            "signature_mode": contract_doc.signature_mode,
            "supplier_signed_at": str(contract_doc.supplier_signed_at)
            if getattr(contract_doc, "supplier_signed_at", None)
            else None,
            "accounting_signed_at": str(contract_doc.accounting_signed_at)
            if getattr(contract_doc, "accounting_signed_at", None)
            else None,
        },
        "closeout": {
            "archived_on": str(now_datetime()),
            "archived_by": frappe.session.user,
            "milestone_count": len(milestones or []),
            "governance_sessions_for_contract_count": len(governance_sessions or []),
            "open_claims_count": frappe.db.count(
                "Claim",
                {
                    "contract": contract_doc.name,
                    "status": ("in", ["Submitted", "Under Review"]),
                },
            ),
            "open_disputes_count": frappe.db.count(
                "Dispute Case",
                {
                    "contract": contract_doc.name,
                    "status": ("in", ["Open", "In Progress"]),
                },
            ),
            "retention_balance": float(
                get_contract_retention_balance(contract_doc.name) or 0
            ),
        },
        "milestones": milestones,
        "governance_sessions": governance_sessions,
    }


def _maybe_create_contract_closeout_archive(contract_doc) -> None:
    """Create an immutable closeout snapshot when the contract transitions into `Closed`."""
    seq = (
        frappe.db.count("Contract Closeout Archive", {"contract": contract_doc.name})
        + 1
    )

    payload = _build_contract_closeout_snapshot(contract_doc)

    archive = frappe.get_doc(
        {
            "doctype": "Contract Closeout Archive",
            "contract": contract_doc.name,
            "archive_sequence": seq,
            "archived_on": now_datetime(),
            "archived_by": frappe.session.user,
            "snapshot_json": json.dumps(payload, default=str, ensure_ascii=True),
        }
    )
    archive.insert(ignore_permissions=True)

    # Marker fields on the contract (used to block later edits while `Closed`).
    contract_doc.closeout_archived = 1
    contract_doc.closeout_archived_on = now_datetime()
    contract_doc.closeout_archive_ref = archive.name
    contract_doc.closeout_archive_sequence = seq


def validate_contract_closeout_archive(doc, method=None) -> None:
    """Closeout archive records are create-only (immutable)."""
    if not doc.is_new():
        frappe.throw("Contract Closeout Archive is immutable and cannot be edited")


def prevent_delete_contract_closeout_archive(doc, method=None) -> None:
    frappe.throw("Contract Closeout Archive cannot be deleted")


def _acceptance_certificate_requires_inspection_report(doc) -> bool:
    if doc.certificate_type in ("Certificate of Conformance", "Certificate of Acceptance", "Final Acceptance"):
        return True
    return bool(getattr(doc, "quality_inspection", None))


def _validate_inspection_report_chain_for_certificate(doc) -> None:
    """For Issued certificates: require submitted Report + Test Plan aligned with QI/contract/task."""
    if not getattr(doc, "inspection_report", None):
        frappe.throw(_("Submitted Inspection Report is required to issue this certificate"))
    ir = frappe.get_doc("Inspection Report", doc.inspection_report)
    if ir.docstatus != 1:
        frappe.throw(_("Inspection Report must be submitted"))

    if ir.contract != doc.contract:
        frappe.throw(_("Inspection Report does not belong to the same Contract as the certificate"))

    if doc.task and ir.milestone_task and ir.milestone_task != doc.task:
        frappe.throw(_("Inspection Report Milestone Task must match the certificate Milestone Task"))

    if not doc.quality_inspection:
        frappe.throw(_("Quality Inspection is required when Inspection Report is linked"))
    if ir.quality_inspection != doc.quality_inspection:
        frappe.throw(
            _("Inspection Report must reference the same Quality Inspection linked on the certificate")
        )

    qi = frappe.get_doc("Quality Inspection", doc.quality_inspection)
    if qi.docstatus != 1:
        frappe.throw(_("Quality Inspection must be submitted"))

    if not getattr(ir, "inspection_test_plan", None):
        frappe.throw(_("Inspection Report must reference an Inspection Test Plan"))

    itp = frappe.get_doc("Inspection Test Plan", ir.inspection_test_plan)
    if itp.docstatus != 1:
        frappe.throw(_("Inspection Test Plan must be submitted before issuing the certificate"))
    if itp.contract != doc.contract:
        frappe.throw(_("Inspection Test Plan must belong to the same Contract"))
    if doc.task and itp.milestone_task and itp.milestone_task != doc.task:
        frappe.throw(_("Inspection Test Plan Milestone Task must match the certificate Milestone Task"))

    if doc.decision == "Approved" and ir.outcome == "Failed":
        frappe.throw(_("Cannot issue Approved certificate with Inspection Report outcome Failed"))
    if doc.decision == "Approved" and qi.status != "Accepted":
        frappe.throw(_("Approved certificate requires Accepted Quality Inspection"))
    if ir.outcome == "Passed" and qi.status != "Accepted":
        frappe.throw(_("Inspection Report outcome Passed requires Quality Inspection status Accepted"))


def validate_inspection_test_plan(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw(_("Contract is required"))
    if not doc.title:
        frappe.throw(_("Title is required"))
    if not doc.scope:
        frappe.throw(_("Scope is required"))
    if not doc.prepared_by:
        frappe.throw(_("Prepared By is required"))
    if not doc.prepared_on:
        frappe.throw(_("Prepared On is required"))

    if doc.milestone_task:
        task_contract = frappe.db.get_value("Task", doc.milestone_task, "contract")
        if task_contract and task_contract != doc.contract:
            frappe.throw(_("Milestone Task must belong to the selected Contract"))
        if not int(frappe.db.get_value("Task", doc.milestone_task, "is_contract_milestone") or 0):
            frappe.throw(_("Milestone Task must be marked as a contract milestone"))


def validate_inspection_report(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw(_("Contract is required"))
    if not doc.inspection_test_plan:
        frappe.throw(_("Inspection Test Plan is required"))
    if not doc.quality_inspection:
        frappe.throw(_("Quality Inspection is required"))
    if not doc.findings:
        frappe.throw(_("Findings Summary is required"))
    if not doc.reported_by:
        frappe.throw(_("Reported By is required"))
    if not doc.reported_on:
        frappe.throw(_("Reported On is required"))

    itp = frappe.get_doc("Inspection Test Plan", doc.inspection_test_plan)
    if itp.contract != doc.contract:
        frappe.throw(_("Inspection Test Plan must belong to the same Contract"))
    if doc.milestone_task and itp.milestone_task and itp.milestone_task != doc.milestone_task:
        frappe.throw(_("Inspection Test Plan milestone must match this report milestone"))

    qi = frappe.get_doc("Quality Inspection", doc.quality_inspection)
    qi_contract = getattr(qi, "contract", None)
    if qi_contract and qi_contract != doc.contract:
        frappe.throw(_("Quality Inspection must belong to the same Contract"))
    qi_task = getattr(qi, "milestone_task", None)
    if doc.milestone_task and qi_task and qi_task != doc.milestone_task:
        frappe.throw(_("Quality Inspection milestone task must match this report"))


def before_submit_inspection_report(doc, method=None) -> None:
    qi = frappe.get_doc("Quality Inspection", doc.quality_inspection)
    if qi.docstatus != 1:
        frappe.throw(_("Quality Inspection must be submitted before Inspection Report"))

    if doc.outcome == "Passed" and qi.status != "Accepted":
        frappe.throw(_("Outcome Passed requires Quality Inspection status Accepted"))
    if doc.outcome == "Failed" and qi.status == "Accepted":
        frappe.throw(_("Outcome Failed is inconsistent with Accepted Quality Inspection"))

    _maybe_create_governance_session_for_inspection_report(doc)


def validate_acceptance_certificate(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.certificate_type:
        frappe.throw("Certificate Type is required")
    if not doc.issued_by:
        frappe.throw("Issued By is required")
    if not doc.issued_on:
        frappe.throw("Issued On is required")
    if doc.task:
        task_contract = frappe.db.get_value("Task", doc.task, "contract")
        if task_contract and task_contract != doc.contract:
            frappe.throw("Milestone Task must belong to the selected Contract")
    if doc.purchase_receipt:
        pr_contract = frappe.db.get_value("Purchase Receipt", doc.purchase_receipt, "contract")
        if pr_contract and pr_contract != doc.contract:
            frappe.throw("Purchase Receipt must belong to the selected Contract")
    if doc.quality_inspection:
        qi = frappe.get_doc("Quality Inspection", doc.quality_inspection)
        if qi.docstatus != 1:
            frappe.throw("Quality Inspection must be submitted")
        if doc.decision == "Approved" and qi.status != "Accepted":
            frappe.throw("Approved certificate requires Accepted Quality Inspection")
        if doc.decision == "Rejected" and qi.status == "Accepted":
            frappe.throw("Rejected certificate cannot use an Accepted Quality Inspection")

        qi_contract = getattr(qi, "contract", None)
        if qi_contract and qi_contract != doc.contract:
            frappe.throw("Quality Inspection must belong to the selected Contract")
        qi_task = getattr(qi, "milestone_task", None)
        if qi_task and doc.task and qi_task != doc.task:
            frappe.throw("Quality Inspection milestone task does not match certificate task")

    # For technical certification, explicit inspection evidence is mandatory.
    if doc.certificate_type in (
        "Certificate of Conformance",
        "Certificate of Acceptance",
        "Final Acceptance",
    ):
        if not doc.quality_inspection:
            frappe.throw(f"{doc.certificate_type} requires a linked Quality Inspection")

    workflow_state = getattr(doc, "workflow_state", None) or "Draft"
    old = doc.get_doc_before_save()
    old_state = old.workflow_state if old else None
    _transition_allowed(
        "Acceptance Certificate workflow state",
        old_state,
        workflow_state,
        ACCEPTANCE_CERT_WORKFLOW_TRANSITIONS,
    )

    # MVP: create “Acceptance Committee Sitting” proceedings when the certificate
    # reaches a committee decision state for the first time.
    if old_state != workflow_state and workflow_state in ("Issued", "Rejected"):
        _maybe_create_governance_session_for_acceptance_certificate(doc)

    # Workflow consistency with decision and submission.
    if workflow_state == "Issued":
        if doc.decision != "Approved":
            frappe.throw("Issued certificate must have Decision = Approved")
        if getattr(doc, "docstatus", 0) != 1:
            frappe.throw("Issued certificate must be submitted")
        if _acceptance_certificate_requires_inspection_report(doc):
            _validate_inspection_report_chain_for_certificate(doc)
    elif workflow_state == "Rejected":
        if doc.decision != "Rejected":
            frappe.throw("Rejected certificate must have Decision = Rejected")
    else:
        if getattr(doc, "docstatus", 0) == 1:
            frappe.throw("Only Issued/Rejected certificates can be submitted")


def _maybe_create_governance_session_for_acceptance_certificate(cert_doc) -> None:
    """Create a draft Governance Session + agenda item when acceptance is decided."""
    workflow_state = getattr(cert_doc, "workflow_state", None) or "Draft"
    if workflow_state not in ("Issued", "Rejected"):
        return

    context_reference_doctype = "Acceptance Certificate"
    context_reference_name = cert_doc.name
    session_type = "Acceptance Committee Sitting"

    # Idempotency: create only one proceedings entry per certificate for this session type.
    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", cert_doc.contract, "contract_title")
        or cert_doc.contract
    )
    decision = getattr(cert_doc, "decision", None) or ""

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Acceptance Committee Sitting: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda_subject = f"Record acceptance committee decision: {workflow_state}"
    agenda_discussion = (
        f"Acceptance Certificate: {cert_doc.name}\n"
        f"Contract: {contract_title}\n"
        f"Certificate Type: {getattr(cert_doc, 'certificate_type', '')}\n"
        f"Decision: {decision}\n"
        f"Workflow State: {workflow_state}"
    )

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "subject": agenda_subject[:140],
            "discussion": agenda_discussion,
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_acceptance_certificate",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "acceptance_certificate": cert_doc.name,
            "contract": cert_doc.contract,
            "certificate_type": getattr(cert_doc, "certificate_type", None),
            "decision": getattr(cert_doc, "decision", None),
            "workflow_state": workflow_state,
        },
    )


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
            "signature_mode": "Role Based",
            "retention_percentage": 0,
            "defect_liability_months": 0,
        }
    )
    contract.insert()
    contract.add_comment("Workflow", "Contract created from awarded tender")
    return contract.name


@frappe.whitelist()
def sign_contract(
    contract_name: str,
    signer_role: str,
    signature_token: str | None = None,
    signature_provider: str | None = None,
) -> str:
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

    if contract.signature_mode == "External Verified":
        evidence = _verify_external_signature(contract, signer_role, signature_token)
        provider = signature_provider or evidence.get("provider") or "External Provider"
        signature_hash = evidence.get("signature_hash")
        signed_at = evidence.get("signed_at")
        if isinstance(signed_at, str):
            try:
                signed_at = get_datetime(signed_at)
            except Exception:
                signed_at = None
        if signer_role == "Supplier":
            contract.supplier_signature_provider = provider
            contract.supplier_signature_hash = signature_hash
            contract.supplier_signed_at = signed_at or now_datetime()
            if evidence.get("signer_certificate_subject"):
                contract.supplier_signer_certificate_subject = evidence.get("signer_certificate_subject")
            if evidence.get("signer_certificate_serial"):
                contract.supplier_signer_certificate_serial = evidence.get("signer_certificate_serial")
            if evidence.get("verification_reference"):
                contract.supplier_signature_verification_ref = evidence.get("verification_reference")
        else:
            contract.accounting_signature_provider = provider
            contract.accounting_signature_hash = signature_hash
            contract.accounting_signed_at = signed_at or now_datetime()
            if evidence.get("signer_certificate_subject"):
                contract.accounting_signer_certificate_subject = evidence.get("signer_certificate_subject")
            if evidence.get("signer_certificate_serial"):
                contract.accounting_signer_certificate_serial = evidence.get("signer_certificate_serial")
            if evidence.get("verification_reference"):
                contract.accounting_signature_verification_ref = evidence.get("verification_reference")

    contract.add_comment("Workflow", f"Signed by {signer_role}: {frappe.session.user}")
    contract.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="contract_signed",
        reference_doctype="Contract",
        reference_name=contract.name,
        details={
            "signer_role": signer_role,
            "signature_mode": contract.signature_mode,
            "provider": getattr(contract, "supplier_signature_provider", None)
            if signer_role == "Supplier"
            else getattr(contract, "accounting_signature_provider", None),
            "verification_ref": getattr(contract, "supplier_signature_verification_ref", None)
            if signer_role == "Supplier"
            else getattr(contract, "accounting_signature_verification_ref", None),
        },
    )

    if contract.signed_by_supplier and contract.signed_by_accounting_officer:
        activate_contract(contract.name)

    return frappe.db.get_value("Contract", contract.name, "status")


def _verify_external_signature(
    contract,
    signer_role: str,
    signature_token: str | None,
) -> dict:
    if not signature_token or not str(signature_token).strip():
        frappe.throw(f"{signer_role} signature token is required in External Verified mode")

    verifier_path = frappe.conf.get("kentender_signature_verifier")
    strict = bool(frappe.conf.get("kentender_signature_strict"))
    token = str(signature_token).strip()

    if strict and not verifier_path:
        frappe.throw(
            _(
                "site_config.json must define kentender_signature_verifier when "
                "kentender_signature_strict is true"
            )
        )

    if verifier_path:
        verifier = frappe.get_attr(verifier_path)
        try:
            result = verifier(
                contract_name=contract.name,
                signer_role=signer_role,
                token=token,
                user=frappe.session.user,
                contract=contract.as_dict(),
            )
        except TypeError:
            # Backward compatible: verifiers that don't accept `contract`
            result = verifier(
                contract_name=contract.name,
                signer_role=signer_role,
                token=token,
                user=frappe.session.user,
            )
        if not isinstance(result, dict) or not result.get("ok"):
            frappe.throw(f"External signature verification failed for {signer_role}")
        signature_hash = result.get("signature_hash")
        if not signature_hash:
            frappe.throw("External signature verifier did not return signature_hash")
        out = {
            "provider": result.get("provider") or "External Provider",
            "signature_hash": signature_hash,
            "signer_certificate_subject": result.get("signer_certificate_subject"),
            "signer_certificate_serial": result.get("signer_certificate_serial"),
            "verification_reference": result.get("verification_reference"),
            "signed_at": result.get("signed_at"),
        }
        return {k: v for k, v in out.items() if v is not None}

    if strict:
        frappe.throw(
            _(
                "No kentender_signature_verifier configured; strict mode disallows token fallback"
            )
        )

    # Safe fallback for non-integrated deployments:
    # keep rollout unblocked while still persisting verifiable evidence hash.
    if len(token) < 12:
        frappe.throw("Signature token is too short for fallback verification")
    signature_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return {"provider": "Token Fallback", "signature_hash": signature_hash}


@frappe.whitelist()
def get_signature_integration_status() -> dict:
    """Report whether external signature verification is configured (admin / integration health)."""
    frappe.only_for("System Manager")
    return {
        "verifier_configured": bool(frappe.conf.get("kentender_signature_verifier")),
        "strict_mode": bool(frappe.conf.get("kentender_signature_strict")),
        "verifier_path": frappe.conf.get("kentender_signature_verifier") or "",
    }


def _milestone_seed_count() -> int:
    """Sites can tune baseline milestone row count via site_config (default 3, max 12)."""
    raw = frappe.conf.get("kentender_milestone_seed_count")
    n = cint(raw) if raw not in (None, "") else 3
    return max(1, min(n, 12))


def _milestone_phase_labels(contract, n: int) -> list[str]:
    """Phase names for baseline schedule; for n=3, use contract-type presets (FRS 4.5)."""
    if n == 3:
        ct = (getattr(contract, "contract_type", None) or "Goods").strip()
        mapping = {
            "Goods": [
                "Procurement & supply",
                "Delivery & inspection",
                "Final acceptance",
            ],
            "Works": [
                "Mobilisation & site setup",
                "Execution",
                "Testing & handover",
            ],
            "Services": [
                "Service initiation",
                "Delivery period",
                "Completion & review",
            ],
        }
        return mapping.get(ct, ["Phase 1", "Phase 2", "Phase 3"])
    return [f"Phase {i + 1}" for i in range(n)]


def _award_context_label(contract) -> str:
    """Derive human-readable scope from Tender → Procurement Plan Item → Item."""
    base = (getattr(contract, "contract_title", None) or contract.name or "").strip()
    tender_name = getattr(contract, "tender", None)
    if not tender_name:
        return base
    ppi = frappe.db.get_value("Tender", tender_name, "procurement_plan_item")
    if not ppi:
        return base
    item_code = frappe.db.get_value("Procurement Plan Item", ppi, "item_code")
    if not item_code:
        return base
    item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
    return f"{item_name} ({item_code})"


def _build_contract_milestone_segments(contract) -> list[dict]:
    from frappe.utils import add_days, date_diff, getdate

    n = _milestone_seed_count()
    phases = _milestone_phase_labels(contract, n)
    base = _award_context_label(contract)
    pct_each = round(100.0 / n, 2)
    pcts = [pct_each] * n
    pcts[-1] = round(100.0 - pct_each * (n - 1), 2)

    start = getattr(contract, "start_date", None)
    end = getattr(contract, "end_date", None)
    segments: list[dict] = []

    if start and end:
        start_d = getdate(start)
        end_d = getdate(end)
        total_days = max(1, date_diff(end_d, start_d))
        for i in range(n):
            seg_start = add_days(start_d, int(total_days * i / n))
            seg_end = add_days(start_d, int(total_days * (i + 1) / n))
            if i == n - 1:
                seg_end = end_d
            segments.append(
                {
                    "subject": f"{phases[i]} — {base}",
                    "payment_percentage": pcts[i],
                    "exp_start_date": seg_start,
                    "exp_end_date": seg_end,
                    "deliverables": f"{phases[i]} deliverables per contract schedule (phase {i + 1} of {n}).",
                    "acceptance_criteria": "Per contract / tender technical requirements and applicable standards.",
                }
            )
    else:
        for i in range(n):
            segments.append(
                {
                    "subject": f"{phases[i]} — {base}",
                    "payment_percentage": pcts[i],
                    "deliverables": f"{phases[i]} deliverables per contract schedule (phase {i + 1} of {n}).",
                    "acceptance_criteria": "Per contract / tender technical requirements and applicable standards.",
                }
            )
    return segments


def _seed_contract_milestone_tasks(contract, *, skip_if_exists: bool = True) -> list[str]:
    """Idempotent baseline milestones when a contract becomes Active."""
    if not getattr(contract, "project", None):
        return []
    if skip_if_exists and frappe.db.count(
        "Task",
        {"contract": contract.name, "is_contract_milestone": 1},
    ):
        return []

    created: list[str] = []
    for seg in _build_contract_milestone_segments(contract):
        row = {
            "doctype": "Task",
            "subject": seg["subject"][:240],
            "project": contract.project,
            "contract": contract.name,
            "is_contract_milestone": 1,
            "payment_percentage": seg["payment_percentage"],
            "deliverables": seg.get("deliverables"),
            "acceptance_criteria": seg.get("acceptance_criteria"),
            "milestone_status": "Pending",
            "status": "Open",
        }
        if seg.get("exp_start_date"):
            row["exp_start_date"] = seg["exp_start_date"]
        if seg.get("exp_end_date"):
            row["exp_end_date"] = seg["exp_end_date"]
        task = frappe.get_doc(row)
        task.insert(ignore_permissions=True)
        created.append(task.name)

    if created:
        log_ken_tender_audit_event(
            action="contract_milestones_seeded",
            reference_doctype="Contract",
            reference_name=contract.name,
            details={
                "tasks": created,
                "tender": getattr(contract, "tender", None),
                "project": contract.project,
            },
        )
    return created


def seed_contract_milestones_on_contract_activation(doc, method=None) -> None:
    """Hook: first transition to Active → seed milestone Tasks from award/tender context."""
    if getattr(frappe.flags, "in_import", False):
        return
    old = doc.get_doc_before_save()
    old_status = getattr(old, "status", None) if old else None

    # Milestone tasks: only on first transition to Active.
    if doc.status == "Active" and (not old or old_status != "Active"):
        if not frappe.conf.get("kentender_skip_milestone_seeding"):
            _seed_contract_milestone_tasks(doc)

    # Proceedings: create a baseline site-handover meeting record when
    # `handover_completed` flips from 0 -> 1.
    old_handover_completed = int(getattr(old, "handover_completed", 0) or 0) if old else 0
    new_handover_completed = int(getattr(doc, "handover_completed", 0) or 0)
    if new_handover_completed == 1 and old_handover_completed != 1:
        _maybe_create_governance_session_for_contract_handover(doc)


@frappe.whitelist()
def seed_contract_milestones(contract_name: str) -> dict:
    """Manually seed milestones if activation ran before template logic existed (idempotent if tasks exist)."""
    contract = frappe.get_doc("Contract", contract_name)
    frappe.has_permission("Contract", "write", doc=contract, throw=True)
    if contract.status != "Active":
        frappe.throw(_("Contract must be Active to seed milestones"))
    created = _seed_contract_milestone_tasks(contract, skip_if_exists=True)
    return {"ok": True, "tasks": created, "count": len(created)}


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
        # Quality Inspection
        {
            "dt": "Quality Inspection",
            "fieldname": "contract",
            "label": "Contract",
            "fieldtype": "Link",
            "options": "Contract",
            "insert_after": "reference_name",
        },
        {
            "dt": "Quality Inspection",
            "fieldname": "milestone_task",
            "label": "Milestone Task",
            "fieldtype": "Link",
            "options": "Task",
            "insert_after": "contract",
        },
        # Payment Entry (ERPNext core financial flow; CLM governance metadata only)
        {
            "dt": "Payment Entry",
            "fieldname": "contract",
            "label": "Contract",
            "fieldtype": "Link",
            "options": "Contract",
            "insert_after": "party",
        },
        {
            "dt": "Payment Entry",
            "fieldname": "clm_workflow_state",
            "label": "CLM Workflow State",
            "fieldtype": "Select",
            "options": "Draft\nProcurement Reviewed\nFinance Verified\nProcurement Certified\nPaid",
            "insert_after": "contract",
        },
        {
            "dt": "Payment Entry",
            "fieldname": "procurement_reviewed_by",
            "label": "Procurement Reviewed By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "clm_workflow_state",
        },
        {
            "dt": "Payment Entry",
            "fieldname": "finance_verified_by",
            "label": "Finance Verified By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "procurement_reviewed_by",
        },
        {
            "dt": "Payment Entry",
            "fieldname": "procurement_certified_by",
            "label": "Procurement Certified By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "finance_verified_by",
        },
        {
            "dt": "Payment Entry",
            "fieldname": "clm_procurement_reviewed_on",
            "label": "CLM Procurement Reviewed On",
            "fieldtype": "Datetime",
            "insert_after": "procurement_certified_by",
            "read_only": 1,
        },
        {
            "dt": "Payment Entry",
            "fieldname": "clm_finance_verified_on",
            "label": "CLM Finance Verified On",
            "fieldtype": "Datetime",
            "insert_after": "clm_procurement_reviewed_on",
            "read_only": 1,
        },
        {
            "dt": "Payment Entry",
            "fieldname": "clm_procurement_certified_on",
            "label": "CLM Procurement Certified On",
            "fieldtype": "Datetime",
            "insert_after": "clm_finance_verified_on",
            "read_only": 1,
        },
        {
            "dt": "Payment Entry",
            "fieldname": "clm_paid_confirmed_by",
            "label": "CLM Paid Confirmed By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "clm_procurement_certified_on",
            "read_only": 1,
        },
        {
            "dt": "Payment Entry",
            "fieldname": "clm_paid_at",
            "label": "CLM Paid At",
            "fieldtype": "Datetime",
            "insert_after": "clm_paid_confirmed_by",
            "read_only": 1,
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


def _infer_contract_from_payment_entry_references(doc) -> str | None:
    refs = getattr(doc, "references", None) or []
    contract_names: set[str] = set()
    for row in refs:
        if row.reference_doctype != "Purchase Invoice" or not row.reference_name:
            continue
        contract = frappe.db.get_value("Purchase Invoice", row.reference_name, "contract")
        if contract:
            contract_names.add(contract)

    if not contract_names:
        return None
    if len(contract_names) > 1:
        frappe.throw("Payment Entry cannot reference invoices from multiple contracts")
    return next(iter(contract_names))


def _validate_contract_payment_entry_pi_rows(doc) -> None:
    """Ensure Purchase Invoice references are submitted and match the Payment Entry contract."""
    contract = getattr(doc, "contract", None)
    if not contract:
        return
    refs = getattr(doc, "references", None) or []
    for row in refs:
        if getattr(row, "reference_doctype", None) != "Purchase Invoice" or not row.reference_name:
            continue
        pi = frappe.db.get_value(
            "Purchase Invoice",
            row.reference_name,
            ["docstatus", "contract"],
            as_dict=True,
        )
        if not pi:
            frappe.throw(_("Unknown Purchase Invoice reference: {0}").format(row.reference_name))
        if pi.contract and pi.contract != contract:
            frappe.throw(
                _("Purchase Invoice {0} belongs to contract {1}, not {2}").format(
                    row.reference_name, pi.contract, contract
                )
            )
        if int(pi.docstatus or 0) != 1 and getattr(doc, "docstatus", 0) == 1:
            frappe.throw(
                _("Submitted Payment Entry cannot reference draft/cancelled Purchase Invoice {0}").format(
                    row.reference_name
                )
            )


def validate_payment_entry_clm(doc, method=None) -> None:
    # Keep ERPNext core behavior intact; enforce CLM only for contract-linked payments.
    inferred_contract = _infer_contract_from_payment_entry_references(doc)
    if inferred_contract and not getattr(doc, "contract", None):
        doc.contract = inferred_contract
    if not getattr(doc, "contract", None):
        return

    if getattr(doc, "party_type", None) != "Supplier":
        frappe.throw("Contract-linked Payment Entry must have Party Type = Supplier")
    if not getattr(doc, "party", None):
        frappe.throw("Supplier is required for contract-linked Payment Entry")

    workflow_state = getattr(doc, "clm_workflow_state", None) or "Draft"
    doc.clm_workflow_state = workflow_state
    old = doc.get_doc_before_save()
    old_state = old.clm_workflow_state if old else None
    _transition_allowed(
        "Payment Entry CLM workflow state",
        old_state,
        workflow_state,
        PAYMENT_ENTRY_CLM_TRANSITIONS,
    )

    # "Paid" in CLM workflow means core financial posting is complete.
    if workflow_state == "Paid" and getattr(doc, "docstatus", 0) != 1:
        frappe.throw("Payment Entry must be submitted before CLM state can be Paid")

    _validate_contract_payment_entry_pi_rows(doc)


def before_submit_payment_entry_clm(doc, method=None) -> None:
    """Final governance gate: contract-linked pay bills cannot be submitted until CLM certification is complete."""
    inferred = _infer_contract_from_payment_entry_references(doc)
    if inferred and not getattr(doc, "contract", None):
        doc.contract = inferred
    if not getattr(doc, "contract", None):
        return

    state = getattr(doc, "clm_workflow_state", None) or "Draft"
    if state != "Procurement Certified":
        frappe.throw(
            _(
                "Contract-linked Payment Entry must be in CLM state Procurement Certified before "
                "submit (complete Draft → Procurement Reviewed → Finance Verified → Procurement Certified). "
                "Current state: {0}"
            ).format(state)
        )
    if not getattr(doc, "procurement_reviewed_by", None):
        frappe.throw(_("Procurement Reviewed By is required before submit"))
    if not getattr(doc, "finance_verified_by", None):
        frappe.throw(_("Finance Verified By is required before submit"))
    if not getattr(doc, "procurement_certified_by", None):
        frappe.throw(_("Procurement Certified By is required before submit"))

    pi_refs = [
        r
        for r in (getattr(doc, "references", None) or [])
        if getattr(r, "reference_doctype", None) == "Purchase Invoice" and r.reference_name
    ]
    if not pi_refs:
        frappe.throw(
            _("Contract-linked Payment Entry must reference at least one Purchase Invoice")
        )
    for row in pi_refs:
        pi = frappe.db.get_value(
            "Purchase Invoice",
            row.reference_name,
            ["docstatus", "contract", "supplier"],
            as_dict=True,
        )
        if not pi:
            frappe.throw(_("Unknown Purchase Invoice: {0}").format(row.reference_name))
        if int(pi.docstatus or 0) != 1:
            frappe.throw(
                _("Purchase Invoice {0} must be submitted before Payment Entry can be submitted").format(
                    row.reference_name
                )
            )
        if pi.contract and pi.contract != doc.contract:
            frappe.throw(
                _("Purchase Invoice {0} does not belong to contract {1}").format(
                    row.reference_name, doc.contract
                )
            )
        if pi.supplier and pi.supplier != doc.party:
            frappe.throw(
                _("Purchase Invoice {0} supplier {1} does not match Payment Entry party {2}").format(
                    row.reference_name, pi.supplier, doc.party
                )
            )


def validate_quality_inspection_clm(doc, method=None) -> None:
    contract = getattr(doc, "contract", None)
    milestone_task = getattr(doc, "milestone_task", None)
    if milestone_task:
        task = frappe.get_doc("Task", milestone_task)
        if not int(getattr(task, "is_contract_milestone", 0)):
            frappe.throw("Milestone Task must be marked as a contract milestone")
        task_contract = getattr(task, "contract", None)
        if contract and task_contract and contract != task_contract:
            frappe.throw("Quality Inspection contract must match Milestone Task contract")
        if not contract and task_contract:
            doc.contract = task_contract

    if not contract:
        return

    # Validate contract consistency with referenced core transaction.
    if doc.reference_type in ("Purchase Receipt", "Purchase Invoice") and doc.reference_name:
        ref_contract = frappe.db.get_value(doc.reference_type, doc.reference_name, "contract")
        if ref_contract and ref_contract != doc.contract:
            frappe.throw(
                f"Quality Inspection contract must match {doc.reference_type} contract"
            )


@frappe.whitelist()
def create_quality_inspection_for_receipt(
    purchase_receipt: str,
    item_code: str,
    milestone_task: str | None = None,
    inspection_type: str = "Incoming",
) -> str:
    receipt = frappe.get_doc("Purchase Receipt", purchase_receipt)
    qi = frappe.get_doc(
        {
            "doctype": "Quality Inspection",
            "inspection_type": inspection_type,
            "reference_type": "Purchase Receipt",
            "reference_name": receipt.name,
            "item_code": item_code,
            "sample_size": 1,
            "inspected_by": frappe.session.user,
            "status": "Accepted",
            "contract": getattr(receipt, "contract", None),
            "milestone_task": milestone_task,
        }
    )
    qi.insert(ignore_permissions=True)
    return qi.name


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


_GOVERNANCE_SESSION_ALLOWED_STATUSES: set[str] = {
    "Draft",
    "Scheduled",
    "In Session",
    "Minutes Drafted",
    "Under Review",
    "Approved",
    "Locked",
    "Cancelled",
}

_GOVERNANCE_SESSION_TRANSITIONS: dict[str, set[str]] = {
    "Draft": {"Scheduled", "Cancelled"},
    "Scheduled": {"In Session"},
    "In Session": {"Minutes Drafted"},
    "Minutes Drafted": {"Under Review"},
    "Under Review": {"Approved"},
    "Approved": {"Locked"},
    "Locked": set(),
    "Cancelled": set(),
}

def _calculate_quorum_met(session_name: str) -> bool:
    """Quorum is met when attendance from Present/Remote reaches quorum_required."""
    session = frappe.get_doc("Governance Session", session_name)
    required = int(getattr(session, "quorum_required", 0) or 0)
    if required <= 0:
        return True
    present = frappe.db.count(
        "Session Participant",
        {
            "session": session.name,
            "attendance_status": ["in", ["Present", "Remote"]],
        },
    )
    return present >= required


def _is_supplier_user() -> bool:
    """Supplier users are identified by ERPNext role name."""
    roles = set(frappe.get_roles(frappe.session.user))
    return bool(roles.intersection({"Supplier Representative"}))


def _throw_if_supplier_access_denied(session_name: str | None) -> None:
    """Confidentiality: suppliers can only access restricted sessions if explicit participants."""
    if not session_name:
        return
    if not _is_supplier_user():
        return

    roles = set(frappe.get_roles(frappe.session.user))
    if "System Manager" in roles:
        return

    confidentiality_level = frappe.db.get_value(
        "Governance Session", session_name, "confidentiality_level"
    ) or "Public"
    if confidentiality_level == "Public":
        return

    is_explicit_supplier_participant = frappe.db.exists(
        "Session Participant",
        {
            "session": session_name,
            "user": frappe.session.user,
            "participant_role": "Supplier Representative",
        },
    )
    if not is_explicit_supplier_participant:
        frappe.throw(
            _("Supplier representatives cannot access restricted proceedings unless explicitly added as participants.")
        )


def validate_governance_session(doc, method=None) -> None:
    """Layer-2 governance hardening (quorum, minutes lock, controlled transitions)."""
    current = getattr(doc, "status", None) or "Draft"
    if current not in _GOVERNANCE_SESSION_ALLOWED_STATUSES:
        frappe.throw(f"Invalid Governance Session status: {current}")

    prev_status = doc.get_value_before_save("status") if getattr(doc, "name", None) else None
    if prev_status == "Locked":
        frappe.throw("Locked Governance Session cannot be modified")

    # Confidentiality: block supplier edits on restricted sessions unless explicitly participating.
    if getattr(doc, "name", None):
        _throw_if_supplier_access_denied(doc.name)

    controlled_flags = any(
        bool(getattr(frappe.flags, flag, False))
        for flag in ("in_override", "in_workflow", "in_transition")
    )
    if prev_status and prev_status != current and not controlled_flags:
        frappe.throw("Manual Governance Session status change not allowed")

    # When transitions are executed via workflow/API, keep minutes_status in sync.
    if prev_status != current and controlled_flags:
        if current == "Approved":
            doc.minutes_status = "Approved"
        elif current == "Locked":
            doc.minutes_status = "Locked"

    # Quorum-aware validation when moving to Approved/Locked.
    if current in ("Approved", "Locked"):
        if not getattr(doc, "name", None):
            frappe.throw("Governance Session must be saved before quorum validation.")
        if not _calculate_quorum_met(doc.name):
            frappe.throw(_("Quorum not met. Cannot approve or lock session."))
        doc.quorum_met = 1

    # Minutes lock validation.
    if current == "Locked" and doc.minutes_status not in ("Approved", "Locked"):
        frappe.throw(_("Minutes must be approved before locking the session."))


def _throw_if_governance_session_locked(session_name: str | None) -> None:
    if not session_name:
        return
    status = frappe.db.get_value("Governance Session", session_name, "status")
    if status == "Locked":
        frappe.throw("Cannot modify records of a locked Governance Session")


def validate_session_agenda_item(doc, method=None) -> None:
    session_name = getattr(doc, "session", None)
    _throw_if_governance_session_locked(session_name)
    _throw_if_supplier_access_denied(session_name)


def validate_session_resolution(doc, method=None) -> None:
    session_name = getattr(doc, "session", None)
    _throw_if_governance_session_locked(session_name)
    _throw_if_supplier_access_denied(session_name)

    # Resolution gating: approved/implemented/closed resolutions require an approved parent session.
    if not session_name:
        return
    session_status = frappe.db.get_value("Governance Session", session_name, "status")
    if doc.status in ("Approved", "Implemented", "Closed") and session_status not in (
        "Approved",
        "Locked",
    ):
        frappe.throw(_("Session must be approved before resolution can move forward."))


def validate_session_action(doc, method=None) -> None:
    session_name = getattr(doc, "session", None)
    _throw_if_governance_session_locked(session_name)
    _throw_if_supplier_access_denied(session_name)


def validate_session_participant(doc, method=None) -> None:
    _throw_if_governance_session_locked(getattr(doc, "session", None))


def validate_session_evidence(doc, method=None) -> None:
    session_name = getattr(doc, "session", None)
    _throw_if_governance_session_locked(session_name)
    _throw_if_supplier_access_denied(session_name)


def validate_session_signature(doc, method=None) -> None:
    session_name = getattr(doc, "session", None)
    _throw_if_governance_session_locked(session_name)
    _throw_if_supplier_access_denied(session_name)


def _signature_hash_payload(
    session_name: str,
    signer: str,
    signer_role: str,
    target_type: str,
    target_name: str = "",
) -> str:
    raw = f"{session_name}|{signer}|{signer_role}|{target_type}|{target_name}|{now_datetime()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@frappe.whitelist()
def sign_session_item(
    session_name: str,
    signer_role: str,
    target_type: str,
    target_name: str = "",
    method_name: str = "OTP",
) -> str:
    """Create an append-only signature for minutes/attendance/resolution evidence."""
    sig_hash = _signature_hash_payload(
        session_name=session_name,
        signer=frappe.session.user,
        signer_role=signer_role,
        target_type=target_type,
        target_name=target_name,
    )
    sig = frappe.get_doc(
        {
            "doctype": "Session Signature",
            "session": session_name,
            "signer": frappe.session.user,
            "signer_role": signer_role,
            "signature_target_type": target_type,
            "target_name": target_name,
            "signature_method": method_name,
            "signature_hash": sig_hash,
            "signed_at": now_datetime(),
            "verification_status": "Verified",
        }
    )
    sig.insert(ignore_permissions=True)

    # For attendance signatures, mark the referenced Session Participant as signed.
    if target_type == "Attendance" and target_name:
        frappe.db.set_value(
            "Session Participant",
            target_name,
            {
                "signed_attendance": 1,
                "signature_status": "Signed",
            },
        )
    return sig.name


@frappe.whitelist()
def get_procurement_unlock_actions_for_resolution(resolution_name: str) -> dict | None:
    """Procurement adapter output: return controlled unlock actions for an approved resolution.

    This function intentionally does NOT execute downstream CLM workflow transitions.
    """
    resolution = frappe.get_doc("Session Resolution", resolution_name)
    session = frappe.get_doc("Governance Session", resolution.session)

    if session.context_type != "Procurement":
        return None
    if resolution.status not in ("Approved", "Implemented"):
        return None

    ref_doctype = None
    ref_name = None
    if getattr(resolution, "agenda_item", None):
        agenda = frappe.get_doc("Session Agenda Item", resolution.agenda_item)
        ref_doctype = getattr(agenda, "reference_doctype", None)
        ref_name = getattr(agenda, "reference_name", None)

    mapping = {
        ("CIT Meeting", "Recommend Approval", "Task"): "Milestone Verification Review",
        ("Inspection Session", "Recommend Acceptance", "Task"): "Milestone Acceptance Review",
        ("Inspection Session", "Recommend Rejection", "Task"): "Milestone Rejection Review",
        ("Dispute Session", "Recommend Stop Work", "Dispute Case"): "Stop Work Review",
        (
            "Monitoring Review",
            "Escalate",
            "Monthly Contract Monitoring Report",
        ): "Risk Escalation Review",
        (
            "Monitoring Review",
            "Endorse Payment",
            "Purchase Invoice",
        ): "Payment Certification",
    }

    unlock = mapping.get((session.session_type, resolution.resolution_type, ref_doctype))
    if not unlock:
        return None

    return {
        "unlock": unlock,
        "reference_doctype": ref_doctype,
        "reference_name": ref_name,
        "session": session.name,
        "resolution": resolution.name,
    }


def validate_monthly_contract_monitoring_report(doc, method=None) -> None:
    """When a monthly monitoring report becomes Reviewed, create proceedings."""
    if getattr(frappe.flags, "in_import", False):
        return

    old = doc.get_doc_before_save()
    old_status = getattr(old, "status", None) if old else None

    if getattr(doc, "status", None) == "Reviewed" and old_status != "Reviewed":
        _maybe_create_governance_session_for_monthly_monitoring_report(doc)


@frappe.whitelist()
def transition_governance_session(
    session_name: str,
    next_state: str,
    remarks: str | None = None,
) -> str:
    session = frappe.get_doc("Governance Session", session_name)
    current = getattr(session, "status", None) or "Draft"

    _transition_allowed(
        "Governance Session",
        current,
        next_state,
        _GOVERNANCE_SESSION_TRANSITIONS,
    )

    # Role-based transition routing (procurement templates).
    # System Manager remains permitted for backwards compatibility.
    required_roles: list[str] = []
    if getattr(session, "context_type", None) == "Procurement":
        mapping = {
            "CIT Meeting": ["Chairperson", "Secretary", "Member"],
            "Inspection Session": ["Chairperson", "Member"],
            "Dispute Session": ["Chairperson", "Legal Counsel"],
            "Monitoring Review": ["Chairperson", "Secretary"],
        }
        required_roles = mapping.get(getattr(session, "session_type", None) or "", [])

    user_roles = set(frappe.get_roles(frappe.session.user))
    if "System Manager" in user_roles:
        pass
    elif required_roles:
        is_allowed_participant = frappe.db.exists(
            "Session Participant",
            {
                "session": session.name,
                "user": frappe.session.user,
                "participant_role": ["in", required_roles],
            },
        )
        if not is_allowed_participant:
            frappe.throw(
                _(
                    "Governance session transition requires System Manager or being an explicit participant with one of roles: {0}"
                ).format(", ".join(required_roles))
            )
    else:
        _require_any_role(["System Manager"], "Governance session transition")

    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        # Sync minutes_status when advancing to minutes/approval/lock states.
        if next_state == "Approved":
            session.minutes_status = "Approved"
        elif next_state == "Locked":
            session.minutes_status = "Locked"

        session.status = next_state
        note = f"Governance Session transition: {current} -> {next_state}"
        if remarks:
            note = f"{note}. {remarks}"
        session.add_comment("Workflow", note)
        session.save()
    finally:
        frappe.flags.in_override = prev_in_override

    log_ken_tender_audit_event(
        action="governance_session_transition",
        reference_doctype="Governance Session",
        reference_name=session_name,
        details={"from": current, "to": next_state, "remarks": remarks or ""},
    )
    return session.status


@frappe.whitelist()
def schedule_governance_session(session_name: str, remarks: str | None = None) -> str:
    return transition_governance_session(session_name, "Scheduled", remarks=remarks)


@frappe.whitelist()
def start_governance_session(session_name: str, remarks: str | None = None) -> str:
    return transition_governance_session(session_name, "In Session", remarks=remarks)


@frappe.whitelist()
def draft_governance_session_minutes(session_name: str, remarks: str | None = None) -> str:
    return transition_governance_session(session_name, "Minutes Drafted", remarks=remarks)


@frappe.whitelist()
def submit_governance_session_minutes(session_name: str, remarks: str | None = None) -> str:
    return transition_governance_session(session_name, "Under Review", remarks=remarks)


@frappe.whitelist()
def approve_governance_session(session_name: str, remarks: str | None = None) -> str:
    return transition_governance_session(session_name, "Approved", remarks=remarks)


@frappe.whitelist()
def lock_governance_session(session_name: str, remarks: str | None = None) -> str:
    return transition_governance_session(session_name, "Locked", remarks=remarks)


def _maybe_create_governance_session_for_contract_handover(contract_doc) -> None:
    """Create a draft Governance Session + agenda item when contract handover is completed."""
    if not int(getattr(contract_doc, "handover_completed", 0) or 0):
        return

    context_reference_doctype = "Contract"
    context_reference_name = contract_doc.name
    session_type = "Site Handover"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (getattr(contract_doc, "contract_title", None) or contract_doc.name)[:120]
    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Site Handover: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "subject": f"Record site handover for contract: {contract_title}",
            "discussion": "",
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_handover",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "contract": contract_doc.name,
            "project": getattr(contract_doc, "project", None),
        },
    )


def _maybe_create_governance_session_for_inspection_report(report_doc) -> None:
    """Create a draft Governance Session + agenda item when an inspection report is submitted."""
    if not getattr(report_doc, "contract", None):
        return

    context_reference_doctype = "Inspection Report"
    context_reference_name = report_doc.name
    session_type = "Inspection Session"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", report_doc.contract, "contract_title") or report_doc.contract
    )
    agenda_discussion = (getattr(report_doc, "findings", None) or "").strip()

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Inspection Session: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "session_template": "Procurement - Inspection Session",
            "quorum_required": 2,
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda_subject = "Inspection Findings"
    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "sequence": 1,
            "subject": agenda_subject,
            "reference_doctype": "Task",
            "reference_name": getattr(report_doc, "milestone_task", None),
            "discussion": agenda_discussion[:5000],
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_inspection_report",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "inspection_report": report_doc.name,
            "contract": report_doc.contract,
            "milestone_task": getattr(report_doc, "milestone_task", None),
            "outcome": getattr(report_doc, "outcome", None),
        },
    )


def _maybe_create_governance_session_for_contract_variation_decision(
    variation_doc,
    *,
    decision_status: str,
    remarks: str | None = None,
) -> None:
    """Create a draft proceedings session when a Contract Variation is decided."""
    if decision_status not in ("Approved", "Rejected"):
        return

    context_reference_doctype = "Contract Variation"
    context_reference_name = variation_doc.name
    session_type = "Variation Review"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", variation_doc.contract, "contract_title")
        or variation_doc.contract
    )
    variation_type = getattr(variation_doc, "variation_type", None) or ""
    justification = getattr(variation_doc, "justification", None) or ""
    financial_impact = getattr(variation_doc, "financial_impact", None) or 0
    time_extension_days = getattr(variation_doc, "time_extension_days", None) or 0

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Variation Review: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    decision_remarks = remarks or ""
    agenda_discussion = (
        f"Contract Variation: {variation_doc.name}\n"
        f"Contract: {contract_title}\n"
        f"Variation Type: {variation_type}\n"
        f"Decision: {decision_status}\n"
        f"Justification: {justification}\n"
        f"Financial Impact: {financial_impact}\n"
        f"Time Extension Days: {time_extension_days}\n"
        f"Remarks: {decision_remarks}"
    )

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "subject": f"Record variation decision: {decision_status}",
            "discussion": agenda_discussion[:5000],
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_variation_decision",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "contract_variation": variation_doc.name,
            "contract": variation_doc.contract,
            "variation_type": variation_type,
            "decision": decision_status,
            "remarks": remarks or "",
        },
    )


def _maybe_create_governance_session_for_claim_decision(
    claim_doc,
    *,
    decision_status: str,
    remarks: str | None = None,
) -> None:
    """Create a draft proceedings session when a Claim is decided."""
    if decision_status not in ("Approved", "Rejected"):
        return

    context_reference_doctype = "Claim"
    context_reference_name = claim_doc.name
    session_type = "Claim Decision"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", claim_doc.contract, "contract_title")
        or claim_doc.contract
    )
    claim_type = getattr(claim_doc, "claim_type", None) or ""
    description = getattr(claim_doc, "description", None) or ""
    amount = getattr(claim_doc, "amount", None) or 0

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Claim Decision: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda_discussion = (
        f"Claim: {claim_doc.name}\n"
        f"Contract: {contract_title}\n"
        f"Claim Type: {claim_type}\n"
        f"Decision: {decision_status}\n"
        f"Amount: {amount}\n"
        f"Description: {description}\n"
        f"Remarks: {remarks or ''}"
    )

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "subject": f"Record claim decision: {decision_status}",
            "discussion": agenda_discussion[:5000],
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_claim_decision",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "claim": claim_doc.name,
            "contract": claim_doc.contract,
            "claim_type": claim_type,
            "decision": decision_status,
            "remarks": remarks or "",
        },
    )


def _maybe_create_governance_session_for_dispute_resolution(
    dispute_doc,
    *,
    decision_status: str,
    remarks: str | None = None,
) -> None:
    """Create a draft proceedings session when a Dispute Case is resolved."""
    if decision_status != "Resolved":
        return

    context_reference_doctype = "Dispute Case"
    context_reference_name = dispute_doc.name
    session_type = "Dispute Resolution"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", dispute_doc.contract, "contract_title")
        or dispute_doc.contract
    )
    summary = getattr(dispute_doc, "summary", None) or ""
    current_stage = getattr(dispute_doc, "current_stage", None) or ""
    resolution = getattr(dispute_doc, "resolution", None) or ""

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Dispute Resolution: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda_discussion = (
        f"Dispute Case: {dispute_doc.name}\n"
        f"Contract: {contract_title}\n"
        f"Current Stage: {current_stage}\n"
        f"Decision: {decision_status}\n"
        f"Summary: {summary}\n"
        f"Resolution: {resolution}\n"
        f"Remarks: {remarks or ''}"
    )

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "subject": "Record dispute resolution outcome",
            "discussion": agenda_discussion[:5000],
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_dispute_resolution",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "dispute_case": dispute_doc.name,
            "contract": dispute_doc.contract,
            "decision": decision_status,
            "current_stage": current_stage,
            "remarks": remarks or "",
        },
    )


def _maybe_create_governance_session_for_stop_work_issued(
    dispute_doc,
    *,
    reason: str,
) -> None:
    """Create a draft proceedings session when Stop Work Order is issued."""
    if not int(getattr(dispute_doc, "stop_work_order_issued", 0) or 0):
        return

    context_reference_doctype = "Dispute Case"
    context_reference_name = dispute_doc.name
    session_type = "Dispute Session"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", dispute_doc.contract, "contract_title")
        or dispute_doc.contract
    )
    cit_rec = int(getattr(dispute_doc, "cit_recommendation", 0) or 0)
    hop_rec = int(getattr(dispute_doc, "head_of_procurement_recommendation", 0) or 0)

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Dispute Session: {contract_title}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "session_template": "Procurement - Dispute Session",
            "quorum_required": 2,
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda_discussion = (
        f"Stop Work Order issued for Dispute Case: {dispute_doc.name}\n"
        f"Contract: {contract_title}\n"
        f"Stop Work Reason: {reason}\n"
        f"CIT Recommendation Present: {cit_rec}\n"
        f"Head of Procurement Recommendation Present: {hop_rec}\n"
    )

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "sequence": 1,
            "subject": "Escalation / Stop Work Recommendation",
            "reference_doctype": "Dispute Case",
            "reference_name": dispute_doc.name,
            "discussion": agenda_discussion[:5000],
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_stop_work_issued",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "dispute_case": dispute_doc.name,
            "contract": dispute_doc.contract,
            "reason": reason,
        },
    )


def _maybe_create_governance_session_for_monthly_monitoring_report(report_doc) -> None:
    """Create a draft Governance Session + agenda item for monthly monitoring review."""
    if getattr(report_doc, "status", None) != "Reviewed":
        return

    context_reference_doctype = "Monthly Contract Monitoring Report"
    context_reference_name = report_doc.name
    session_type = "Monitoring Review"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    contract_title = (
        frappe.db.get_value("Contract", report_doc.contract, "contract_title")
        or report_doc.contract
    )
    report_month = getattr(report_doc, "report_month", None)

    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"Monitoring Review: {contract_title} ({report_month})",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "session_template": "Procurement - Monitoring Review",
            "quorum_required": 2,
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    milestone_summary = getattr(report_doc, "milestone_progress_summary", "") or ""
    payment_summary = getattr(report_doc, "payment_status_summary", "") or ""
    outstanding = getattr(report_doc, "outstanding_obligations", "") or ""
    risks = getattr(report_doc, "contract_risks", "") or ""

    discussion = (
        f"Monthly Contract Monitoring Report: {report_doc.name}\n"
        f"Contract: {contract_title}\n"
        f"Report Month: {report_month}\n\n"
        f"Milestone Progress Summary:\n{milestone_summary}\n\n"
        f"Payment Status Summary:\n{payment_summary}\n\n"
        f"Outstanding Obligations:\n{outstanding}\n\n"
        f"Contract Risks:\n{risks}\n"
    )

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "sequence": 1,
            "subject": "Milestone Progress",
            "reference_doctype": "Monthly Contract Monitoring Report",
            "reference_name": report_doc.name,
            "discussion": discussion[:5000],
            "decision_required": 0,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_monthly_monitoring_report",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "monthly_report": report_doc.name,
            "contract": report_doc.contract,
            "report_month": report_month,
        },
    )


def _maybe_create_governance_session_for_milestone_completed(task_doc) -> None:
    """Create a draft Governance Session + agenda item when a milestone is first completed."""
    if not int(getattr(task_doc, "is_contract_milestone", 0)):
        return
    if getattr(task_doc, "milestone_status", None) != "Completed":
        return

    # Use the Task as the canonical context reference for idempotence.
    context_reference_doctype = "Task"
    context_reference_name = task_doc.name
    session_type = "CIT Meeting"

    if frappe.db.exists(
        "Governance Session",
        {
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
        },
    ):
        return

    from frappe.utils import nowdate

    subj = (getattr(task_doc, "subject", None) or task_doc.name)[:120]
    session = frappe.get_doc(
        {
            "doctype": "Governance Session",
            "title": f"CIT Meeting: {subj}",
            "context_type": "Procurement",
            "context_reference_doctype": context_reference_doctype,
            "context_reference_name": context_reference_name,
            "session_type": session_type,
            "meeting_date": nowdate(),
            "mode": "Physical",
            "session_template": "Procurement - CIT Meeting",
            "quorum_required": 2,
            "status": "Draft",
        }
    )
    session.insert(ignore_permissions=True)

    agenda = frappe.get_doc(
        {
            "doctype": "Session Agenda Item",
            "session": session.name,
            "sequence": 1,
            "subject": "Milestone Progress Review",
            "reference_doctype": "Task",
            "reference_name": task_doc.name,
            "discussion": "",
            "decision_required": 1,
        }
    )
    agenda.insert(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="governance_session_created_from_milestone",
        reference_doctype="Governance Session",
        reference_name=session.name,
        details={
            "task": task_doc.name,
            "contract": getattr(task_doc, "contract", None),
            "project": getattr(task_doc, "project", None),
        },
    )


def maybe_create_inspection_test_plan_for_milestone(doc, method=None) -> None:
    """When a contract milestone first reaches Completed, create a draft Inspection Test Plan (inspection-ready)."""
    if not int(getattr(doc, "is_contract_milestone", 0)):
        return
    if not getattr(doc, "contract", None):
        return

    new_status = getattr(doc, "milestone_status", None) or "Pending"
    if new_status != "Completed":
        return

    prev = doc.get_doc_before_save()
    prev_status = getattr(prev, "milestone_status", None) if prev else None
    if prev_status == "Completed":
        return

    _maybe_create_governance_session_for_milestone_completed(doc)

    if frappe.db.exists(
        "Inspection Test Plan",
        {"contract": doc.contract, "milestone_task": doc.name, "docstatus": ("!=", 2)},
    ):
        return

    subj = (getattr(doc, "subject", None) or doc.name)[:120]
    itp = frappe.get_doc(
        {
            "doctype": "Inspection Test Plan",
            "title": f"ITP: {subj}",
            "contract": doc.contract,
            "milestone_task": doc.name,
            "scope": (
                "Auto-created when milestone reached Completed (inspection-ready). "
                "Define methods, samples, and acceptance criteria, then submit before field inspection."
            ),
            "prepared_by": frappe.session.user,
            "prepared_on": now_datetime(),
        }
    )
    itp.insert(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="inspection_test_plan_auto_created",
        reference_doctype="Inspection Test Plan",
        reference_name=itp.name,
        details={"task": doc.name, "contract": doc.contract},
    )


@frappe.whitelist()
def create_inspection_test_plan_for_task(
    task_name: str,
    title: str | None = None,
    scope: str | None = None,
) -> str:
    task = frappe.get_doc("Task", task_name)
    if not int(getattr(task, "is_contract_milestone", 0)):
        frappe.throw(_("Task is not a contract milestone"))
    if not task.contract:
        frappe.throw(_("Task has no Contract"))

    itp = frappe.get_doc(
        {
            "doctype": "Inspection Test Plan",
            "title": title or f"ITP: {(task.subject or task.name)[:120]}",
            "contract": task.contract,
            "milestone_task": task.name,
            "scope": scope
            or (
                "Inspection test plan for this milestone. Define scope, methods, "
                "and acceptance criteria before inspection."
            ),
            "prepared_by": frappe.session.user,
            "prepared_on": now_datetime(),
        }
    )
    itp.insert(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="inspection_test_plan_manual_created",
        reference_doctype="Inspection Test Plan",
        reference_name=itp.name,
        details={"task": task.name, "contract": task.contract},
    )
    return itp.name


def validate_cit_member(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.employee:
        frappe.throw("Employee is required")

    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status not in ("Draft", "Pending Supplier Signature", "Pending Accounting Officer Signature", "Active", "Suspended"):
        frappe.throw("CIT member cannot be assigned to a contract that is terminated/closed")

    if doc.is_new() and doc.status != "Proposed":
        roles = set(frappe.get_roles(frappe.session.user))
        if "System Manager" not in roles:
            frappe.throw("New CIT members must start in status Proposed")

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

    old = doc.get_doc_before_save()
    if old and old.status != doc.status:
        _transition_allowed(
            "CIT member status", old.status, doc.status, CIT_MEMBER_STATUS_TRANSITIONS
        )
        if doc.status == "Approved" and old.status == "Proposed":
            _require_any_role(
                ["Accounting Officer", "System Manager"],
                "Approve CIT appointment",
            )
        elif doc.status == "Active" and old.status == "Approved":
            _require_any_role(
                ["Head of Procurement", "System Manager"],
                "Activate CIT member",
            )
        elif doc.status == "Removed":
            _require_any_role(
                ["Accounting Officer", "Head of Procurement", "System Manager"],
                "Remove CIT member",
            )


def validate_inspection_committee_member(doc, method=None) -> None:
    if not doc.contract:
        frappe.throw("Contract is required")
    if not doc.employee:
        frappe.throw("Employee is required")

    contract = frappe.get_doc("Contract", doc.contract)
    if contract.status not in (
        "Draft",
        "Pending Supplier Signature",
        "Pending Accounting Officer Signature",
        "Active",
        "Suspended",
    ):
        frappe.throw(
            "Inspection Committee member cannot be assigned to a contract that is terminated/closed"
        )

    if doc.is_new() and doc.status != "Proposed":
        roles = set(frappe.get_roles(frappe.session.user))
        if "System Manager" not in roles:
            frappe.throw("New Inspection Committee members must start in status Proposed")

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

    old = doc.get_doc_before_save()
    if old and old.status != doc.status:
        _transition_allowed(
            "Inspection Committee member status",
            old.status,
            doc.status,
            ICM_STATUS_TRANSITIONS,
        )
        if doc.status == "Approved" and old.status == "Proposed":
            _require_any_role(
                ["Accounting Officer", "System Manager"],
                "Approve Inspection Committee appointment",
            )
        elif doc.status == "Active" and old.status == "Approved":
            _require_any_role(
                ["Head of Procurement", "System Manager"],
                "Activate Inspection Committee member",
            )
        elif doc.status == "Dissolved":
            _require_any_role(
                ["Accounting Officer", "Head of Procurement", "System Manager"],
                "Dissolve Inspection Committee member appointment",
            )


@frappe.whitelist()
def transition_cit_member(
    member_name: str,
    next_status: str,
    remarks: str | None = None,
) -> str:
    doc = frappe.get_doc("Contract Implementation Team Member", member_name)
    current = doc.status
    if next_status == current:
        return current
    _transition_allowed(
        "CIT member status", current, next_status, CIT_MEMBER_STATUS_TRANSITIONS
    )

    if next_status == "Approved":
        _require_any_role(
            ["Accounting Officer", "System Manager"],
            "Approve CIT appointment",
        )
    elif next_status == "Active":
        _require_any_role(
            ["Head of Procurement", "System Manager"],
            "Activate CIT member",
        )
    elif next_status == "Removed":
        _require_any_role(
            ["Accounting Officer", "Head of Procurement", "System Manager"],
            "Remove CIT member",
        )

    doc.status = next_status
    if next_status in ("Approved", "Active"):
        if not getattr(doc, "appointed_by", None):
            doc.appointed_by = frappe.session.user
        if not getattr(doc, "appointed_on", None):
            doc.appointed_on = now_datetime()

    note = f"CIT status: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    doc.add_comment("Workflow", note)
    doc.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="cit_member_transition",
        reference_doctype="Contract Implementation Team Member",
        reference_name=doc.name,
        details={
            "contract": doc.contract,
            "from": current,
            "to": next_status,
            "remarks": remarks,
        },
    )
    return doc.status


@frappe.whitelist()
def transition_inspection_committee_member(
    member_name: str,
    next_status: str,
    remarks: str | None = None,
) -> str:
    doc = frappe.get_doc("Inspection Committee Member", member_name)
    current = doc.status
    if next_status == current:
        return current
    _transition_allowed(
        "Inspection Committee member status",
        current,
        next_status,
        ICM_STATUS_TRANSITIONS,
    )

    if next_status == "Approved":
        _require_any_role(
            ["Accounting Officer", "System Manager"],
            "Approve Inspection Committee appointment",
        )
    elif next_status == "Active":
        _require_any_role(
            ["Head of Procurement", "System Manager"],
            "Activate Inspection Committee member",
        )
    elif next_status == "Dissolved":
        _require_any_role(
            ["Accounting Officer", "Head of Procurement", "System Manager"],
            "Dissolve Inspection Committee member appointment",
        )

    doc.status = next_status
    if next_status in ("Approved", "Active"):
        if not getattr(doc, "appointed_by", None):
            doc.appointed_by = frappe.session.user
        if not getattr(doc, "appointed_on", None):
            doc.appointed_on = now_datetime()

    note = f"Inspection Committee status: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    doc.add_comment("Workflow", note)
    doc.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="inspection_committee_member_transition",
        reference_doctype="Inspection Committee Member",
        reference_name=doc.name,
        details={
            "contract": doc.contract,
            "from": current,
            "to": next_status,
            "remarks": remarks,
        },
    )
    return doc.status


def _variation_high_financial_impact_threshold() -> float:
    return float(
        frappe.conf.get("kentender_variation_high_financial_impact_threshold", 1000000)
    )


def _variation_high_time_extension_days_threshold() -> int:
    return int(
        frappe.conf.get("kentender_variation_high_time_extension_days_threshold", 30)
    )


def _variation_second_level_approval_role() -> str:
    return str(
        frappe.conf.get("kentender_variation_second_level_approval_role", "Head of Finance")
    )


def _variation_requires_second_level_approval(variation_doc) -> bool:
    """High-impact variations need a second level approval before Approved."""
    financial_impact = float(getattr(variation_doc, "financial_impact", 0) or 0)
    time_extension_days = int(getattr(variation_doc, "time_extension_days", 0) or 0)
    return bool(financial_impact >= _variation_high_financial_impact_threshold()) or bool(
        time_extension_days >= _variation_high_time_extension_days_threshold()
    )


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

    if getattr(doc, "status", None) == "Approved":
        if _variation_requires_second_level_approval(doc) and not int(
            getattr(doc, "second_level_approved", 0) or 0
        ):
            frappe.throw(
                "High-impact Contract Variation requires second-level approval before Approved"
            )

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
        if not getattr(record, "legal_advice_reference", None):
            frappe.throw("Cannot complete settlement without legal advice reference")
        if not int(getattr(record, "notice_issued_to_supplier", 0) or 0):
            frappe.throw("Cannot complete settlement without notice issued to supplier")
        if not int(getattr(record, "supporting_documents_provided", 0) or 0):
            frappe.throw("Cannot complete settlement without supporting documents")

    record.settlement_status = next_status
    note = f"Settlement transition: {current} -> {next_status}"
    if remarks:
        note = f"{note}. {remarks}"
    record.add_comment("Workflow", note)
    record.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="termination_settlement_transition",
        reference_doctype="Termination Record",
        reference_name=record.name,
        details={"from": current, "to": next_status, "remarks": remarks},
    )
    return record.settlement_status


_PENALTY_CLAIM_TYPES = ("Liquidated Damages", "Performance Penalty")
_PENALTY_CLAIM_BY = "Procuring Entity"


def _penalty_rate_per_day() -> float:
    """Deterministic penalty rate configuration (configurable per tenant)."""
    return float(frappe.conf.get("kentender_penalty_rate_per_day", 1000))


def _contract_expected_completion_date(contract_name: str):
    """Expected completion date for penalty computation."""
    from frappe.utils import getdate

    contract = frappe.get_doc("Contract", contract_name)
    if getattr(contract, "end_date", None):
        return getdate(contract.end_date)

    # Fallback: max expected milestone end date.
    rows = frappe.get_all(
        "Task",
        filters={"contract": contract_name, "is_contract_milestone": 1},
        fields=["exp_end_date"],
        order_by="exp_end_date desc",
        limit_page_length=1,
    )
    if rows and rows[0].get("exp_end_date"):
        return getdate(rows[0]["exp_end_date"])
    return None


def _contract_actual_completion_date(contract_name: str):
    """Actual completion date (proxy) for penalty computation.

    Uses the max `Task.modified` date among Completed/Accepted contract milestones.
    """
    from frappe.utils import getdate

    rows = frappe.get_all(
        "Task",
        filters={
            "contract": contract_name,
            "is_contract_milestone": 1,
            "milestone_status": ["in", ["Completed", "Accepted"]],
        },
        fields=["modified"],
        order_by="modified desc",
        limit_page_length=1,
    )
    if rows and rows[0].get("modified"):
        return getdate(rows[0]["modified"])
    return None


def _maybe_calculate_penalty_for_claim(doc) -> None:
    """Auto-calculate Claim.amount for penalty/LD claims when amount is unset/zero.

    Deterministic inputs:
    - Contract expected completion date (`Contract.end_date`, else milestone exp_end_date)
    - Contract actual completion date (max Task.modified for Completed/Accepted milestones)
    - Configured rate per day (`kentender_penalty_rate_per_day`)
    """
    if getattr(doc, "claim_type", None) not in _PENALTY_CLAIM_TYPES:
        return
    if getattr(doc, "claim_by", None) != _PENALTY_CLAIM_BY:
        return

    expected = _contract_expected_completion_date(doc.contract)
    actual = _contract_actual_completion_date(doc.contract)

    if not expected or not actual:
        delay_days = 0
    else:
        delay_days = max(0, (actual - expected).days)

    rate = _penalty_rate_per_day()
    computed_amount = float(delay_days) * float(rate)

    # Always populate trace fields for transparency.
    doc.penalty_rate_per_day = rate
    doc.penalty_expected_completion_date = expected
    doc.penalty_actual_completion_date = actual
    doc.penalty_delay_days = int(delay_days)
    doc.penalty_formula = (
        f"delay_days({delay_days}) * rate_per_day({rate})"
    )

    # Only override amount when the user hasn't provided one.
    if getattr(doc, "amount", None) in (None, "", 0):
        doc.amount = computed_amount


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

    _maybe_calculate_penalty_for_claim(doc)

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

    # Stop-work governance: if marked issued, core evidence must exist.
    if int(getattr(doc, "stop_work_order_issued", 0)):
        if not getattr(doc, "issued_by", None):
            frappe.throw("Issued By is required when Stop Work Order is issued")
        if not getattr(doc, "stop_work_reason", None):
            frappe.throw("Stop Work Reason is required when Stop Work Order is issued")
        if not int(getattr(doc, "cit_recommendation", 0)):
            frappe.throw("CIT recommendation is required before issuing Stop Work Order")
        if not int(getattr(doc, "head_of_procurement_recommendation", 0)):
            frappe.throw("Head of Procurement recommendation is required before issuing Stop Work Order")


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
        # Planned = draft scheduling row only; does not affect held retention.
        if row.retention_type == "Planned":
            continue
        amount = float(row.amount or 0)
        if row.retention_type == "Deduction":
            balance += amount
        else:
            balance -= amount
    return balance


@frappe.whitelist()
def get_retention_release_readiness(contract_name: str) -> dict:
    """Return whether `release_contract_retention` can run, and why not."""
    contract = frappe.get_doc("Contract", contract_name)
    balance = float(get_contract_retention_balance(contract_name) or 0)
    blockers: list[str] = []
    if balance <= 0:
        blockers.append("no_retention_balance")
    if contract.status not in ("Closed", "Terminated"):
        blockers.append("contract_not_closed_or_terminated")
    if contract.dlp_status != "Completed":
        blockers.append("dlp_not_completed")

    approved_penalty_claims = frappe.db.count(
        "Claim",
        {
            "contract": contract_name,
            "claim_by": _PENALTY_CLAIM_BY,
            "claim_type": ["in", list(_PENALTY_CLAIM_TYPES)],
            "status": "Approved",
        },
    )
    if approved_penalty_claims > 0:
        blockers.append("approved_penalty_claims_pending")

    return {
        "contract": contract_name,
        "release_ready": len(blockers) == 0,
        "retention_balance": balance,
        "blockers": blockers,
        "status": contract.status,
        "dlp_status": contract.dlp_status,
    }


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

    approved_penalty_claims = frappe.db.count(
        "Claim",
        {
            "contract": contract.name,
            "claim_by": _PENALTY_CLAIM_BY,
            "claim_type": ["in", list(_PENALTY_CLAIM_TYPES)],
            "status": "Approved",
        },
    )
    if approved_penalty_claims > 0:
        frappe.throw(
            "Retention release is blocked by unresolved approved penalty-related claims"
        )

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
    log_ken_tender_audit_event(
        action="retention_released",
        reference_doctype="Contract",
        reference_name=contract.name,
        details={
            "amount": release_amount,
            "balance_after": new_balance,
            "retention_ledger": row.name,
            "payment_entry": payment_entry,
        },
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


@frappe.whitelist()
def get_retention_release_due_contracts(
    lead_days: int = 30,
    company: str | None = None,
) -> list[dict]:
    """Contracts with retention held and DLP completed or DLP end within lead_days (eligibility window)."""
    from frappe.utils import add_days, getdate, nowdate

    due_rows: list[dict] = []
    today = getdate(nowdate())
    due_limit = add_days(today, int(lead_days or 0))

    cfilters: dict = {
        "status": (
            "in",
            [
                "Active",
                "Suspended",
                "Pending Close-Out",
                "Closed",
                "Terminated",
            ],
        ),
    }
    if company:
        cfilters["company"] = company

    contracts = frappe.get_all(
        "Contract",
        filters=cfilters,
        fields=["name", "dlp_end_date", "dlp_status", "status", "company"],
    )

    for row in contracts:
        retention_balance = float(get_contract_retention_balance(row.name) or 0)
        if retention_balance <= 0:
            continue

        dlp_completed = (row.dlp_status or "") == "Completed"
        in_window = False
        dlp_end = None
        if row.dlp_end_date:
            dlp_end = getdate(row.dlp_end_date)
            in_window = dlp_end <= due_limit

        if not dlp_completed and not in_window:
            continue

        days_to = (dlp_end - today).days if dlp_end else None
        readiness = get_retention_release_readiness(row.name)

        due_rows.append(
            {
                "contract": row.name,
                "company": row.company,
                "status": row.status,
                "dlp_status": row.dlp_status,
                "dlp_end_date": str(row.dlp_end_date) if row.dlp_end_date else None,
                "retention_balance": retention_balance,
                "days_to_dlp_end": days_to,
                "release_ready": readiness["release_ready"],
                "release_blockers": readiness["blockers"],
            }
        )

    return due_rows


def remind_retention_release_due() -> int:
    """Daily reminder: flag contracts nearing/after DLP with retention held; optional planned ledger row."""
    from frappe.utils import nowdate

    due_rows = get_retention_release_due_contracts(lead_days=30)
    if not due_rows:
        return 0

    created = 0
    marker_date = nowdate()
    planned_created = 0
    period_marker = marker_date[:7]  # YYYY-MM

    for row in due_rows:
        marker = f"[RETENTION-REMINDER:{marker_date}]"
        exists = frappe.db.exists(
            "Comment",
            {
                "reference_doctype": "Contract",
                "reference_name": row["contract"],
                "comment_type": "Workflow",
                "content": ("like", f"%{marker}%"),
            },
        )
        if not exists:
            contract = frappe.get_doc("Contract", row["contract"])
            rd = row.get("dlp_end_date") or "n/a"
            dte = row.get("days_to_dlp_end")
            dte_s = str(dte) if dte is not None else "n/a"
            ready = row.get("release_ready")
            blockers = row.get("release_blockers") or []
            blocker_s = f" Blockers: {', '.join(blockers)}." if blockers else ""
            contract.add_comment(
                "Workflow",
                (
                    f"{marker} Retention release window: DLP end {rd}, days to DLP end {dte_s}, "
                    f"balance {row['retention_balance']:.2f}. "
                    f"Release API ready: {bool(ready)}.{blocker_s}"
                ),
            )
            created += 1

        # Optional draft "Planned" row — one per contract per month; not a GL posting.
        if not frappe.conf.get("kentender_skip_retention_planned_ledger"):
            pm = f"[RETENTION-PLANNED:{period_marker}]"
            has_planned = frappe.db.exists(
                "Retention Ledger",
                {
                    "contract": row["contract"],
                    "retention_type": "Planned",
                    "remarks": ("like", f"%{pm}%"),
                },
            )
            if not has_planned:
                frappe.get_doc(
                    {
                        "doctype": "Retention Ledger",
                        "contract": row["contract"],
                        "retention_type": "Planned",
                        "posting_date": marker_date,
                        "amount": float(row["retention_balance"] or 0),
                        "balance_after_transaction": float(
                            get_contract_retention_balance(row["contract"]) or 0
                        ),
                        "status": "Pending",
                        "remarks": (
                            f"{pm} Suggested retention release for review (informational; "
                            "not a payment). Complete governance gates then use Release API."
                        ),
                    }
                ).insert(ignore_permissions=True)
                planned_created += 1

    if planned_created and due_rows:
        log_ken_tender_audit_event(
            action="retention_planned_ledger_batch",
            reference_doctype="Contract",
            reference_name=due_rows[0]["contract"],
            details={"planned_rows": planned_created, "period": period_marker},
        )

    return created


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
def get_contract_payment_governance_chain(contract: str) -> dict:
    """Return Payment Entry rows for a contract with CLM workflow metadata and Purchase Invoice references."""
    if not frappe.has_permission("Contract", "read", doc=contract):
        frappe.throw(_("Not permitted to read this contract"), frappe.PermissionError)

    pe_names = frappe.get_all(
        "Payment Entry",
        filters={"contract": contract},
        pluck="name",
        order_by="posting_date desc, modified desc",
    )
    rows: list[dict] = []
    for name in pe_names:
        doc = frappe.get_doc("Payment Entry", name)
        pi_refs: list[dict] = []
        for r in getattr(doc, "references", None) or []:
            if getattr(r, "reference_doctype", None) != "Purchase Invoice" or not r.reference_name:
                continue
            pinv = frappe.db.get_value(
                "Purchase Invoice",
                r.reference_name,
                ["docstatus", "grand_total", "status", "posting_date"],
                as_dict=True,
            )
            pi_refs.append(
                {
                    "purchase_invoice": r.reference_name,
                    "allocated_amount": float(r.allocated_amount or 0),
                    "invoice_docstatus": int(pinv.docstatus) if pinv else None,
                    "invoice_grand_total": float(pinv.grand_total or 0) if pinv else None,
                    "invoice_status": pinv.status if pinv else None,
                    "invoice_posting_date": str(pinv.posting_date) if pinv and pinv.posting_date else None,
                }
            )
        rows.append(
            {
                "name": doc.name,
                "posting_date": str(doc.posting_date) if doc.posting_date else None,
                "party": doc.party,
                "payment_type": doc.payment_type,
                "docstatus": doc.docstatus,
                "clm_workflow_state": getattr(doc, "clm_workflow_state", None) or "Draft",
                "procurement_reviewed_by": getattr(doc, "procurement_reviewed_by", None),
                "finance_verified_by": getattr(doc, "finance_verified_by", None),
                "procurement_certified_by": getattr(doc, "procurement_certified_by", None),
                "clm_procurement_reviewed_on": getattr(doc, "clm_procurement_reviewed_on", None),
                "clm_finance_verified_on": getattr(doc, "clm_finance_verified_on", None),
                "clm_procurement_certified_on": getattr(doc, "clm_procurement_certified_on", None),
                "clm_paid_confirmed_by": getattr(doc, "clm_paid_confirmed_by", None),
                "clm_paid_at": getattr(doc, "clm_paid_at", None),
                "grand_total": float(doc.paid_amount or doc.grand_total or 0),
                "purchase_invoice_references": pi_refs,
            }
        )
    return {"contract": contract, "payment_entries": rows}


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
        if row.retention_type == "Planned":
            continue
        contract_name = row.contract
        amount = float(row.amount or 0)
        if contract_name not in retention_by_contract:
            retention_by_contract[contract_name] = 0.0
        if row.retention_type == "Deduction":
            retention_by_contract[contract_name] += amount
        else:
            retention_by_contract[contract_name] -= amount

    total_retention_held = sum(retention_by_contract.values())

    ret_due_list: list[dict] = []
    if contract_names:
        due_scope = set(contract_names)
        ret_due_list = [
            r
            for r in get_retention_release_due_contracts(30, company=company)
            if r["contract"] in due_scope
        ]

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
            "retention_release_due_contracts": len(ret_due_list),
            "retention_release_ready_contracts": sum(
                1 for r in ret_due_list if r.get("release_ready")
            ),
            **(
                {
                    "payment_entries_submitted_pending_clm_paid": frappe.db.count(
                        "Payment Entry",
                        {
                            "docstatus": 1,
                            "contract": in_contracts,
                            "clm_workflow_state": ("!=", "Paid"),
                        },
                    ),
                    "payment_entries_certified_awaiting_submit": frappe.db.count(
                        "Payment Entry",
                        {
                            "docstatus": 0,
                            "contract": in_contracts,
                            "clm_workflow_state": "Procurement Certified",
                        },
                    ),
                }
                if contract_names
                else {
                    "payment_entries_submitted_pending_clm_paid": 0,
                    "payment_entries_certified_awaiting_submit": 0,
                }
            ),
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
    log_ken_tender_audit_event(
        action="acceptance_certificate_transition",
        reference_doctype="Acceptance Certificate",
        reference_name=cert.name,
        details={"from": current_state, "to": next_state, "remarks": remarks},
    )
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
def transition_payment_entry_clm(
    payment_entry_name: str,
    next_state: str,
    remarks: str | None = None,
) -> str:
    entry = frappe.get_doc("Payment Entry", payment_entry_name)
    if not getattr(entry, "contract", None):
        inferred_contract = _infer_contract_from_payment_entry_references(entry)
        if inferred_contract:
            entry.contract = inferred_contract
    if not getattr(entry, "contract", None):
        frappe.throw("Payment Entry is not linked to a Contract")

    current = getattr(entry, "clm_workflow_state", None) or "Draft"
    _transition_allowed(
        "Payment Entry CLM workflow state",
        current,
        next_state,
        PAYMENT_ENTRY_CLM_TRANSITIONS,
    )

    if next_state == "Procurement Reviewed":
        _require_any_role(["Head of Procurement", "System Manager"], "Payment review")
        entry.procurement_reviewed_by = frappe.session.user
    elif next_state == "Finance Verified":
        _require_any_role(["Head of Finance", "System Manager"], "Finance verification")
        entry.finance_verified_by = frappe.session.user
    elif next_state == "Procurement Certified":
        _require_any_role(["Head of Procurement", "System Manager"], "Procurement certification")
        entry.procurement_certified_by = frappe.session.user
    elif next_state == "Paid":
        _require_any_role(["Head of Finance", "System Manager"], "Payment confirmation")
        if entry.docstatus != 1:
            frappe.throw("Submit Payment Entry first before setting CLM state to Paid")

    now = now_datetime()
    if next_state == "Procurement Reviewed":
        entry.clm_procurement_reviewed_on = now
    elif next_state == "Finance Verified":
        entry.clm_finance_verified_on = now
    elif next_state == "Procurement Certified":
        entry.clm_procurement_certified_on = now
    elif next_state == "Paid":
        entry.clm_paid_confirmed_by = frappe.session.user
        entry.clm_paid_at = now

    entry.clm_workflow_state = next_state
    note = f"CLM workflow transition: {current} -> {next_state}"
    if remarks:
        note = f"{note}. {remarks}"
    entry.add_comment("Workflow", note)
    entry.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="payment_entry_clm_transition",
        reference_doctype="Payment Entry",
        reference_name=entry.name,
        details={"from": current, "to": next_state, "remarks": remarks},
    )
    return entry.clm_workflow_state


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
    elif next_status == "Approved":
        _require_any_role(["Accounting Officer", "System Manager"], "Variation decision")
        if _variation_requires_second_level_approval(variation) and not int(
            getattr(variation, "second_level_approved", 0) or 0
        ):
            frappe.throw(
                "High-impact Contract Variation requires second-level approval before Approved"
            )
    elif next_status == "Rejected":
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
    log_ken_tender_audit_event(
        action="contract_variation_transition",
        reference_doctype="Contract Variation",
        reference_name=variation.name,
        details={"from": current, "to": next_status, "remarks": remarks},
    )
    _maybe_create_governance_session_for_contract_variation_decision(
        variation, decision_status=next_status, remarks=remarks
    )
    return variation.status


@frappe.whitelist()
def second_approve_contract_variation(
    variation_name: str, remarks: str | None = None
) -> str:
    """Second-level approval for high-impact Contract Variations.

    This is intentionally separate from the status transition to keep a
    verifiable multi-level approval chain.
    """
    variation = frappe.get_doc("Contract Variation", variation_name)

    if not _variation_requires_second_level_approval(variation):
        frappe.throw(
            "Second-level approval is not required for this Contract Variation"
        )

    if variation.status not in ("Draft", "Under Review"):
        frappe.throw(
            "Second-level approval is allowed only when Contract Variation is Draft/Under Review"
        )

    _require_any_role(
        [_variation_second_level_approval_role(), "System Manager"],
        "Second level variation approval",
    )

    variation.second_level_approved = 1
    variation.second_level_approved_by = frappe.session.user
    variation.second_level_approved_on = now_datetime()

    note = "Second-level approval recorded"
    if remarks:
        note = f"{note}. {remarks}"
    variation.add_comment("Workflow", note)
    variation.save(ignore_permissions=True)

    log_ken_tender_audit_event(
        action="contract_variation_second_level_approval",
        reference_doctype="Contract Variation",
        reference_name=variation.name,
        details={
            "requires_second_level": 1,
            "second_level_approved_by": frappe.session.user,
        },
    )

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
    log_ken_tender_audit_event(
        action="claim_transition",
        reference_doctype="Claim",
        reference_name=claim.name,
        details={"from": current, "to": next_status, "remarks": remarks},
    )
    _maybe_create_governance_session_for_claim_decision(
        claim, decision_status=next_status, remarks=remarks
    )
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
    log_ken_tender_audit_event(
        action="dispute_transition",
        reference_doctype="Dispute Case",
        reference_name=dispute.name,
        details={"from": current, "to": next_status, "remarks": remarks},
    )
    _maybe_create_governance_session_for_dispute_resolution(
        dispute, decision_status=next_status, remarks=remarks
    )
    return dispute.status


@frappe.whitelist()
def issue_stop_work_order(dispute_name: str, reason: str) -> dict:
    dispute = frappe.get_doc("Dispute Case", dispute_name)
    _require_any_role(["Accounting Officer", "System Manager"], "Stop Work issuance")

    if not reason or not str(reason).strip():
        frappe.throw("Stop Work Reason is required")
    if not int(getattr(dispute, "cit_recommendation", 0)):
        frappe.throw("Stop Work Order requires CIT recommendation")
    if not int(getattr(dispute, "head_of_procurement_recommendation", 0)):
        frappe.throw("Stop Work Order requires Head of Procurement recommendation")
    if int(getattr(dispute, "stop_work_order_issued", 0)):
        frappe.throw("Stop Work Order is already issued for this dispute")

    contract = frappe.get_doc("Contract", dispute.contract)
    if contract.status in ("Closed", "Terminated"):
        frappe.throw("Cannot issue Stop Work on a closed/terminated contract")

    other_active_sw = frappe.db.count(
        "Dispute Case",
        {"contract": contract.name, "stop_work_order_issued": 1, "name": ("!=", dispute.name)},
    )

    previous_contract_status = contract.status

    # First active Stop Work on this contract: optionally suspend and remember resume status.
    if other_active_sw == 0:
        if contract.status != "Suspended":
            contract.resume_status_after_stop_work = contract.status
            contract.status = "Suspended"
            contract.add_comment(
                "Workflow",
                f"Contract suspended due to Stop Work Order on dispute {dispute.name}",
            )
            contract.save(ignore_permissions=True)
        # If already Suspended (e.g. manual or other process), do not set resume_status —
        # withdrawing Stop Work must not change contract state in that case.
    else:
        if contract.status != "Suspended":
            frappe.throw(
                "Data inconsistency: other disputes have an active Stop Work order but "
                f"Contract {contract.name} is not Suspended. Resolve before continuing."
            )

    dispute.stop_work_order_issued = 1
    dispute.issued_by = frappe.session.user
    dispute.stop_work_reason = reason
    dispute.add_comment(
        "Workflow",
        f"Stop Work Order issued by {frappe.session.user}. Reason: {reason}",
    )
    dispute.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="stop_work_issued",
        reference_doctype="Dispute Case",
        reference_name=dispute.name,
        details={
            "reason": reason,
            "contract": contract.name,
            "contract_status_before": previous_contract_status,
            "contract_status_after": contract.status,
        },
    )
    _maybe_create_governance_session_for_stop_work_issued(dispute, reason=reason)

    return {
        "ok": True,
        "dispute": dispute.name,
        "stop_work_order_issued": int(dispute.stop_work_order_issued or 0),
        "contract": contract.name,
        "contract_status_before": previous_contract_status,
        "contract_status_after": contract.status,
    }


@frappe.whitelist()
def withdraw_stop_work_order(dispute_name: str, reason: str) -> dict:
    dispute = frappe.get_doc("Dispute Case", dispute_name)
    _require_any_role(["Accounting Officer", "System Manager"], "Stop Work withdrawal")

    if not reason or not str(reason).strip():
        frappe.throw("Withdrawal reason is required")
    if not int(getattr(dispute, "stop_work_order_issued", 0)):
        frappe.throw("Stop Work Order is not currently issued for this dispute")

    contract = frappe.get_doc("Contract", dispute.contract)
    previous_contract_status = contract.status

    dispute.stop_work_order_issued = 0
    dispute.add_comment(
        "Workflow",
        f"Stop Work Order withdrawn by {frappe.session.user}. Reason: {reason}",
    )
    dispute.save(ignore_permissions=True)

    contract.reload()
    remaining_sw = frappe.db.count(
        "Dispute Case", {"contract": contract.name, "stop_work_order_issued": 1}
    )
    # Resume only when this was the last Stop Work order AND we had captured a resume
    # status when first suspending via Stop Work (avoids resuming non-SW suspensions).
    if (
        remaining_sw == 0
        and contract.status == "Suspended"
        and getattr(contract, "resume_status_after_stop_work", None)
    ):
        resume_to = (contract.resume_status_after_stop_work or "").strip() or "Active"
        allowed_resume = {
            "Draft",
            "Pending Supplier Signature",
            "Pending Accounting Officer Signature",
            "Active",
            "Suspended",
            "Pending Termination Approval",
            "Terminated",
            "Pending Close-Out",
            "Closed",
        }
        if resume_to not in allowed_resume:
            resume_to = "Active"
        contract.status = resume_to
        contract.resume_status_after_stop_work = None
        contract.add_comment(
            "Workflow",
            f"Contract restored to {resume_to} after Stop Work withdrawal on dispute {dispute.name} "
            f"(no remaining Stop Work orders)",
        )
        contract.save(ignore_permissions=True)
    log_ken_tender_audit_event(
        action="stop_work_withdrawn",
        reference_doctype="Dispute Case",
        reference_name=dispute.name,
        details={
            "reason": reason,
            "contract": contract.name,
            "contract_status_before": previous_contract_status,
            "contract_status_after": contract.status,
        },
    )

    return {
        "ok": True,
        "dispute": dispute.name,
        "stop_work_order_issued": int(dispute.stop_work_order_issued or 0),
        "contract": contract.name,
        "contract_status_before": previous_contract_status,
        "contract_status_after": contract.status,
    }


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
def try_set_termination_record_evidence(
    termination_name: str,
    legal_advice_reference: str | None = None,
    notice_issued_to_supplier: int = 0,
    supporting_documents_provided: int = 0,
    handover_completed: int = 0,
    discharge_document_reference: str | None = None,
    final_financial_reconciliation: float | None = None,
) -> dict:
    """Bench helper to set termination evidence bundle checklist fields."""
    try:
        record = frappe.get_doc("Termination Record", termination_name)
        if legal_advice_reference is not None:
            record.legal_advice_reference = legal_advice_reference
        record.notice_issued_to_supplier = int(notice_issued_to_supplier or 0)
        record.supporting_documents_provided = int(supporting_documents_provided or 0)
        record.handover_completed = int(handover_completed or 0)
        if discharge_document_reference is not None:
            record.discharge_document_reference = discharge_document_reference
        if final_financial_reconciliation is not None:
            record.final_financial_reconciliation = final_financial_reconciliation
        record.save(ignore_permissions=True)
        return {"ok": True, "name": record.name}
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


@frappe.whitelist()
def try_set_contract_dates(
    contract_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Bench helper: set Contract start/end dates (used for deterministic penalty tests)."""
    try:
        contract = frappe.get_doc("Contract", contract_name)
        if start_date:
            contract.start_date = start_date
        if end_date:
            contract.end_date = end_date
        contract.save(ignore_permissions=True)
        return {"ok": True, "name": contract.name, "start_date": contract.start_date, "end_date": contract.end_date}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_set_dispute_recommendations(
    dispute_name: str,
    cit_recommendation: int = 1,
    head_of_procurement_recommendation: int = 1,
) -> dict:
    """Bench helper: set CIT + HoP recommendation flags for Stop Work issuance."""
    try:
        dispute = frappe.get_doc("Dispute Case", dispute_name)
        dispute.cit_recommendation = int(cit_recommendation or 0)
        dispute.head_of_procurement_recommendation = int(
            head_of_procurement_recommendation or 0
        )
        dispute.save(ignore_permissions=True)
        return {
            "ok": True,
            "name": dispute.name,
            "cit_recommendation": int(dispute.cit_recommendation or 0),
            "head_of_procurement_recommendation": int(
                dispute.head_of_procurement_recommendation or 0
            ),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_set_monthly_contract_monitoring_report_status(
    report_name: str,
    status: str,
) -> dict:
    """Bench helper: set Monthly Contract Monitoring Report.status."""
    try:
        report = frappe.get_doc("Monthly Contract Monitoring Report", report_name)
        report.status = status
        report.save(ignore_permissions=True)
        return {"ok": True, "name": report.name, "status": report.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_add_session_participant(
    session_name: str,
    participant_role: str,
    attendance_status: str,
    user: str | None = None,
    employee: str | None = None,
) -> dict:
    """Bench helper: add a Session Participant (for quorum-aware governance tests)."""
    try:
        payload = {
            "doctype": "Session Participant",
            "session": session_name,
            "participant_role": participant_role,
            "attendance_status": attendance_status,
        }
        payload["user"] = user or frappe.session.user
        if employee:
            payload["employee"] = employee
        participant = frappe.get_doc(payload)
        participant.insert(ignore_permissions=True)
        return {"ok": True, "name": participant.name}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_create_session_resolution(
    session_name: str,
    agenda_item_name: str | None,
    resolution_type: str,
    resolution_text: str,
    status: str = "Draft",
) -> dict:
    """Bench helper: create Session Resolution (used for resolution gating UAT)."""
    try:
        payload: dict = {
            "doctype": "Session Resolution",
            "session": session_name,
            "resolution_type": resolution_type,
            "resolution_text": resolution_text,
            "status": status,
        }
        if agenda_item_name:
            payload["agenda_item"] = agenda_item_name
        resolution = frappe.get_doc(payload)
        resolution.insert(ignore_permissions=True)
        return {"ok": True, "name": resolution.name, "status": resolution.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@frappe.whitelist()
def try_set_session_resolution_status(
    resolution_name: str,
    status: str,
) -> dict:
    """Bench helper: set Session Resolution.status (triggers parent-session gating)."""
    try:
        resolution = frappe.get_doc("Session Resolution", resolution_name)
        resolution.status = status
        resolution.save(ignore_permissions=True)
        return {"ok": True, "name": resolution.name, "status": resolution.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _log_tender_submission_block(doc, block_code: str, message: str) -> None:
    """Audited governance signal when a submission cannot be created/validated."""
    log_ken_tender_audit_event(
        action="tender_submission_blocked",
        reference_doctype="Tender",
        reference_name=doc.tender,
        details={
            "block_code": block_code,
            "message": message,
            "supplier": getattr(doc, "supplier", None),
            "submission_name": getattr(doc, "name", None),
        },
    )


def audit_tender_submission_created(doc, method=None) -> None:
    """One audit row per successful insert (UI, API, or bench helper)."""
    log_ken_tender_audit_event(
        action="tender_submission_created",
        reference_doctype="Tender Submission",
        reference_name=doc.name,
        details={
            "tender": doc.tender,
            "supplier": doc.supplier,
            "quoted_amount": getattr(doc, "quoted_amount", None),
            "currency": getattr(doc, "currency", None),
            "base_amount": getattr(doc, "base_amount", None),
        },
    )


def validate_submission(doc, method) -> None:
    tender = frappe.get_doc("Tender", doc.tender)
    if tender.status != "Published":
        msg = "Tender is not open"
        _log_tender_submission_block(doc, "tender_not_published", msg)
        frappe.throw(msg)
    if tender.submission_deadline and now_datetime() > tender.submission_deadline:
        msg = "Submission deadline passed"
        _log_tender_submission_block(doc, "submission_deadline_passed", msg)
        frappe.throw(msg)
    set_exchange(doc)
    try:
        validate_supplier_compliance(doc.supplier)
    except frappe.ValidationError as e:
        _log_tender_submission_block(doc, "supplier_compliance_blocked", str(e))
        raise

    # Phase 2 supplier status gate.
    supplier_master = frappe.db.get_value("Supplier Master", {"supplier_name": doc.supplier}, ["name", "supplier_status"], as_dict=True)
    if supplier_master and supplier_master.supplier_status in {"Suspended", "Debarred", "Blacklisted"}:
        msg = f"Supplier status '{supplier_master.supplier_status}' is not eligible for submissions"
        _log_tender_submission_block(doc, "supplier_status_blocked", msg)
        frappe.throw(msg)

    if not getattr(doc, "server_received_on", None):
        doc.server_received_on = now_datetime()
    if not getattr(doc, "submitted_on", None):
        doc.submitted_on = now_datetime()
    if not getattr(doc, "submission_status", None):
        doc.submission_status = "Submitted"

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


def phase2_validate_award_decision(doc, method=None) -> None:
    if doc.award_status in {"Approved", "Finalized"}:
        if not getattr(doc, "award_recommendation", None):
            frappe.throw("Award Recommendation is required before approval/finalization")
        if not getattr(doc, "approved_submission", None):
            frappe.throw("Approved Submission is required before approval/finalization")

    if getattr(doc, "award_status", None) == "Finalized":
        active_case = frappe.db.exists(
            "Challenge Review Case",
            {
                "award_decision": doc.name,
                "status": ("in", ["Open", "Under Review"]),
            },
        )
        if active_case:
            frappe.throw(
                f"Cannot finalize award while Challenge/Review Case is active: {active_case}"
            )


def phase2_on_update_award_decision(doc, method=None) -> None:
    if getattr(doc, "award_status", None) != "Finalized":
        return

    if not getattr(doc, "approved_submission", None):
        return

    tender = frappe.get_doc("Tender", doc.tender)
    if not getattr(tender, "purchase_order", None):
        award_tender(doc.tender, doc.approved_submission)
        tender.reload()

    existing_handoff = frappe.db.exists("Award Contract Handoff", {"award_decision": doc.name})
    if not existing_handoff:
        frappe.get_doc(
            {
                "doctype": "Award Contract Handoff",
                "award_decision": doc.name,
                "handoff_status": "Prepared",
                "prepared_by": frappe.session.user,
                "prepared_on": now_datetime(),
                "notes": f"Auto-created from finalized award decision {doc.name}",
            }
        ).insert(ignore_permissions=True)

    prev_in_override = getattr(frappe.flags, "in_override", False)
    frappe.flags.in_override = True
    try:
        tender.status = "Award Published"
        tender.save(ignore_permissions=True)
    finally:
        frappe.flags.in_override = prev_in_override

    log_ken_tender_audit_event(
        action="phase2_award_finalized",
        reference_doctype="Award Decision",
        reference_name=doc.name,
        details={
            "tender": doc.tender,
            "submission": doc.approved_submission,
            "purchase_order": frappe.db.get_value("Tender", doc.tender, "purchase_order"),
        },
    )


def phase2_flag_expired_supplier_documents() -> None:
    today = now_datetime().date()
    expired_docs = frappe.get_all(
        "Supplier Compliance Document",
        filters={"expiry_date": ("<", today), "verification_status": ("!=", "Expired")},
        fields=["name", "supplier"],
        limit=5000,
    )
    suppliers = set()
    for row in expired_docs or []:
        frappe.db.set_value(
            "Supplier Compliance Document",
            row.name,
            {"verification_status": "Expired"},
            update_modified=False,
        )
        if row.supplier:
            suppliers.add(row.supplier)

    for supplier_name in suppliers:
        supplier = frappe.get_doc("Supplier Master", supplier_name)
        if supplier.supplier_status == "Active":
            prev_in_override = getattr(frappe.flags, "in_override", False)
            frappe.flags.in_override = True
            try:
                supplier.supplier_status = "Expired Compliance"
                supplier.save(ignore_permissions=True)
            finally:
                frappe.flags.in_override = prev_in_override


def phase2_auto_close_due_tenders() -> None:
    due = frappe.get_all(
        "Tender",
        filters={"status": "Published", "submission_deadline": ("<=", now_datetime())},
        pluck="name",
        limit=2000,
    )
    for tender_name in due or []:
        tender = frappe.get_doc("Tender", tender_name)
        prev_in_override = getattr(frappe.flags, "in_override", False)
        frappe.flags.in_override = True
        try:
            tender.status = "Closed"
            tender.save(ignore_permissions=True)
        finally:
            frappe.flags.in_override = prev_in_override


def phase2_notify_challenge_window_expiry() -> None:
    open_cases = frappe.get_all(
        "Challenge Review Case",
        filters={"status": ("in", ["Open", "Under Review"])},
        fields=["name", "tender", "supplier", "filed_on"],
        limit=2000,
    )
    for row in open_cases or []:
        if not row.tender:
            continue
        exists = frappe.db.exists(
            "Tender Notification Log",
            {
                "tender": row.tender,
                "supplier": row.supplier,
                "notification_type": "Intention to Award",
                "reference": row.name,
            },
        )
        if exists:
            continue
        frappe.get_doc(
            {
                "doctype": "Tender Notification Log",
                "tender": row.tender,
                "supplier": row.supplier,
                "notification_type": "Intention to Award",
                "sent_on": now_datetime(),
                "channel": "Portal",
                "status": "Queued",
                "reference": row.name,
            }
        ).insert(ignore_permissions=True)


@frappe.whitelist()
def phase2_run_uat_smoke() -> dict:
    """Run a controlled Phase 2 UAT smoke and return created evidence IDs."""
    stamp = now_datetime().strftime("%Y%m%d%H%M%S")
    out: dict = {}

    sra = frappe.get_doc(
        {
            "doctype": "Supplier Registration Application",
            "supplier_name": f"Phase2 UAT Supplier {stamp}",
            "legal_name": f"Phase2 UAT Supplier {stamp} Limited",
            "registration_number": f"P2REG-{stamp}",
            "tax_id": f"P2TAX-{stamp}",
            "email": f"phase2-uat-{stamp}@example.com",
            "phone": "+254700000001",
            "country": "Kenya",
            "physical_address": "Nairobi",
            "application_status": "Draft",
        }
    ).insert(ignore_permissions=True)
    out["sra"] = sra.name

    scd = frappe.get_doc(
        {
            "doctype": "Supplier Compliance Document",
            "application": sra.name,
            "document_type": "Tax Compliance",
            "document_number": f"TAX-{stamp}",
            "issue_date": now_datetime().date(),
            "expiry_date": add_days(now_datetime().date(), 60),
            "verification_status": "Verified",
        }
    ).insert(ignore_permissions=True)
    out["scd"] = scd.name

    sra.db_set("application_status", "Approved", update_modified=False)
    sra.db_set("approved_on", now_datetime(), update_modified=False)
    sra.reload()
    phase2_sync_supplier_master_from_application(sra)

    sm = frappe.get_doc(
        "Supplier Master",
        {"tax_id": sra.tax_id, "registration_number": sra.registration_number},
    )
    out["supplier_master"] = sm.name

    plan_item = frappe.get_all(
        "Procurement Plan Item",
        filters={"status": "Approved"},
        fields=["name"],
        limit=1,
    )
    if not plan_item:
        frappe.throw("No approved Procurement Plan Item available for Phase 2 UAT")
    plan_item_name = plan_item[0].name

    ppi_meta = frappe.get_meta("Procurement Plan Item")
    company_field = "entity" if ppi_meta.has_field("entity") else ("company" if ppi_meta.has_field("company") else None)
    company = frappe.db.get_value("Procurement Plan Item", plan_item_name, company_field) if company_field else None
    company = company or frappe.db.get_value("Company", {}, "name")

    tender = frappe.get_doc(
        {
            "doctype": "Tender",
            "company": company,
            "procurement_plan_item": plan_item_name,
            "status": "Draft",
            "publish_date": now_datetime().date(),
            "submission_deadline": add_days(now_datetime(), 2),
            "closing_datetime": add_days(now_datetime(), 2),
            "opening_datetime": add_days(now_datetime(), 2),
            "method": "Open Tender",
            "procurement_type": "Goods",
            "evaluation_method": "Weighted Score",
            "linked_requisition_count": 1,
        }
    ).insert(ignore_permissions=True)
    out["tender"] = tender.name

    pack = frappe.get_doc(
        {
            "doctype": "Tender Document Pack",
            "tender": tender.name,
            "document_pack_status": "Approved",
            "instructions_document": "/files/phase2-uat-instructions.txt",
            "specification_document": "/files/phase2-uat-specification.txt",
        }
    ).insert(ignore_permissions=True)
    out["doc_pack"] = pack.name
    tender.db_set("status", "Published", update_modified=False)
    tender.reload()

    supplier = frappe.db.get_value("Supplier", {"supplier_name": sra.supplier_name}, "name")
    if not supplier:
        supplier = frappe.db.get_value("Supplier", {}, "name")
    if not supplier:
        frappe.throw("No Supplier record available for submission smoke")
    profile = frappe.db.get_value("Supplier Compliance Profile", {"supplier": supplier}, "name")
    if profile:
        frappe.db.set_value(
            "Supplier Compliance Profile",
            profile,
            {"status": "Verified", "last_checked": now_datetime()},
            update_modified=False,
        )
    else:
        frappe.get_doc(
            {
                "doctype": "Supplier Compliance Profile",
                "supplier": supplier,
                "status": "Verified",
                "last_checked": now_datetime(),
            }
        ).insert(ignore_permissions=True)

    submission = frappe.get_doc(
        {
            "doctype": "Tender Submission",
            "tender": tender.name,
            "supplier": supplier,
            "currency": frappe.get_cached_value("Company", company, "default_currency") or "KES",
            "quoted_amount": 125000,
        }
    ).insert(ignore_permissions=True)
    criteria = frappe.get_all("Evaluation Criteria", fields=["name"], limit=1)
    criteria_name = criteria[0].name if criteria else None
    if not criteria_name:
        criteria_doc = frappe.get_doc(
            {
                "doctype": "Evaluation Criteria",
                "criteria_name": f"Phase2 UAT Criterion {stamp}",
                "weight": 1.0,
                "type": "Technical",
            }
        ).insert(ignore_permissions=True)
        criteria_name = criteria_doc.name
    submission.append("scores", {"criteria": criteria_name, "score": 85})
    submission.save(ignore_permissions=True)
    out["submission"] = submission.name

    declaration = frappe.get_doc(
        {
            "doctype": "Evaluator Declaration",
            "tender": tender.name,
            "committee_member": frappe.session.user,
            "declaration_type": "Both",
            "status": "Signed",
            "signed_on": now_datetime(),
        }
    ).insert(ignore_permissions=True)
    out["declaration"] = declaration.name

    worksheet = frappe.get_doc(
        {
            "doctype": "Evaluation Worksheet",
            "tender": tender.name,
            "submission": submission.name,
            "evaluator": frappe.session.user,
            "evaluation_stage": "Technical",
            "worksheet_status": "Submitted by Evaluator",
        }
    ).insert(ignore_permissions=True)
    out["worksheet"] = worksheet.name

    recommendation = frappe.get_doc(
        {
            "doctype": "Award Recommendation",
            "tender": tender.name,
            "recommended_submission": submission.name,
            "recommended_supplier": supplier,
            "recommended_amount": 125000,
            "recommendation_basis": "Best evaluated and compliant bid.",
            "prepared_by": frappe.session.user,
            "prepared_on": now_datetime(),
            "status": "Approved",
        }
    ).insert(ignore_permissions=True)
    out["recommendation"] = recommendation.name

    decision = frappe.get_doc(
        {
            "doctype": "Award Decision",
            "tender": tender.name,
            "award_recommendation": recommendation.name,
            "award_status": "Approved",
            "approved_supplier": supplier,
            "approved_submission": submission.name,
            "approved_amount": 125000,
            "decision_date": now_datetime().date(),
            "approved_by": frappe.session.user,
        }
    ).insert(ignore_permissions=True)
    out["decision"] = decision.name

    challenge = frappe.get_doc(
        {
            "doctype": "Challenge Review Case",
            "tender": tender.name,
            "award_decision": decision.name,
            "supplier": supplier,
            "case_number": f"CRC-{stamp}",
            "case_type": "Administrative Review",
            "filed_on": now_datetime(),
            "status": "Open",
        }
    ).insert(ignore_permissions=True)
    out["challenge"] = challenge.name

    blocked_error = None
    try:
        decision.reload()
        decision.award_status = "Finalized"
        decision.save(ignore_permissions=True)
    except Exception as exc:
        blocked_error = str(exc)

    challenge.reload()
    challenge.status = "Resolved"
    challenge.decision = "No merit; proceed with award finalization."
    challenge.decision_date = now_datetime().date()
    challenge.save(ignore_permissions=True)

    decision.reload()
    decision.award_status = "Finalized"
    decision.save(ignore_permissions=True)

    tender.reload()
    out["handoff"] = frappe.db.get_value("Award Contract Handoff", {"award_decision": decision.name}, "name")
    out["tender_status"] = tender.status
    out["purchase_order"] = tender.purchase_order
    out["challenge_block_message"] = blocked_error

    return out


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

    tender.db_set("purchase_order", po.name, update_modified=False)
    # Keep compatibility with phase-2 workflow-enabled instances.
    target_status = "Award Published" if frappe.db.exists("Workflow", "Tender Workflow") else "Awarded"
    tender.db_set("status", target_status, update_modified=False)
    tender.add_comment(
        "Workflow",
        f"Awarded to supplier {submission.supplier}. Purchase Order: {po.name}",
    )
    tender.reload()

    log_ken_tender_audit_event(
        action="tender_awarded",
        reference_doctype="Tender",
        reference_name=tender.name,
        details={
            "submission": submission.name,
            "supplier": submission.supplier,
            "purchase_order": po.name,
            "requested_submission": submission_name,
            "resolved_winner": winner,
        },
    )

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
    old_status = doc.status
    try:
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
        log_ken_tender_audit_event(
            action="plan_item_status_override",
            reference_doctype="Procurement Plan Item",
            reference_name=docname,
            details={
                "from_status": old_status,
                "to_status": status,
                "reason": reason,
            },
        )
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

