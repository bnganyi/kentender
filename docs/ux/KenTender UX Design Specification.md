# KenTender UX Design Specification

**1\. Purpose of This Document**

This document defines the **UX behavior, rules, and interaction patterns** for KenTender.

It governs:

- how users interact with the system
- how workflows are enforced through UI
- how templates control behavior
- how roles are isolated
- how system constraints are communicated

**2\. UX Philosophy (Final)**

KenTender is a:

👉 **Process-controlled procurement system**

NOT:

- form-driven
- user-configurable at runtime
- permissive

**2.1 Core Principle**

Users do not define processes.  
Users execute system-defined processes.

**2.2 System Authority Layers**

Every action is governed by:

1.  Workflow State
2.  Template (procurement / evaluation / acceptance)
3.  Permissions
4.  Assignment

**2.3 UX Responsibility**

The UI must:

- expose system decisions
- guide users to valid actions
- prevent invalid actions
- explain constraints

**3\. Core UX Rules (Non-Negotiable)**

**Rule 1 — Process-first navigation**

Users move through:

Requisition → Planning → Tender → Evaluation → Award → Contract → Acceptance → GRN → Asset

Navigation must reflect this order.

**Rule 2 — Templates drive behavior**

Users must NEVER:

- define evaluation criteria
- define acceptance workflows
- modify process structure

System must:

- derive behavior from templates
- display the template used

**Rule 3 — System decisions must be visible**

Every major record must show:

- template name + version
- match quality (exact / partial)
- override status

**Rule 4 — No silent blocking**

If an action is unavailable:

UI MUST show:

- why it is blocked
- what is required
- who must act

**Rule 5 — Role isolation is strict**

Users see ONLY:

- relevant records
- permitted actions
- assigned tasks

**Rule 6 — Single source of truth**

- one identifier (name)
- one workflow state
- no duplicated control fields

**4\. Workflow Interaction Model**

**4.1 Action Model**

All user actions must be:

- triggered via buttons
- validated server-side
- logged (audit)

**4.2 State Transition Rules**

- Users cannot directly change workflow_state
- Transitions only via:
    - approved buttons
    - workflow engine

**4.3 Blocking Model**

When blocked:

UI must display:

Action unavailable:  
\- Reason  
\- Required step  
\- Responsible role

**5\. Template-Driven UX Model**

**5.1 Template Visibility**

Every record must show:

- Template name
- Version
- Match type
- Override status

**5.2 Template Effects on UX**

Templates control:

| **Area** | **Effect** |
| --- | --- |
| Tender | structure, requirements |
| Evaluation | criteria, scoring |
| Award | approval flow |
| Acceptance | inspection workflow |

**5.3 Template Lineage**

UI must display:

Plan Item → Template → Evaluation Template → Acceptance Template

**6\. Workspace Interaction Model**

**6.1 Workspace Components**

Each workspace contains:

1.  Quick Actions
2.  My Work Queue
3.  Monitoring (KPIs)
4.  Linked Records

**6.2 Queue Behavior**

Queues must:

- be role-filtered
- reflect workflow_state
- update in real-time

**6.3 Assignment Model**

Users act ONLY on:

- assigned records
- permitted queues

**7\. Role-Based UX Design**

**7.1 Role Matrix**

| **Role** | **Interaction** |
| --- | --- |
| Procurement Officer | Planning, Tendering |
| Evaluator | Evaluation only |
| Inspector | Acceptance workflow |
| Storekeeper | GRN processing |
| Asset Officer | Asset lifecycle |
| Contract Manager | Contract execution |

**7.2 UX Restrictions**

- Evaluators cannot see bids outside assignment
- Suppliers cannot see internal data
- Inspectors cannot modify contracts

**8\. Form Interaction Design**

**8.1 Header Requirements**

Every form must display:

- Document ID
- Workflow State
- Template + Version
- Owner

**8.2 Context Panel**

Must show:

- constraints
- required actions
- next steps

**8.3 Smart Buttons**

Buttons must:

- reflect allowed actions
- disappear when invalid
- never bypass workflow

**9\. Critical UX Patterns**

**9.1 Template Awareness**

Users always see:

- what template is applied
- how it affects them

**9.2 Constraint Visibility**

Example:

Cannot proceed:  
\- Standstill period active  
\- Awaiting approval from Finance

**9.3 Lifecycle Breadcrumbs**

Display:

Requisition → Plan → Tender → Evaluation → Award

**9.4 Assignment-driven UI**

Users see:

- “My Evaluations”
- “My Inspections”
- “My Contracts”

**10\. Supplier Portal UX (Final)**

**10.1 Structure**

Tabs:

- Registration
- Documents
- My Bids
- Notifications

**10.2 Restrictions**

Suppliers MUST NOT see:

- evaluation data
- competitor bids
- internal notes

**11\. UX for Acceptance, Stores & Assets**

**11.1 Acceptance**

- dynamic workflow (based on template)
- inspection → technical → committee → approval

**11.2 Stores**

- GRN only after acceptance
- goods tracking

**11.3 Assets**

- asset creation from GRN
- lifecycle tracking

**12\. Error & Feedback Handling**

**12.1 System Messages**

Must be:

- specific
- actionable
- role-aware

**12.2 No Generic Errors**

❌ “Action failed”  
✅ “Cannot proceed: Evaluation not approved”

**13\. UX Anti-Patterns (Strictly Prohibited)**

❌ Manual process definition  
❌ Hidden system logic  
❌ Multiple identifiers  
❌ Duplicate status fields  
❌ Uncontrolled actions  
❌ Supplier/internal UI mixing

**14\. Final UX Model**

User flow:

User → Workspace → Queue → Record → Action

System control:

Template → Workflow → Permissions → Outcome

**15\. Final Principle**

The system enforces policy.  
The UI must make that enforcement clear, predictable, and usable.