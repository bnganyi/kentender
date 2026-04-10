**KenTender Permission Defect Triage Checklist**

**Purpose**

Use this checklist whenever a user says:

- “I can’t access this”
- “I can access too much”
- “The report opens but shows nothing”
- “The workflow button is missing”
- “I can open the record but can’t act”
- “I can see another department’s data”

This checklist helps determine **which permission layer is broken**.

**1\. Identify the failure type first**

Every permission issue usually belongs to one of these layers:

**Layer A — Workspace/Menu visibility**

User cannot see the menu, workspace, or shortcut.

**Layer B — Report open-access**

User sees the menu but gets:

- “You don’t have access to Report...”

**Layer C — Row-level filtering**

User opens the report, but:

- sees no records they should see
- sees records they should not see

**Layer D — DocType access**

User can’t open a record at all, even when they should.

**Layer E — Workflow action authorization**

User can open the record but:

- cannot approve
- cannot publish
- cannot submit
- cannot activate

**Layer F — Assignment-based access**

User should only access assigned items but either:

- sees unassigned items
- cannot see assigned items

**Layer G — Sensitivity / sealed access**

User accesses documents or content they should not, or cannot access content they should.

Do **not** start debugging until you classify the issue into one of these.

**2\. Triage questions to ask for every defect**

Capture these first:

- What exact user account was used?
- What exact role(s) does that account have?
- What exact screen/report/object was accessed?
- What exact action failed?
- What exact message appeared?
- What object business ID was involved?
- What workflow state was the object in?
- Was the user assigned to it?
- Was the object sealed/sensitive?

Without this, debugging becomes guessing.

**3\. Core triage table**

**A. Workspace/Menu issue**

**Symptoms**

- workspace missing
- shortcut missing
- report not visible in menu

**Check**

- Is the workspace assigned to the role?
- Is the report shortcut visible to the role?
- Is the route hidden by role logic?

**Root cause usually**

- wrong workspace visibility mapping
- role-to-workspace rule missing
- shortcut not assigned

**Fix area**

- workspace visibility config
- route/menu config
- role mapping

**B. Report open-access issue**

**Symptoms**

- user clicks report
- gets “no access to report”

**Check**

- Is the role listed on the report definition?
- Is report access handled in custom backend logic?
- Is the role name exact and not mismatched?
- Is the report in the correct app/module context?

**Root cause usually**

- report role list missing the role
- wrong role name
- report copied/duplicated without permissions
- custom report access override blocking it

**Fix area**

- report roles
- report access registry
- backend report access hooks

**Example**

**HOD cannot open Pending Requisition Approvals**

- likely report role not assigned to HOD

**C. Row-level filtering issue**

**Symptoms**

- report opens but shows nothing
- report shows too much
- user sees another department/entity’s records

**Check**

- What filter condition is being applied?
- Is it based on current user?
- Is it department-scoped correctly?
- Is the workflow state filter correct?
- Is assignment filter correct?
- Is entity scope filter correct?

**Root cause usually**

- report role is correct, but row filter is wrong
- missing current-user condition
- wrong department mapping
- stale workflow-state names
- missing assignment join/filter

**Fix area**

- query filter logic
- backend report condition builder
- scope helper service

**Example**

HOD should see:

workflow_state = "Pending HOD Approval"  
AND hod_user = current_user

Not just:

workflow_state = "Pending HOD Approval"

**D. DocType access issue**

**Symptoms**

- user cannot open record from list/report
- user gets document permission error

**Check**

- Does role have baseline read permission?
- Is permission manager configured for read?
- Is there a custom has_permission override?
- Is there entity/owner/scope logic blocking read?

**Root cause usually**

- report allowed but DocType read not allowed
- custom has_permission too strict
- baseline role permission missing
- owner/scope logic incorrect

**Fix area**

- DocType role permissions
- custom permission hooks
- scope helper logic

**E. Workflow action authorization issue**

**Symptoms**

- user opens record but cannot approve/publish/submit/activate
- button missing or backend blocks action

**Check**

- Does user have the required business role?
- Is the record in the correct workflow state?
- Is the user assigned where required?
- Is separation-of-duty blocking them?
- Is the action authorized only in service layer?

**Root cause usually**

- action is correctly blocked
- or service-layer authorization is too strict
- or wrong workflow state
- or wrong actor role
- or assignment missing
- or separation-of-duty triggered

**Fix area**

- workflow action authorization service
- role-stage mapping
- assignment mapping
- SoD rules

**Important**

Do **not** “fix” this by granting write permission.  
That would be the wrong layer.

**F. Assignment-based access issue**

**Symptoms**

- evaluator cannot see assigned evaluation
- evaluator can see unassigned evaluation
- opening chair cannot open session
- complaint reviewer cannot review assigned complaint

**Check**

- Does assignment record exist?
- Is assignment active?
- Is user identity exact?
- Is committee role correct?
- Does access logic check assignment state?

**Root cause usually**

- assignment missing
- inactive assignment
- wrong linked record
- custom access logic not reading assignments correctly

**Fix area**

- assignment records
- assignment helper service
- query joins
- stage access checks

**G. Sensitivity / sealed access issue**

**Symptoms**

- supplier sees internal docs
- evaluator sees sealed bid too early
- procurement user can download pre-opening financial docs
- complaint evidence is too exposed

**Check**

- What is the file/document sensitivity class?
- Is the object in a sealed stage?
- Is protected file access being used?
- Is access going through authorized service path?

**Root cause usually**

- direct file access bypass
- generic attachment access exposed
- sealed access helper not integrated
- report/list exposing sensitive metadata

**Fix area**

- protected file access
- sensitivity enforcement helper
- document download routes
- UI links and attachments rendering

**4\. Triage workflow developers should follow**

Use this order every time.

**Step 1 — Reproduce**

Use the exact affected user account.

**Step 2 — Identify the object and stage**

Record:

- DocType
- business ID
- workflow state
- current role(s)

**Step 3 — Check report open-access**

Can the user open the report at all?

**Step 4 — Check DocType read permission**

Can the user open the underlying record directly?

**Step 5 — Check row-level filter**

Should this specific user see this specific row?

**Step 6 — Check assignment**

If assignment-sensitive, is the assignment active and correct?

**Step 7 — Check workflow authorization**

If acting on the record, should they be able to perform that action in this stage?

**Step 8 — Check sensitivity/sealed rules**

If documents/files are involved, is sealed or confidential logic in play?

Do not skip the sequence.

**5\. Defect classification template**

Use this structure in your defect log.

**Defect fields**

- Defect ID
- User account
- Role(s)
- Object type
- Business ID
- Workflow state
- Screen/report name
- Action attempted
- Actual result
- Expected result
- Permission layer affected
- Suspected root cause
- Evidence screenshot
- Reproducible? Yes/No

**Permission layer options**

- Workspace/Menu
- Report Access
- Row-Level Filter
- DocType Access
- Workflow Action
- Assignment Access
- Sensitivity/Sealed Access

This alone will make defect triage much cleaner.

**6\. High-priority triage scenarios for KenTender**

These are the first defects to test systematically.

**Requisition**

- HOD can open Pending Requisition Approvals
- HOD cannot see another HOD’s requisitions
- Finance sees only finance-stage requisitions
- Requisitioner sees own or department scope only

**Tender/Bids**

- Supplier sees only own bid
- Supplier cannot see another supplier’s bid
- Internal users cannot access sealed bids pre-opening
- Opening Chair can access opening session and register

**Evaluation**

- Evaluator can access assigned session only
- Evaluator cannot access without conflict declaration
- Evaluation Chair can finalize report
- Evaluator cannot approve award

**Award/Contract**

- Accounting Officer can final-approve award
- Procurement can prepare but not improperly final-approve if restricted
- Contract creation blocked during standstill
- Unauthorized user cannot activate contract

**Inspection/Stores/Assets**

- Inspector sees assigned inspection only
- Storekeeper sees only own store queues
- Asset Officer sees asset registration queue
- Contract Manager has read but not inappropriate edit rights

These should become your first permission regression suite.

**7\. Common wrong fixes to avoid**

These are the traps teams fall into.

**Wrong fix 1**

Grant broad read/write to make the error disappear.

**Why wrong**

It bypasses the real access model and creates data leakage.

**Wrong fix 2**

Fix report roles but ignore row filters.

**Why wrong**

User can open the report and then see everything.

**Wrong fix 3**

Put permission checks only in client-side button visibility.

**Why wrong**

Backend actions can still be triggered.

**Wrong fix 4**

Use owner-based logic where department/entity/assignment logic is required.

**Why wrong**

KenTender is not a personal-task app. It is a scoped institutional workflow app.

**Wrong fix 5**

Assume admin bypass is acceptable for business roles.

**Why wrong**

You lose the integrity of approval and audit controls.

**8\. Recommended debugging checklist for the current HOD issue**

Use this exact checklist.

**Case**

HOD cannot access Pending Requisition Approvals

**Check 1**

Does the report definition include the HOD role?

**Check 2**

Does HOD have baseline read access to Purchase Requisition?

**Check 3**

Does the report query filter use:

- hod_user = current_user
- correct workflow state

**Check 4**

Does the affected requisition actually have:

- hod_user populated
- correct workflow state value

**Check 5**

Is there custom report access logic denying HOD?

**Check 6**

Is the HOD role name in code exactly the same as the configured role?

**Check 7**

Can the HOD open the requisition directly if given the exact route?

That will isolate the failure fast.

**9\. Recommended implementation audit for every report**

For each key report, create a tiny checklist:

**Report**

Pending Requisition Approvals

**Allowed roles**

- HOD
- Finance Approver
- Auditor
- Admin

**Row filter**

- HOD: own approvals only
- Finance: finance-stage only
- Auditor/Admin: broad read

**Sensitive columns**

- internal exception notes hidden except authorized roles

**Backend enforced?**

- yes

This should exist for all critical reports.

**10\. Best next move**

The strongest next artifact is a **Permission Defect Triage Workbook** with sheets for:

- defect intake
- permission layer classification
- triage checklist
- key report validation cases
- role-by-role verification cases

That would let your testers and developers work from the same diagnostic framework instead of guessing.

Top of Form

Bottom of Form