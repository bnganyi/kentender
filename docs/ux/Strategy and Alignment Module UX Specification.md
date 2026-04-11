# Strategy and Alignment Module UX Specification

**1\. Purpose & Scope**

**1.1 Purpose**

The Strategy module defines **why procurement exists**.

It provides the structure that connects:

- policy → programs → targets → procurement demand → budget → execution

**1.2 Role in System**

Strategy is the **anchor layer** for:

- requisition justification
- budget allocation
- procurement planning
- reporting and audit

**1.3 Key UX Principle**

👉 Strategy must be **visible everywhere it matters**, not just inside its own module.

**2\. Core Objects**

**Hierarchy (Canonical)**

National Framework  
→ National Pillar  
→ National Objective  
→ Entity Strategic Plan  
→ Program  
→ Sub-Program  
→ Indicator  
→ Target

**UX Rule**

- Always display **Name + Code**
- Example:
    - _Social Development (SOC)_
    - _Healthcare Delivery (HD)_

**3\. Actors & Roles**

**Primary Users**

- Planning Authority
- Procurement Planner
- Finance Officer
- Strategy / Master Data Admin

**Secondary Users**

- HoD
- Requisitioner
- Procurement Officer

**Read-Only Oversight**

- Auditor

**4\. Workspace Definition**

**Strategy & Alignment Workspace**

**4.1 Layout Overview**

**Left Panel (Filters & Navigation)**

- Framework filter
- Strategic Plan filter
- Program filter
- Department filter
- Fiscal Period

**Main Canvas**

1.  KPI Strip
2.  Hierarchy Explorer
3.  Alignment Panels
4.  Exception Panels

**Right Panel**

- Recent changes
- Linked plans
- Saved reports

**5\. KPI Strip**

Displays:

- Active Strategic Plans
- Active Programs
- Active Targets
- Requisitions Linked to Strategy
- Plan Items Linked to Strategy
- Unlinked Records

👉 This is the **health dashboard** of alignment.

**6\. Hierarchy Explorer (CRITICAL)**

**Purpose**

Allow users to navigate strategy like a tree.

**UX Pattern**

Expandable tree:

Vision 2030  
└── Social Development  
└── Improve Healthcare Access  
└── MOH Strategic Plan 2026–2030  
└── Healthcare Delivery  
└── County Referral Strengthening  
└── Imaging Equipment Coverage  
└── Target: Equip 2 hospitals

**Behavior**

- click node → open detail view
- expand/collapse nodes
- show counts:
    - number of requisitions
    - number of plan items

**7\. Alignment Panels (MOST IMPORTANT)**

**7.1 Requisitions by Program**

Shows:

- Program
- Number of requisitions
- Total value

**7.2 Plan Items by Target**

Shows:

- Target
- Number of plan items
- Total planned value

**7.3 Budget by Indicator**

Shows:

- Indicator
- Allocated budget
- Reserved
- Committed

**7.4 Contracts by Strategic Plan**

Shows:

- Strategic Plan
- Number of contracts
- Total contract value

**UX Insight**

This answers:

👉 “Are we procuring what we said we would?”

**8\. Exception Panels**

**Show problems, not data**

**8.1 Unlinked Requisitions**

- requisitions missing strategy linkage

**8.2 Unlinked Plan Items**

- plan items without target

**8.3 Budget Without Strategy**

- budget lines not linked to indicators

**8.4 Misaligned Records**

- mismatched program/sub-program

**UX Rule**

- show count + severity
- clickable → fix screen

**9\. Strategy Forms (All Levels)**

**9.1 Header**

- Name
- Code
- Status
- Parent

**9.2 Tabs**

**Summary**

- description
- owner
- validity period

**Hierarchy**

- parent
- children

**Downstream Links**

- linked requisitions
- plan items
- budget lines
- contracts

**Audit**

- created by
- modified by
- approval history

**9.3 Smart Buttons**

- View Child Records
- View Requisitions
- View Plan Items
- View Budgets
- View Contracts

**10\. Linkage in Downstream Forms**

**Strategy must appear in:**

**Requisition Form**

- Strategic Plan
- Program
- Sub-Program
- Indicator
- Target

**Plan Item**

- full strategy chain

**Budget Line**

- indicator + target

**UX Rule**

- clickable links
- show name, not code

**11\. Validation Rules**

**11.1 Mandatory Linkage**

**Requisition must have:**

- Program
- Sub-Program
- Indicator
- Target

**11.2 Consistency**

if sub_program.program != program:  
throw("Invalid program/sub-program combination")

**11.3 Target Coverage**

- target must belong to indicator
- indicator must belong to sub-program

**12\. Permissions & Control**

**Strategy Admin**

- full CRUD

**Planning Authority**

- read + approve

**Planner**

- read + use

**Others**

- read only

**Rule**

❌ No uncontrolled edits by operational users

**13\. UI Behavior Rules**

**13.1 Labels**

Always show:

👉 Name + Code

**13.2 Dropdowns**

- searchable
- grouped by hierarchy

**13.3 Inline Context**

Show:

Target:  
Equip 2 district hospitals (PT-IMG-2026)  
Program:  
Healthcare Delivery (HD)

**14\. Anti-Patterns**

❌ Showing only codes  
❌ Flat dropdowns with no hierarchy  
❌ Missing linkage in requisitions  
❌ Allowing edits without governance  
❌ Hiding strategy from planning

**15\. Acceptance Criteria**

Strategy UX is complete when:

**Functional**

- users can navigate hierarchy
- users can link strategy to requisitions

**Visibility**

- strategy visible across modules

**Integrity**

- invalid combinations blocked

**Reporting**

- alignment panels reflect reality

**16\. Final Insight**

If Strategy is done correctly:

- Planning becomes structured
- Budget becomes meaningful
- Procurement becomes justifiable
- Audit becomes trivial

If Strategy is weak:

- everything downstream becomes guesswork