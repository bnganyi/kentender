app_name = "kentender_assets"
app_title = "Kentender Assets"
app_publisher = "Midas"
app_description = "KenTender assets module."
app_email = "bnganyi@yahoo.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "kentender_assets",
# 		"logo": "/assets/kentender_assets/logo.png",
# 		"title": "Kentender Assets",
# 		"route": "/kentender_assets",
# 		"has_permission": "kentender_assets.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/kentender_assets/css/kentender_assets.css"
# app_include_js = "/assets/kentender_assets/js/kentender_assets.js"

# include js, css files in header of web template
# web_include_css = "/assets/kentender_assets/css/kentender_assets.css"
# web_include_js = "/assets/kentender_assets/js/kentender_assets.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "kentender_assets/public/scss/website"

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
# app_include_icons = "kentender_assets/public/icons.svg"

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
# 	"methods": "kentender_assets.utils.jinja_methods",
# 	"filters": "kentender_assets.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "kentender_assets.install.before_install"
# after_install = "kentender_assets.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "kentender_assets.uninstall.before_uninstall"
# after_uninstall = "kentender_assets.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "kentender_assets.utils.before_app_install"
# after_app_install = "kentender_assets.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "kentender_assets.utils.before_app_uninstall"
# after_app_uninstall = "kentender_assets.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "kentender_assets.notifications.get_notification_config"

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
# 		"kentender_assets.tasks.all"
# 	],
# 	"daily": [
# 		"kentender_assets.tasks.daily"
# 	],
# 	"hourly": [
# 		"kentender_assets.tasks.hourly"
# 	],
# 	"weekly": [
# 		"kentender_assets.tasks.weekly"
# 	],
# 	"monthly": [
# 		"kentender_assets.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "kentender_assets.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "kentender_assets.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "kentender_assets.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "kentender_assets.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["kentender_assets.utils.before_request"]
# after_request = ["kentender_assets.utils.after_request"]

# Job Events
# ----------
# before_job = ["kentender_assets.utils.before_job"]
# after_job = ["kentender_assets.utils.after_job"]

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
# 	"kentender_assets.auth.validate"
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

