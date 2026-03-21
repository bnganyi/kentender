import json, os
from pathlib import Path

# Directory containing workspaces/, sidebars/, desktop_icons/, patches/
base = str(Path(__file__).resolve().parent)

APP='kentender'
MODULE='KenTender'

roles = {
    'procurement_planning': ['Planning Authority','Procurement Planner','Finance/Budget Officer','Head of Procurement','Accounting Officer','Internal Auditor'],
    'requisitions': ['Requestor','Head of Department','Finance/Budget Officer','Accounting Officer','Procurement Officer','Head of Procurement','Internal Auditor'],
    'suppliers': ['Supplier Registration Officer','Procurement Officer','Head of Procurement','Internal Auditor'],
    'tendering': ['Procurement Officer','Head of Procurement','Tender Committee Secretary','Accounting Officer','Internal Auditor'],
    'submissions_opening': ['Procurement Officer','Tender Committee Secretary','Opening Committee Member','Internal Auditor'],
    'evaluation_award': ['Evaluation Committee Member','Evaluation Committee Chair','Tender Committee Secretary','Procurement Officer','Head of Procurement','Accounting Officer','Internal Auditor'],
    'contracts_execution': ['Procurement Officer','Contract Manager','Stores User','Accounts User','Head of Procurement','Accounting Officer','Internal Auditor'],
    'oversight_audit': ['Accounting Officer','Internal Auditor','Oversight Viewer','Head of Procurement'],
}

workspace_defs = [
    {
        'key':'procurement_planning','name':'KT Procurement Planning','title':'Procurement Planning','icon':'goal','color':'blue','sequence':10,
        'shortcuts':[
            ('New Procurement Plan','Procurement Plan','New'),
            ('Procurement Plans','Procurement Plan','List'),
            ('Plan Items','Procurement Plan Item','List'),
            ('Strategic Objectives','Strategic Objective','List'),
            ('Budget Control Rules','Budget Control Rule','List'),
            ('Threshold Rules','Procurement Threshold Rule','List'),
        ],
        'quick_lists':[
            ('Procurement Plan','Draft Plans','[["status","=","Draft"]]'),
            ('Procurement Plan','Pending Finance Review','[["status","=","Finance Review"]]'),
            ('Procurement Plan Item','High Risk Planned Items','[["risk_level","=","High"]]'),
        ],
        'link_cards':[
            ('Planning Actions', [
                ('Procurement Plan','DocType','Procurement Plan'),
                ('Procurement Plan Item','DocType','Procurement Plan Item'),
                ('Procurement Plan Revision','DocType','Procurement Plan Revision'),
            ]),
            ('Planning Reference Data', [
                ('Strategic Objective','DocType','Strategic Objective'),
                ('Procurement Policy Profile','DocType','Procurement Policy Profile'),
                ('Procurement Threshold Rule','DocType','Procurement Threshold Rule'),
                ('Approval Matrix Rule','DocType','Approval Matrix Rule'),
            ]),
        ],
        'number_cards':[('Planned Value','KT Planned APP Value'),('Plans Awaiting Approval','KT APP Pending Approval')],
        'sidebar':[
            ('Section Break','Planning Desk','compass',None,None),
            ('Link','Dashboard','Workspace','KT Procurement Planning',None,None),
            ('Link','Procurement Plans','DocType','Procurement Plan',None,None),
            ('Link','Plan Items','DocType','Procurement Plan Item',None,None),
            ('Link','Plan Revisions','DocType','Procurement Plan Revision',None,None),
            ('Section Break','Reference Data','database',None,None),
            ('Link','Strategic Objectives','DocType','Strategic Objective',None,None),
            ('Link','Policy Profiles','DocType','Procurement Policy Profile',None,None),
            ('Link','Budget Control Rules','DocType','Budget Control Rule',None,None),
        ]
    },
    {
        'key':'requisitions','name':'KT Requisitions','title':'Requisitions','icon':'form','color':'orange','sequence':20,
        'shortcuts':[
            ('New Requisition','Purchase Requisition','New'),
            ('My Requisitions','Purchase Requisition','List'),
            ('Requisition Amendments','Purchase Requisition Amendment','List'),
            ('Active Commitments','Purchase Requisition Commitment','List'),
            ('Exceptions','Purchase Requisition Exception','List'),
            ('Tender Handoffs','Requisition Tender Handoff','List'),
        ],
        'quick_lists':[
            ('Purchase Requisition','Pending My Approval','[["status","in",["HoD Review","Finance Review","AO Review","Procurement Review"]]]'),
            ('Purchase Requisition','Budget Blocked','[["budget_status","=","Blocked"]]'),
            ('Purchase Requisition','Emergency Requests','[["emergency_flag","=",1]]'),
        ],
        'link_cards':[
            ('Requisition Operations', [
                ('Purchase Requisition','DocType','Purchase Requisition'),
                ('Purchase Requisition Amendment','DocType','Purchase Requisition Amendment'),
                ('Purchase Requisition Commitment','DocType','Purchase Requisition Commitment'),
                ('Requisition Tender Handoff','DocType','Requisition Tender Handoff'),
            ]),
            ('Governance', [
                ('Purchase Requisition Exception','DocType','Purchase Requisition Exception'),
                ('APP to Requisition Traceability','Report','APP to Requisition Traceability'),
            ]),
        ],
        'number_cards':[('Pending Requisitions','KT Requisition Pending'),('Committed Value','KT Requisition Commitment Value')],
        'sidebar':[
            ('Section Break','Requisition Desk','clipboard',None,None),
            ('Link','Dashboard','Workspace','KT Requisitions',None,None),
            ('Link','Purchase Requisitions','DocType','Purchase Requisition',None,None),
            ('Link','Amendments','DocType','Purchase Requisition Amendment',None,None),
            ('Link','Commitments','DocType','Purchase Requisition Commitment',None,None),
            ('Link','Exceptions','DocType','Purchase Requisition Exception',None,None),
            ('Link','Tender Handoffs','DocType','Requisition Tender Handoff',None,None),
        ]
    },
    {
        'key':'suppliers','name':'KT Suppliers','title':'Suppliers','icon':'people','color':'green','sequence':30,
        'shortcuts':[
            ('Supplier Applications','Supplier Registration Application','List'),
            ('Supplier Master','Supplier Master','List'),
            ('Category Registrations','Supplier Category Registration','List'),
            ('Compliance Documents','Supplier Compliance Document','List'),
            ('Renewal Reviews','Supplier Renewal Review','List'),
            ('Debarment Register','Suspension Debarment Register','List'),
        ],
        'quick_lists':[
            ('Supplier Registration Application','Pending Review','[["application_status","in",["Submitted","Compliance Review","Procurement Review"]]]'),
            ('Supplier Compliance Document','Expiring Soon','[["verification_status","=","Expired"]]'),
            ('Supplier Master','Suspended Suppliers','[["supplier_status","in",["Suspended","Debarred","Blacklisted"]]]'),
        ],
        'link_cards':[
            ('Supplier Governance', [
                ('Supplier Registration Application','DocType','Supplier Registration Application'),
                ('Supplier Master','DocType','Supplier Master'),
                ('Supplier Status Action','DocType','Supplier Status Action'),
                ('Suspension Debarment Register','DocType','Suspension Debarment Register'),
            ]),
            ('Supplier Compliance', [
                ('Supplier Compliance Document','DocType','Supplier Compliance Document'),
                ('Supplier Category Registration','DocType','Supplier Category Registration'),
                ('Supplier Beneficial Ownership','DocType','Supplier Beneficial Ownership'),
                ('Supplier Bank Detail','DocType','Supplier Bank Detail'),
            ]),
        ],
        'number_cards':[('Active Suppliers','KT Active Suppliers'),('Supplier Renewals Due','KT Supplier Renewals Due')],
        'sidebar':[
            ('Section Break','Supplier Desk','users',None,None),
            ('Link','Dashboard','Workspace','KT Suppliers',None,None),
            ('Link','Applications','DocType','Supplier Registration Application',None,None),
            ('Link','Supplier Master','DocType','Supplier Master',None,None),
            ('Link','Category Registrations','DocType','Supplier Category Registration',None,None),
            ('Link','Compliance Documents','DocType','Supplier Compliance Document',None,None),
            ('Link','Debarment Register','DocType','Suspension Debarment Register',None,None),
        ]
    },
    {
        'key':'tendering','name':'KT Tendering','title':'Tendering','icon':'bullhorn','color':'red','sequence':40,
        'shortcuts':[
            ('Create Tender','Tender','New'),
            ('Draft Tenders','Tender','List'),
            ('Tender Lots','Tender Lot','List'),
            ('Document Packs','Tender Document Pack','List'),
            ('Clarifications','Tender Clarification','List'),
            ('Addenda','Tender Addendum','List'),
        ],
        'quick_lists':[
            ('Tender','Ready for Publication','[["tender_status","=","Approved for Publication"]]'),
            ('Tender','Active Tenders','[["tender_status","=","Published"]]'),
            ('Tender','Closing Soon','[["tender_status","=","Published"]]'),
        ],
        'link_cards':[
            ('Tender Setup', [
                ('Tender','DocType','Tender'),
                ('Tender Lot','DocType','Tender Lot'),
                ('Tender Eligibility Rule','DocType','Tender Eligibility Rule'),
                ('Tender Security Rule','DocType','Tender Security Rule'),
            ]),
            ('Tender Documents', [
                ('Tender Document Pack','DocType','Tender Document Pack'),
                ('Tender Document Version','DocType','Tender Document Version'),
                ('Tender Clarification','DocType','Tender Clarification'),
                ('Tender Addendum','DocType','Tender Addendum'),
                ('Tender Publication Record','DocType','Tender Publication Record'),
            ]),
        ],
        'number_cards':[('Published Tenders','KT Published Tenders'),('Closings This Week','KT Tenders Closing This Week')],
        'sidebar':[
            ('Section Break','Tender Desk','briefcase',None,None),
            ('Link','Dashboard','Workspace','KT Tendering',None,None),
            ('Link','Tenders','DocType','Tender',None,None),
            ('Link','Tender Lots','DocType','Tender Lot',None,None),
            ('Link','Document Packs','DocType','Tender Document Pack',None,None),
            ('Link','Clarifications','DocType','Tender Clarification',None,None),
            ('Link','Addenda','DocType','Tender Addendum',None,None),
        ]
    },
    {
        'key':'submissions_opening','name':'KT Submissions & Opening','title':'Submissions & Opening','icon':'inbox','color':'purple','sequence':50,
        'shortcuts':[
            ('Tender Submissions','Tender Submission','List'),
            ('Bid Receipt Log','Bid Receipt Log','List'),
            ('Opening Register','Bid Opening Register','List'),
            ('Opening Records','Bid Opening Record','List'),
        ],
        'quick_lists':[
            ('Tender Submission','Submissions Received','[["submission_status","=","Submitted"]]'),
            ('Tender Submission','Late Submissions','[["submission_status","=","Late"]]'),
            ('Bid Opening Register','Ready for Opening','[["register_status","=","Draft"]]'),
        ],
        'link_cards':[
            ('Submission Control', [
                ('Tender Submission','DocType','Tender Submission'),
                ('Tender Submission Lot Response','DocType','Tender Submission Lot Response'),
                ('Tender Submission Attachment','DocType','Tender Submission Attachment'),
                ('Bid Receipt Log','DocType','Bid Receipt Log'),
            ]),
            ('Opening Control', [
                ('Bid Opening Register','DocType','Bid Opening Register'),
                ('Bid Opening Record','DocType','Bid Opening Record'),
            ]),
        ],
        'number_cards':[('Submissions Received','KT Tender Submissions Received'),('Late Bids','KT Late Bids')],
        'sidebar':[
            ('Section Break','Submission Desk','mail',None,None),
            ('Link','Dashboard','Workspace','KT Submissions & Opening',None,None),
            ('Link','Tender Submissions','DocType','Tender Submission',None,None),
            ('Link','Receipt Log','DocType','Bid Receipt Log',None,None),
            ('Link','Opening Register','DocType','Bid Opening Register',None,None),
            ('Link','Opening Records','DocType','Bid Opening Record',None,None),
        ]
    },
    {
        'key':'evaluation_award','name':'KT Evaluation & Award','title':'Evaluation & Award','icon':'verify','color':'cyan','sequence':60,
        'shortcuts':[
            ('My Worksheets','Evaluation Worksheet','List'),
            ('Consensus Records','Evaluation Consensus Record','List'),
            ('Award Recommendations','Award Recommendation','List'),
            ('Award Decisions','Award Decision','List'),
            ('Challenge Cases','Challenge Review Case','List'),
            ('Notifications','Tender Notification Log','List'),
        ],
        'quick_lists':[
            ('Evaluator Declaration','Pending Declarations','[["status","!=","Signed"]]'),
            ('Evaluation Worksheet','Worksheets In Progress','[["worksheet_status","=","Under Review"]]'),
            ('Award Recommendation','Pending Approval','[["status","in",["Draft","Committee Review"]]]'),
        ],
        'link_cards':[
            ('Evaluation', [
                ('Evaluation Committee','DocType','Evaluation Committee'),
                ('Evaluator Declaration','DocType','Evaluator Declaration'),
                ('Tender Evaluation Scheme','DocType','Tender Evaluation Scheme'),
                ('Evaluation Worksheet','DocType','Evaluation Worksheet'),
                ('Evaluation Consensus Record','DocType','Evaluation Consensus Record'),
                ('Post Qualification Check','DocType','Post Qualification Check'),
            ]),
            ('Award', [
                ('Award Recommendation','DocType','Award Recommendation'),
                ('Award Decision','DocType','Award Decision'),
                ('Tender Notification Log','DocType','Tender Notification Log'),
                ('Challenge Review Case','DocType','Challenge Review Case'),
                ('Award Publication Record','DocType','Award Publication Record'),
            ]),
        ],
        'number_cards':[('Evaluations Pending','KT Evaluations Pending'),('Awards Awaiting Approval','KT Awards Awaiting Approval')],
        'sidebar':[
            ('Section Break','Evaluation Desk','check-circle',None,None),
            ('Link','Dashboard','Workspace','KT Evaluation & Award',None,None),
            ('Link','Evaluation Worksheets','DocType','Evaluation Worksheet',None,None),
            ('Link','Consensus Records','DocType','Evaluation Consensus Record',None,None),
            ('Link','Award Recommendations','DocType','Award Recommendation',None,None),
            ('Link','Award Decisions','DocType','Award Decision',None,None),
            ('Link','Challenge Cases','DocType','Challenge Review Case',None,None),
        ]
    },
    {
        'key':'contracts_execution','name':'KT Contracts & Execution','title':'Contracts & Execution','icon':'folder-open','color':'yellow','sequence':70,
        'shortcuts':[
            ('Contract Handoffs','Award Contract Handoff','List'),
            ('PO Handoffs','Award PO Handoff','List'),
            ('Supplier Performance Baseline','Supplier Performance Baseline','List'),
            ('Purchase Orders','Purchase Order','List'),
            ('Purchase Invoices','Purchase Invoice','List'),
        ],
        'quick_lists':[
            ('Award Contract Handoff','Ready for Contract','[["handoff_status","in",["Draft","Ready"]]]'),
            ('Award PO Handoff','Ready for PO','[["handoff_status","in",["Draft","Ready"]]]'),
            ('Purchase Order','Open Purchase Orders','[["status","not in",["Completed","Closed","Cancelled"]]]'),
        ],
        'link_cards':[
            ('Award Handoffs', [
                ('Award Contract Handoff','DocType','Award Contract Handoff'),
                ('Award PO Handoff','DocType','Award PO Handoff'),
                ('Supplier Performance Baseline','DocType','Supplier Performance Baseline'),
            ]),
            ('Execution', [
                ('Purchase Order','DocType','Purchase Order'),
                ('Purchase Invoice','DocType','Purchase Invoice'),
                ('Payment Entry','DocType','Payment Entry'),
            ]),
        ],
        'number_cards':[('Contract Handoffs Pending','KT Contract Handoffs Pending'),('Open Purchase Orders','KT Open Purchase Orders')],
        'sidebar':[
            ('Section Break','Execution Desk','file-text',None,None),
            ('Link','Dashboard','Workspace','KT Contracts & Execution',None,None),
            ('Link','Contract Handoffs','DocType','Award Contract Handoff',None,None),
            ('Link','PO Handoffs','DocType','Award PO Handoff',None,None),
            ('Link','Purchase Orders','DocType','Purchase Order',None,None),
            ('Link','Purchase Invoices','DocType','Purchase Invoice',None,None),
        ]
    },
    {
        'key':'oversight_audit','name':'KT Oversight & Audit','title':'Oversight & Audit','icon':'shield','color':'grey','sequence':80,
        'shortcuts':[
            ('Exception Register','Exception Register Entry','List'),
            ('Published Plans','Published Plan Record','List'),
            ('Award Publications','Award Publication Record','List'),
            ('User Permissions','User Permission','List'),
            ('Workflow Actions','Workflow Action','List'),
        ],
        'quick_lists':[
            ('Exception Register Entry','Open Exceptions','[["status","not in",["Closed","Resolved"]]]'),
            ('Challenge Review Case','Open Challenge Cases','[["status","not in",["Closed","Resolved"]]]'),
            ('Purchase Requisition Exception','Open Requisition Exceptions','[["status","not in",["Closed","Approved"]]]'),
        ],
        'link_cards':[
            ('Oversight Registers', [
                ('Exception Register Entry','DocType','Exception Register Entry'),
                ('Published Plan Record','DocType','Published Plan Record'),
                ('Award Publication Record','DocType','Award Publication Record'),
                ('Challenge Review Case','DocType','Challenge Review Case'),
            ]),
            ('Audit & Security', [
                ('User Permission','DocType','User Permission'),
                ('Role Permission Manager','Page','permission-manager'),
                ('Workflow Action','DocType','Workflow Action'),
                ('Activity Log','DocType','Activity Log'),
            ]),
        ],
        'number_cards':[('Open Exceptions','KT Open Exceptions'),('Open Challenge Cases','KT Open Challenge Cases')],
        'sidebar':[
            ('Section Break','Oversight Desk','shield',None,None),
            ('Link','Dashboard','Workspace','KT Oversight & Audit',None,None),
            ('Link','Exception Register','DocType','Exception Register Entry',None,None),
            ('Link','Challenge Cases','DocType','Challenge Review Case',None,None),
            ('Link','Workflow Actions','DocType','Workflow Action',None,None),
            ('Link','User Permissions','DocType','User Permission',None,None),
            ('Link','Role Permission Manager','Page','permission-manager',None,None),
        ]
    },
]


def mk_roles(role_names):
    return [{'doctype':'Has Role','role':r} for r in role_names]


def mk_shortcuts(shortcuts):
    out=[]
    for label, link_to, doc_view in shortcuts:
        out.append({
            'doctype':'Workspace Shortcut','type':'DocType','link_to':link_to,'doc_view':doc_view,
            'label':label,'icon':'','color':'blue' if doc_view=='New' else 'gray'
        })
    return out


def mk_quick_lists(qs):
    return [{'doctype':'Workspace Quick List','document_type':dt,'label':label,'quick_list_filter':flt} for dt,label,flt in qs]


def mk_number_cards(cards):
    return [{'doctype':'Workspace Number Card','number_card_name':card,'label':label} for label,card in cards]


def mk_links(cards):
    rows=[]
    for card_label, links in cards:
        rows.append({'doctype':'Workspace Link','type':'Card Break','label':card_label,'hidden':0,'icon':''})
        for label, link_type, link_to in links:
            row={'doctype':'Workspace Link','type':'Link','label':label,'link_type':link_type,'link_to':link_to}
            if link_type=='Report':
                row['is_query_report']=1
            rows.append(row)
    return rows


def mk_content(defn):
    blocks=[]
    blocks.append({'id':'header-main','type':'header','data':{'text':defn['title'],'level':2,'col':12}})
    blocks.append({'id':'header-shortcuts','type':'header','data':{'text':'Quick Actions','level':4,'col':12}})
    for i,(label,_,_) in enumerate(defn['shortcuts'],1):
        blocks.append({'id':f'shortcut-{i}','type':'shortcut','data':{'shortcut_name':label,'col':4}})
    blocks.append({'id':'header-queues','type':'header','data':{'text':'Queues & Monitoring','level':4,'col':12}})
    for i,(_,label,_) in enumerate(defn['quick_lists'],1):
        blocks.append({'id':f'quick-list-{i}','type':'quick_list','data':{'quick_list_name':label,'col':4}})
    blocks.append({'id':'header-insights','type':'header','data':{'text':'KPIs','level':4,'col':12}})
    for i,(label,_) in enumerate(defn['number_cards'],1):
        blocks.append({'id':f'number-card-{i}','type':'number_card','data':{'number_card_name':label,'col':3}})
    blocks.append({'id':'header-links','type':'header','data':{'text':'Navigation','level':4,'col':12}})
    for i,(card_label,_) in enumerate(defn['link_cards'],1):
        blocks.append({'id':f'links-{i}','type':'links','data':{'links_name':card_label,'col':6}})
    return json.dumps(blocks, separators=(',',':'))


def mk_workspace(defn):
    return {
        'doctype':'Workspace','name':defn['name'],'label':defn['name'],'title':defn['title'],'sequence_id':defn['sequence'],
        'module':MODULE,'app':APP,'type':'Workspace','public':1,'is_hidden':0,'icon':defn['icon'],'indicator_color':defn['color'],
        'content':mk_content(defn),'charts':[],'shortcuts':mk_shortcuts(defn['shortcuts']),'links':mk_links(defn['link_cards']),
        'quick_lists':mk_quick_lists(defn['quick_lists']),'number_cards':mk_number_cards(defn['number_cards']),'custom_blocks':[],
        'roles':mk_roles(roles[defn['key']])
    }


def mk_sidebar(defn):
    items=[]
    for entry in defn['sidebar']:
        if entry[0] == 'Section Break':
            _, label, icon, *rest = entry
            items.append({
                'doctype':'Workspace Sidebar Item',
                'type':'Section Break',
                'label':label,
                'icon':icon,
                'collapsible':1,
                'keep_closed':0
            })
        else:
            _, label, link_type, link_to, *rest = entry
            filters = rest[0] if len(rest) > 0 else None
            route_options = rest[1] if len(rest) > 1 else None
            item={
                'doctype':'Workspace Sidebar Item',
                'type':'Link',
                'label':label,
                'link_type':link_type,
                'link_to':link_to,
                'icon':''
            }
            if filters:
                item['filters']=filters
            if route_options:
                item['route_options']=route_options
            items.append(item)
    return {
        'doctype':'Workspace Sidebar','name':defn['title'],'title':defn['title'],'header_icon':defn['icon'],'module':MODULE,
        'standard':0,'app':APP,'items':items
    }


def mk_desktop_icon(defn):
    return {
        'doctype':'Desktop Icon','name':defn['title'],'label':defn['title'],'icon_type':'App','link_type':'Workspace Sidebar',
        'link_to':'Workspace Sidebar','sidebar':defn['title'],'standard':0,'app':APP,'icon':defn['icon'],'bg_color':'blue',
        'roles':mk_roles(roles[defn['key']]), 'hidden':0
    }

for d in workspace_defs:
    with open(os.path.join(base,'workspaces',f"{d['key']}.json"),'w') as f:
        json.dump(mk_workspace(d),f,indent=2)
    with open(os.path.join(base,'sidebars',f"{d['key']}_sidebar.json"),'w') as f:
        json.dump(mk_sidebar(d),f,indent=2)
    with open(os.path.join(base,'desktop_icons',f"{d['key']}_desktop_icon.json"),'w') as f:
        json.dump(mk_desktop_icon(d),f,indent=2)

readme = '''# KenTender ERPNext v16 Workspace Configs

This package contains custom **Workspace**, **Workspace Sidebar**, and **Desktop Icon** JSON configs for the KenTender modules built so far:

- Procurement Planning
- Requisitions
- Suppliers
- Tendering
- Submissions & Opening
- Evaluation & Award
- Contracts & Execution
- Oversight & Audit

## Design approach

These are **custom public workspaces** for ERPNext/Frappe v16, designed around task-oriented navigation rather than raw DocType exposure.

## Package contents

- `workspaces/` - importable Workspace records
- `sidebars/` - v16 Workspace Sidebar records
- `desktop_icons/` - desktop/app-launcher icons linked to sidebars
- `patches/` - optional helper script to upsert records in a custom app

## Recommended install path

1. Review DocType names and report names against your live app.
2. Rename any placeholder Number Cards or Reports to match your actual records.
3. Import into a staging site first using `bench --site <site> import-doc <path-to-json>`.
4. Clear cache and reload Desk after import.
5. Curate sidebar ordering and role restrictions in staging before production.

## Important v16 notes

- v16 uses a persistent sidebar powered by **Workspace Sidebar**.
- Standard workspace modifications can be lost across upgrades; these files are intended as **custom** records.
- Keep cross-module links deliberate, otherwise sidebar context can feel jumpy in v16.

## Placeholder records to create or map

Some blocks reference Number Cards / Reports that may not yet exist in your site, such as:

- `KT Planned APP Value`
- `KT APP Pending Approval`
- `KT Requisition Pending`
- `KT Requisition Commitment Value`
- `KT Active Suppliers`
- `KT Supplier Renewals Due`
- `KT Published Tenders`
- `KT Tenders Closing This Week`
- `KT Tender Submissions Received`
- `KT Late Bids`
- `KT Evaluations Pending`
- `KT Awards Awaiting Approval`
- `KT Contract Handoffs Pending`
- `KT Open Purchase Orders`
- `KT Open Exceptions`
- `KT Open Challenge Cases`

Replace these with your final Number Card names or remove them from the JSON.

## Optional app-based deployment

If you want these in source control, place the JSON records in your app and include them in fixtures or import them through a patch.
'''
with open(os.path.join(base,'README.md'),'w') as f:
    f.write(readme)

patch = '''import frappe
from pathlib import Path
import json

BASE = Path(__file__).resolve().parent.parent

def import_json(path):
    with open(path) as f:
        doc = frappe.get_doc(json.load(f))
    if frappe.db.exists(doc.doctype, doc.name):
        existing = frappe.get_doc(doc.doctype, doc.name)
        existing.update(doc.as_dict())
        existing.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)


def execute():
    for folder in ["workspaces", "sidebars", "desktop_icons"]:
        for path in sorted((BASE / folder).glob("*.json")):
            import_json(path)
    frappe.clear_cache()
'''
with open(os.path.join(base,'patches','create_kentender_workspaces.py'),'w') as f:
    f.write(patch)

print('generated')
