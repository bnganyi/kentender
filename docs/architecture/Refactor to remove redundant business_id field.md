# Refactor to remove redundant business_id field

**Why I initially included business_id**

There are two common reasons architects introduce it:

**1\. Separation of concerns (generic enterprise pattern)**

- name → system/internal key
- business_id → human/business identifier

Used in systems where:

- IDs change format
- multiple identifiers exist
- integrations require stable external IDs

**2\. Frappe-specific caution (legacy habit)**

In some Frappe systems:

- name is auto-generated (hash or simple series)
- developers add business_id to get readable IDs later

**Why that reasoning DOES NOT apply to your system**

Your system is:

- workflow-heavy
- audit-heavy
- traceability-critical
- single-source-of-truth driven

👉 In that context, duplicating identifiers is a **design mistake**

**The real problem business_id creates (in your system)**

**1\. Drift risk (serious)**

Two fields representing the same concept:

- name = PR-0001
- business_id = PR-MOH-0001

Now:

- reports may use one
- APIs may use another
- users reference inconsistently

👉 This breaks traceability.

**2\. Violates your own architecture principles**

You’ve already enforced:

- one authoritative workflow state
- no duplicated status fields

But business_id is:  
👉 **duplicate identity**

Same problem, different place.

**3\. Adds unnecessary complexity**

You now need to maintain:

- generation logic
- uniqueness
- synchronization
- migration consistency

All for something Frappe already handles.

**The correct design for KenTender**

**🔥 Use name as the business identifier**

This is the clean, correct approach.

**Example**

Instead of:

| **Field** | **Value** |
| --- | --- |
| name | a8s7d9f |
| business_id | PR-MOH-0001 |

Use:

| **Field** | **Value** |
| --- | --- |
| name | PR-MOH-0001 |

**Enforce via naming series**

Frappe supports this natively.

Examples:

PR-.YYYY.-.#####  
PP-.YYYY.-.#####  
TD-.YYYY.-.#####  
AWD-.YYYY.-.#####  
CT-.YYYY.-.#####

**Why this is better (for your system)**

**1\. Single source of truth**

- no duplication
- no drift

**2\. Cleaner queries and joins**

- no need to map fields

**3\. Better audit**

- every reference uses same ID

**4\. Simpler UI**

- no confusion for users

**5\. Less code**

- no sync logic
- no validation duplication

**When business_id would have been valid**

Only if you had:

- external regulatory IDs (e.g. government-issued tender numbers)
- multiple identifiers per object
- legacy system migration constraints

👉 You don’t have those (based on your current design)

**So what should you do now?**

**Step 1 — Confirm usage**

Search:

- DocTypes
- reports
- APIs

Where is business_id used?

**Step 2 — Migrate**

- move business-friendly format to name
- ensure naming series is correct

**Step 3 — Remove field**

- delete business_id
- remove dependencies

**Step 4 — Fix references**

- reports → use name
- UI → display name
- APIs → expose name

**Important correction (from me to you)**

In your system, recommending business_id was overly generic and not aligned with your architecture maturity.

You’ve already made strong decisions:

- no duplicated status
- strict workflow control
- template-driven logic

👉 This same discipline applies to identifiers.

**One principle to lock in**

**Identity must be singular, stable, and visible**

In KenTender:  
👉 that is name