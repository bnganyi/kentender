# KenTender UX Design

The UX must reflect:

- **public-sector workflow reality**
- **role-driven navigation**
- **process-first thinking (not DocType-first)**

ERPNext v16 gives you the right primitives:

- Workspaces
- Sidebar groups
- Quick actions
- Kanban/list views
- Dashboards
- Web portal (for suppliers)

If you just expose DocTypes, users will get lost.  
We’re going to design **task-oriented workspaces**.

**🧠 Core UX Principles (Non-Negotiable)**

**1\. Users think in processes, not DocTypes**

❌ “Create Procurement Plan Item”  
✅ “Plan Procurement”

**2\. Each role should see ONLY what they need**

- Procurement ≠ Finance ≠ Evaluator ≠ Supplier

**3\. Navigation should follow lifecycle**

Plan → Request → Tender → Evaluate → Award → Execute

NOT:

DocType A → DocType B → DocType C

**🧩 System Navigation Architecture**

**Top-Level Sidebar (Modules)**

Keep this clean. No more than 7–8.

**✅ Recommended modules**

1.  **Procurement Planning**
2.  **Requisitions**
3.  **Tendering**
4.  **Suppliers**
5.  **Evaluation & Award**
6.  **Contracts & Execution** _(Phase 3)_
7.  **Oversight & Audit**
8.  **Administration**

**🧭 Workspace Design (ERPNext v16)**

We’ll define **Workspaces per module**, not per DocType.

**🟦 1. PROCUREMENT PLANNING WORKSPACE**

**🎯 Users:**

- Planning Authority
- Procurement Planner
- Finance

**🔹 Sections**

**A. Quick Actions**

- ➕ Create Procurement Plan
- ➕ Add Plan Item
- 📊 View Budget Status

**B. Work in Progress**

- Draft Plans
- Pending Consolidation
- Pending Finance Review

**C. Insights**

- Budget vs Planned
- Plans by Department
- Plans by Quarter

**D. Links**

- Procurement Plan
- Procurement Plan Item
- Strategic Objective
- Budget Control

**🟩 2. REQUISITIONS WORKSPACE**

This is your **operational nerve center**

**🎯 Users:**

- Departments
- Finance
- Procurement

**A. Quick Actions**

- ➕ New Requisition
- 📋 My Requisitions
- 📦 Department Requests

**B. Action Queues (VERY IMPORTANT UX)**

- 🔴 Pending My Approval
- 🟡 Awaiting Finance Review
- 🔵 Awaiting Procurement Review
- ⚠️ Budget Blocked
- 🚨 Emergency Requests

**C. Monitoring**

- Requisition Status Board (Kanban)
- Budget Commitments
- Aging Requests

**D. Links**

- Purchase Requisition
- Requisition Items
- Commitments
- Exceptions
- Amendments

**🟨 3. SUPPLIERS WORKSPACE**

**🎯 Users:**

- Supplier Officers
- Procurement

**A. Quick Actions**

- ➕ New Supplier Application
- 🔍 Review Applications

**B. Queues**

- Pending Approval
- Expiring Compliance
- Suspended Suppliers
- Renewal Due

**C. Insights**

- Suppliers by Category
- Compliance Status

**D. Links**

- Supplier Master
- Applications
- Compliance Documents
- Debarment Register

**🟥 4. TENDERING WORKSPACE**

This is your **core operational UX**

**🎯 Users:**

- Procurement

**A. Quick Actions**

- ➕ Create Tender (from Requisition)
- 📄 Upload Documents
- 📢 Publish Tender

**B. Action Boards**

- Draft Tenders
- Pending Internal Review
- Ready for Publication
- Active Tenders
- Closing Soon

**C. Lifecycle Tracker (🔥 important)**

Show stages:

Draft → Published → Closed → Opened → Evaluation → Award

Clickable per stage.

**D. Links**

- Tender
- Tender Lots
- Documents
- Addenda
- Clarifications

**🟪 5. SUBMISSIONS & OPENING WORKSPACE**

**🎯 Users:**

- Procurement
- Opening Committee

**A. Queues**

- Submissions Received
- Closing Today
- Ready for Opening
- Late Submissions

**B. Opening Control Panel**

- Start Opening Session
- View Register
- Generate Opening Record

**C. Links**

- Submissions
- Receipt Log
- Opening Register

**🟫 6. EVALUATION & AWARD WORKSPACE**

**🎯 Users:**

- Evaluators
- Committee Chair
- Procurement

**A. My Tasks (critical UX)**

- Assigned Evaluations
- Pending Declarations
- Worksheets in Progress

**B. Evaluation Flow Panel**

Preliminary → Technical → Financial → Consensus

Each stage clickable.

**C. Decision Area**

- Award Recommendations
- Pending Approval
- Notifications
- Challenge Cases

**D. Links**

- Evaluation Worksheets
- Consensus Records
- Award Decision
- Notifications

**⚫ 7. CONTRACTS & EXECUTION (Phase 3)**

Keep minimal for now:

- Contract Handoff
- Purchase Orders
- Delivery tracking

**⚪ 8. OVERSIGHT & AUDIT**

**🎯 Users:**

- Auditor
- Accounting Officer

**A. Dashboards**

- Full Procurement Pipeline
- Exceptions
- Overrides
- Delays

**B. Logs**

- Approval Logs
- Amendment Logs
- Opening Logs
- Evaluation Logs

**C. Reports**

- Requisition → Award traceability
- Supplier actions
- Budget vs actual

**🔧 FIELD-LEVEL UX (IMPORTANT)**

Use **permlevel** smartly:

**permlevel structure**

- **0** → operational users
- **1** → supervisors (HoD, Procurement)
- **2** → finance / approvals
- **3** → audit / system only

**Example (Requisition)**

**permlevel 0**

- description
- quantity
- specs

**permlevel 1**

- approval comments
- department validation

**permlevel 2**

- budget fields
- commitment fields

**permlevel 3**

- audit logs
- system flags

**🎯 CRITICAL UX PATTERNS**

**1\. “Queues, not lists”**

Always show:

- “Pending My Action”
- not just raw lists

**2\. Status colors**

- Red → blocked
- Yellow → pending
- Green → approved
- Blue → in progress

**3\. Lifecycle breadcrumbs**

Every major document should show:

APP → Requisition → Tender → Submission → Award

Clickable.

**4\. Locking UX**

When locked:

- disable fields
- show banner:

“This record is locked due to tender initiation”

**5\. Smart buttons**

On every doc:

**Requisition**

- “Create Tender”
- “View Commitments”

**Tender**

- “View Submissions”
- “Start Opening”
- “View Evaluation”

**Submission**

- “View Evaluation Status”

**📱 SUPPLIER PORTAL UX (SEPARATE)**

Do NOT mix with ERP backend.

Supplier sees:

- Registration
- My Documents
- My Bids
- Notifications

**⚠️ COMMON UX MISTAKES (AVOID THESE)**

❌ exposing raw DocTypes in sidebar  
❌ mixing supplier and internal UI  
❌ allowing too many actions on one screen  
❌ no “Pending My Action” views  
❌ unclear workflow progression  
❌ hidden approval steps  
❌ editable data after lock

**🧭 FINAL NAVIGATION FLOW**

**Internal user journey**

Planning Workspace  
↓  
Requisition Workspace  
↓  
Tendering Workspace  
↓  
Submission & Opening  
↓  
Evaluation & Award  
↓  
Contracts

**🚀 What I recommend next**

We can take this further into:

**Option A**

👉 **ERPNext Workspace JSON configs (import-ready)**

**Option B**

👉 **UI wireframes (screen-by-screen)**

**Option C**

👉 **Role-based UX flows (click-by-click journeys)**

**Sample Designs from Core ERPNext**

**Landing page for Selling**