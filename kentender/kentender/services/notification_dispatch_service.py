# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Notification dispatch abstraction (STORY-CORE-022).

Resolves **Notification Template** rows, renders **subject** / **body** with Jinja
context, and hands off to pluggable per-channel backends. Default backends are
no-ops so no email/SMS gateways run until wired.

**Channels** must match **Notification Template** options: :data:`CHANNEL_IN_APP`,
:data:`CHANNEL_EMAIL`, :data:`CHANNEL_SMS`.

Call only from **server-side** code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import strip_html
from frappe.utils.jinja import render_template as render_jinja_template

NOTIFICATION_TEMPLATE_DOCTYPE = "Notification Template"

CHANNEL_IN_APP = "In-App"
CHANNEL_EMAIL = "Email"
CHANNEL_SMS = "SMS"


@dataclass
class NotificationPayload:
	"""Arguments passed to a channel backend."""

	channel: str
	recipient: str
	subject: str | None
	body: str
	event_name: str
	template_code: str | None
	metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelDeliveryResult:
	"""Outcome for one recipient on one channel."""

	ok: bool
	channel: str
	recipient: str
	detail: str | None = None
	error_code: str | None = None
	error_message: str | None = None


@dataclass
class NotificationDispatchResult:
	"""Aggregate result for a dispatch call."""

	ok: bool
	rendered_subject: str | None
	rendered_body: str
	template_code: str | None
	channel: str
	event_name: str
	deliveries: list[ChannelDeliveryResult] = field(default_factory=list)
	messages: list[str] = field(default_factory=list)


class NotificationChannelBackend(Protocol):
	"""Pluggable channel integration (email provider, SMS gateway, in-app feed)."""

	def deliver(self, payload: NotificationPayload) -> ChannelDeliveryResult:
		...


class NoOpNotificationBackend:
	"""Default backend: succeeds without calling external systems."""

	def deliver(self, payload: NotificationPayload) -> ChannelDeliveryResult:
		return ChannelDeliveryResult(
			ok=True,
			channel=payload.channel,
			recipient=payload.recipient,
			detail="noop_gateway_not_wired",
		)


def render_notification_content(
	subject_template: str | None,
	body_template: str,
	context: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
	"""Render *subject_template* and *body_template* with Jinja *context*."""
	ctx = dict(context or {})
	body = (body_template or "").strip()
	if not body:
		frappe.throw(_("Body template is empty."), frappe.ValidationError)

	rendered_body = render_jinja_template(body, ctx, is_path=False)
	subject = None
	if subject_template and str(subject_template).strip():
		subject = render_jinja_template(str(subject_template).strip(), ctx, is_path=False)
	return subject, rendered_body


def get_active_notification_template(
	event_name: str,
	channel: str,
	*,
	prefer_scope_type: str | None = None,
) -> Document | None:
	"""Load the newest active **Notification Template** for *event_name* and *channel*.

	If *prefer_scope_type* is set (``Global`` or ``Procuring Entity``), only templates
	with that scope are considered. Entity-specific targeting by procuring entity is
	not modeled on the DocType yet; callers may pass an explicit *template_doc* /
	*template_code* until a link field exists.
	"""
	ev = (event_name or "").strip()
	ch = (channel or "").strip()
	if not ev or not ch:
		return None

	filters: dict[str, Any] = {"event_name": ev, "channel": ch, "active": 1}
	if prefer_scope_type:
		filters["scope_type"] = prefer_scope_type.strip()

	rows = frappe.get_all(
		NOTIFICATION_TEMPLATE_DOCTYPE,
		filters=filters,
		pluck="name",
		order_by="modified desc",
		limit=1,
	)
	if not rows and prefer_scope_type:
		# Fall back to any active template for event/channel.
		rows = frappe.get_all(
			NOTIFICATION_TEMPLATE_DOCTYPE,
			filters={"event_name": ev, "channel": ch, "active": 1},
			pluck="name",
			order_by="modified desc",
			limit=1,
		)
	if not rows:
		return None
	return frappe.get_doc(NOTIFICATION_TEMPLATE_DOCTYPE, rows[0])


def get_notification_template_by_code(template_code: str) -> Document | None:
	"""Return active template by *template_code*, or ``None``."""
	code = (template_code or "").strip()
	if not code:
		return None
	name = frappe.db.get_value(
		NOTIFICATION_TEMPLATE_DOCTYPE,
		{"template_code": code, "active": 1},
		"name",
	)
	if not name:
		return None
	return frappe.get_doc(NOTIFICATION_TEMPLATE_DOCTYPE, name)


def _normalize_recipients(recipients: str | list[str]) -> list[str]:
	if isinstance(recipients, str):
		r = recipients.strip()
		return [r] if r else []
	out: list[str] = []
	for r in recipients:
		s = (r or "").strip()
		if s:
			out.append(s)
	return out


def _body_for_channel(channel: str, rendered_body: str) -> str:
	if channel == CHANNEL_SMS:
		return strip_html(rendered_body).strip()
	return rendered_body


def _resolve_backend(
	channel: str,
	backends: dict[str, NotificationChannelBackend] | None,
) -> NotificationChannelBackend:
	if backends and channel in backends:
		return backends[channel]
	return NoOpNotificationBackend()


def dispatch_notification(
	*,
	event_name: str,
	channel: str,
	recipients: str | list[str],
	context: dict[str, Any] | None = None,
	template_doc: Document | None = None,
	template_code: str | None = None,
	prefer_scope_type: str | None = None,
	backends: dict[str, NotificationChannelBackend] | None = None,
	metadata: dict[str, Any] | None = None,
) -> NotificationDispatchResult:
	"""Resolve template, render content, deliver via backend(s).

	Exactly one template source should be provided among *template_doc*,
	*template_code*, or implicit resolution via *event_name* + *channel*.
	"""
	ev = (event_name or "").strip()
	ch = (channel or "").strip()
	recs = _normalize_recipients(recipients)
	meta = dict(metadata or {})
	ctx = dict(context or {})

	msgs: list[str] = []
	if not ev:
		msgs.append(_("event_name is required."))
	if not ch:
		msgs.append(_("channel is required."))
	if not recs:
		msgs.append(_("At least one recipient is required."))
	if msgs:
		return NotificationDispatchResult(
			ok=False,
			rendered_subject=None,
			rendered_body="",
			template_code=None,
			channel=ch,
			event_name=ev,
			messages=msgs,
		)

	tpl: Document | None = template_doc
	if tpl is None and template_code:
		tpl = get_notification_template_by_code(template_code)
	if tpl is None:
		tpl = get_active_notification_template(ev, ch, prefer_scope_type=prefer_scope_type)

	if tpl is None:
		return NotificationDispatchResult(
			ok=False,
			rendered_subject=None,
			rendered_body="",
			template_code=None,
			channel=ch,
			event_name=ev,
			messages=[_("No active notification template found.")],
		)

	try:
		subject, body = render_notification_content(
			tpl.subject_template,
			tpl.body_template or "",
			ctx,
		)
	except Exception as e:
		return NotificationDispatchResult(
			ok=False,
			rendered_subject=None,
			rendered_body="",
			template_code=tpl.template_code,
			channel=ch,
			event_name=ev,
			messages=[str(e)],
		)

	body_out = _body_for_channel(ch, body)
	backend = _resolve_backend(ch, backends)
	deliveries: list[ChannelDeliveryResult] = []
	all_ok = True
	tcode = (tpl.template_code or "").strip() or None

	for rcpt in recs:
		payload = NotificationPayload(
			channel=ch,
			recipient=rcpt,
			subject=subject,
			body=body_out,
			event_name=ev,
			template_code=tcode,
			metadata=meta,
		)
		try:
			out = backend.deliver(payload)
		except Exception as e:
			out = ChannelDeliveryResult(
				ok=False,
				channel=ch,
				recipient=rcpt,
				error_code="backend_exception",
				error_message=str(e),
			)
		deliveries.append(out)
		if not out.ok:
			all_ok = False

	return NotificationDispatchResult(
		ok=all_ok,
		rendered_subject=subject,
		rendered_body=body_out,
		template_code=tcode,
		channel=ch,
		event_name=ev,
		deliveries=deliveries,
		messages=msgs,
	)
