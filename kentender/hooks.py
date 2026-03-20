doc_events = {
	"Procurement Plan": {
		"before_insert": "kentender.kentender.api.phase1_procurement_plan_before_insert",
		"validate": "kentender.kentender.api.phase1_procurement_plan_validate",
		"on_submit": "kentender.kentender.api.phase1_procurement_plan_on_submit",
		"on_update_after_submit": "kentender.kentender.api.phase1_procurement_plan_on_update_after_submit",
	},
	"Procurement Plan Item": {
		"validate": "kentender.kentender.api.validate_plan_item",
	},
	"Procurement Plan Revision": {
		"validate": "kentender.kentender.api.phase1_procurement_plan_revision_validate",
		"on_update": "kentender.kentender.api.phase1_procurement_plan_revision_on_update",
	},
	"Contract": {
		"validate": "kentender.kentender.api.validate_contract",
		"on_update": "kentender.kentender.api.seed_contract_milestones_on_contract_activation",
	},
	"Contract Closeout Archive": {
		"validate": "kentender.kentender.api.validate_contract_closeout_archive",
		"on_trash": "kentender.kentender.api.prevent_delete_contract_closeout_archive",
	},
	"Governance Session": {
		"validate": "kentender.kentender.api.validate_governance_session",
	},
	"Session Agenda Item": {
		"validate": "kentender.kentender.api.validate_session_agenda_item",
	},
	"Session Resolution": {
		"validate": "kentender.kentender.api.validate_session_resolution",
	},
	"Session Action": {
		"validate": "kentender.kentender.api.validate_session_action",
	},
	"Session Participant": {
		"validate": "kentender.kentender.api.validate_session_participant",
	},
	"Session Evidence": {
		"validate": "kentender.kentender.api.validate_session_evidence",
	},
	"Session Signature": {
		"validate": "kentender.kentender.api.validate_session_signature",
	},
	"Acceptance Certificate": {
		"validate": "kentender.kentender.api.validate_acceptance_certificate",
	},
	"Contract Implementation Team Member": {
		"validate": "kentender.kentender.api.validate_cit_member",
	},
	"Inspection Committee Member": {
		"validate": "kentender.kentender.api.validate_inspection_committee_member",
	},
	"Contract Variation": {
		"validate": "kentender.kentender.api.validate_contract_variation",
		"on_submit": "kentender.kentender.api.apply_contract_variation",
	},
	"Termination Record": {
		"validate": "kentender.kentender.api.validate_termination_record",
		"on_submit": "kentender.kentender.api.apply_termination_record",
	},
	"Defect Liability Case": {
		"validate": "kentender.kentender.api.validate_defect_liability_case",
		"on_update": "kentender.kentender.api.handle_defect_liability_case_update",
	},
	"Claim": {
		"validate": "kentender.kentender.api.validate_claim",
	},
	"Dispute Case": {
		"validate": "kentender.kentender.api.validate_dispute_case",
	},
	"KenTender Audit Event": {
		"validate": "kentender.kentender.api.validate_ken_tender_audit_event",
		"on_trash": "kentender.kentender.api.prevent_delete_ken_tender_audit_event",
	},
	"Task": {
		"validate": "kentender.kentender.api.validate_task_milestone",
		"on_update": "kentender.kentender.api.maybe_create_inspection_test_plan_for_milestone",
	},
	"Inspection Test Plan": {
		"validate": "kentender.kentender.api.validate_inspection_test_plan",
	},
	"Inspection Report": {
		"validate": "kentender.kentender.api.validate_inspection_report",
		"before_submit": "kentender.kentender.api.before_submit_inspection_report",
	},
	"Quality Inspection": {
		"validate": "kentender.kentender.api.validate_quality_inspection_clm",
	},
	"Tender Submission": {
		"validate": "kentender.kentender.api.validate_submission",
		"after_insert": "kentender.kentender.api.audit_tender_submission_created",
	},
	"Purchase Invoice": {
		"validate": "kentender.kentender.api.validate_purchase_invoice_certificate",
		"on_submit": "kentender.kentender.api.create_retention_ledger_entry_from_invoice",
	},
	"Payment Entry": {
		"validate": "kentender.kentender.api.validate_payment_entry_clm",
		"before_submit": "kentender.kentender.api.before_submit_payment_entry_clm",
	},
	"Purchase Requisition": {
		"validate": "kentender.kentender.api.phase1_validate_purchase_requisition",
		"on_update": "kentender.kentender.api.phase1_on_update_purchase_requisition",
	},
	"Purchase Requisition Amendment": {
		"on_submit": "kentender.kentender.api.phase15_on_submit_purchase_requisition_amendment",
	},
	"Tender": {
		"on_submit": "kentender.kentender.api.validate_tender",
	},
	"Monthly Contract Monitoring Report": {
		"validate": "kentender.kentender.api.validate_monthly_contract_monitoring_report",
	},
}

scheduler_events = {
	"daily": [
		"kentender.kentender.api.recheck_supplier_compliance",
		"kentender.kentender.api.monitor_dlp_expiry",
		"kentender.kentender.api.remind_retention_release_due",
	],
	"monthly": [
		"kentender.kentender.api.create_monthly_contract_monitoring_reports",
	],
}

after_migrate = "kentender.kentender.api.phase1_after_migrate_setup"
app_name = "kentender"
app_title = "KenTender"
app_publisher = "Midas"
app_description = "Public eProcurement System"
app_email = "bnganyi@yahoo.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kentender",
# 		"logo": "/assets/kentender/logo.png",
# 		"title": "KenTender",
# 		"route": "/kentender",
# 		"has_permission": "kentender.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kentender/css/kentender.css"
# app_include_js = "/assets/kentender/js/kentender.js"

# include js, css files in header of web template
# web_include_css = "/assets/kentender/css/kentender.css"
# web_include_js = "/assets/kentender/js/kentender.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "kentender/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "kentender.utils.jinja_methods",
# 	"filters": "kentender.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender.install.before_install"
# after_install = "kentender.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kentender.uninstall.before_uninstall"
# after_uninstall = "kentender.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender.utils.before_app_install"
# after_app_install = "kentender.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender.utils.before_app_uninstall"
# after_app_uninstall = "kentender.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"kentender.tasks.all"
# 	],
# 	"daily": [
# 		"kentender.tasks.daily"
# 	],
# 	"hourly": [
# 		"kentender.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kentender.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kentender.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kentender.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kentender.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kentender.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kentender.utils.before_request"]
# after_request = ["kentender.utils.after_request"]

# Job Events
# ----------
# before_job = ["kentender.utils.before_job"]
# after_job = ["kentender.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"kentender.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

