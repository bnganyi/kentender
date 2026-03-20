from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ComplianceRequirement(Document):
    pass


def recheck_supplier_compliance() -> None:
    """Daily job entrypoint: evaluate all suppliers against compliance requirements."""
    suppliers = frappe.get_all("Supplier", pluck="name")
    for supplier in suppliers:
        frappe.enqueue("kentender.kentender.doctype.compliance_requirement.compliance_requirement.run_check", supplier=supplier, queue="long")


def run_check(supplier: str) -> None:
    """Evaluate mandatory compliance requirements for a supplier and update profile + records."""
    from json import dumps

    requirements = frappe.get_all(
        "Compliance Requirement",
        fields=["name", "api_url", "is_mandatory"],
    )

    mandatory_reqs = [r["name"] for r in requirements if r.get("is_mandatory")]

    # If nothing is configured, allow access.
    if not mandatory_reqs:
        _upsert_profile_status(supplier, "Verified")
        return

    def _requirement_status_and_payload(req: dict) -> tuple[str, str]:
        api_url = (req.get("api_url") or "").strip()
        api_url_l = api_url.lower()

        # Deterministic mock results for local/testing without network calls.
        # Examples: mock://verified, mock://failed, mock://pending
        if api_url_l.startswith("mock://"):
            if "pending" in api_url_l:
                return "Pending", dumps({"mock": api_url})
            if "failed" in api_url_l:
                return "Failed", dumps({"mock": api_url})
            return "Verified", dumps({"mock": api_url})

        # MVP usability default: when api_url isn't configured yet, treat as Verified.
        if not api_url:
            return "Verified", dumps({"note": "No api_url provided; treated as Verified for MVP"})

        try:
            import requests

            resp = requests.get(api_url, params={"supplier": supplier}, timeout=5)
            data = resp.json() if hasattr(resp, "json") else {}
            status_raw = data.get("status") or data.get("result") or data.get("valid")
            status_raw_l = str(status_raw).lower()

            if status_raw_l in ("valid", "verified", "true", "1", "yes"):
                return "Verified", dumps(data)

            return "Failed", dumps(data)
        except Exception as e:
            return "Pending", dumps({"error": str(e), "api_url": api_url})

    mandatory_statuses: list[str] = []

    for req in requirements:
        req_name = req["name"]
        status, payload = _requirement_status_and_payload(req)

        record_name = frappe.db.get_value(
            "Supplier Compliance Record",
            {"supplier": supplier, "requirement": req_name},
            "name",
        )

        if not record_name:
            frappe.get_doc(
                {
                    "doctype": "Supplier Compliance Record",
                    "supplier": supplier,
                    "requirement": req_name,
                    "status": status,
                    "last_verified_on": now_datetime(),
                    "response_payload": payload,
                }
            ).insert()
        else:
            frappe.db.set_value(
                "Supplier Compliance Record",
                record_name,
                {
                    "status": status,
                    "last_verified_on": now_datetime(),
                    "response_payload": payload,
                },
            )

        if req.get("is_mandatory"):
            mandatory_statuses.append(status)

    overall = _aggregate_status(mandatory_statuses)
    _upsert_profile_status(supplier, overall)


def _aggregate_status(mandatory_statuses: list[str]) -> str:
    if any(s == "Failed" for s in mandatory_statuses):
        return "Rejected"
    if all(s == "Verified" for s in mandatory_statuses):
        return "Verified"
    if any(s == "Verified" for s in mandatory_statuses):
        return "Partially Verified"
    return "Pending"


def _upsert_profile_status(supplier: str, status: str) -> None:
    profile_name = frappe.db.get_value("Supplier Compliance Profile", {"supplier": supplier}, "name")
    if not profile_name:
        frappe.get_doc(
            {
                "doctype": "Supplier Compliance Profile",
                "supplier": supplier,
                "status": status,
                "last_checked": now_datetime(),
            }
        ).insert()
    else:
        frappe.db.set_value(
            "Supplier Compliance Profile",
            profile_name,
            {"status": status, "last_checked": now_datetime()},
        )

