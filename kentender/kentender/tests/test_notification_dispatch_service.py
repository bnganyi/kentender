# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

from unittest.mock import MagicMock

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender.services.notification_dispatch_service import (
	CHANNEL_EMAIL,
	CHANNEL_IN_APP,
	CHANNEL_SMS,
	ChannelDeliveryResult,
	NotificationPayload,
	dispatch_notification,
	get_active_notification_template,
	get_notification_template_by_code,
	render_notification_content,
)

TEMPLATE_DOCTYPE = "Notification Template"


class TestNotificationDispatchService(FrappeTestCase):
	def tearDown(self):
		frappe.db.delete(TEMPLATE_DOCTYPE, {"template_code": ("like", "_KT_ND_%")})
		frappe.db.commit()
		super().tearDown()

	def _insert_template(self, **kwargs):
		data = {
			"doctype": TEMPLATE_DOCTYPE,
			"template_code": "_KT_ND_001",
			"template_name": "Dispatch test",
			"channel": CHANNEL_EMAIL,
			"event_name": "nd.test.event",
			"scope_type": "Global",
			"subject_template": "Hi {{ name }}",
			"body_template": "<p>Hello {{ name }}</p>",
		}
		data.update(kwargs)
		doc = frappe.get_doc(data)
		doc.insert()
		return doc

	def test_render_notification_content(self):
		sub, body = render_notification_content(
			"Subject {{ name }}",
			"<b>{{ name }}</b>",
			{"name": "Ada"},
		)
		self.assertEqual(sub, "Subject Ada")
		self.assertIn("Ada", body)

	def test_render_notification_content_empty_body_raises(self):
		self.assertRaises(frappe.ValidationError, render_notification_content, None, "   ", {})

	def test_get_active_notification_template(self):
		self._insert_template()
		doc = get_active_notification_template("nd.test.event", CHANNEL_EMAIL)
		self.assertIsNotNone(doc)
		self.assertEqual(doc.template_code, "_KT_ND_001")

	def test_get_notification_template_by_code(self):
		self._insert_template(template_code="_KT_ND_BYCODE")
		doc = get_notification_template_by_code("_KT_ND_BYCODE")
		self.assertIsNotNone(doc)
		self.assertEqual(doc.event_name, "nd.test.event")

	def test_dispatch_no_template(self):
		res = dispatch_notification(
			event_name="missing.event",
			channel=CHANNEL_EMAIL,
			recipients="a@example.com",
			context={"name": "X"},
		)
		self.assertFalse(res.ok)
		self.assertEqual(res.deliveries, [])

	def test_dispatch_with_noop_backend(self):
		self._insert_template()
		res = dispatch_notification(
			event_name="nd.test.event",
			channel=CHANNEL_EMAIL,
			recipients=["u1@example.com", "u2@example.com"],
			context={"name": "Bo"},
		)
		self.assertTrue(res.ok)
		self.assertEqual(res.template_code, "_KT_ND_001")
		self.assertEqual(res.rendered_subject, "Hi Bo")
		self.assertEqual(len(res.deliveries), 2)
		for d in res.deliveries:
			self.assertTrue(d.ok)
			self.assertEqual(d.detail, "noop_gateway_not_wired")

	def test_dispatch_with_mock_backend(self):
		self._insert_template()
		mock_backend = MagicMock()
		mock_backend.deliver.return_value = ChannelDeliveryResult(
			ok=True,
			channel=CHANNEL_EMAIL,
			recipient="x@example.com",
			detail="mock_sent",
		)
		res = dispatch_notification(
			event_name="nd.test.event",
			channel=CHANNEL_EMAIL,
			recipients="x@example.com",
			context={"name": "Zed"},
			backends={CHANNEL_EMAIL: mock_backend},
		)
		self.assertTrue(res.ok)
		mock_backend.deliver.assert_called_once()
		call_arg = mock_backend.deliver.call_args[0][0]
		self.assertIsInstance(call_arg, NotificationPayload)
		self.assertEqual(call_arg.recipient, "x@example.com")
		self.assertEqual(call_arg.subject, "Hi Zed")

	def test_sms_channel_strips_html(self):
		self._insert_template(
			template_code="_KT_ND_SMS",
			channel=CHANNEL_SMS,
			body_template="<p>Plain {{ name }}</p>",
			subject_template="",
		)
		res = dispatch_notification(
			event_name="nd.test.event",
			channel=CHANNEL_SMS,
			recipients="+254700000000",
			context={"name": "text"},
		)
		self.assertTrue(res.ok)
		self.assertNotIn("<p>", res.rendered_body)
		self.assertIn("text", res.rendered_body)

	def test_backend_exception_becomes_failed_delivery(self):
		self._insert_template(
			template_code="_KT_ND_IA",
			channel=CHANNEL_IN_APP,
			event_name="nd.test.inapp",
		)

		class Boom:
			def deliver(self, payload):
				raise RuntimeError("simulated failure")

		res = dispatch_notification(
			event_name="nd.test.inapp",
			channel=CHANNEL_IN_APP,
			recipients="Administrator",
			context={"name": "Q"},
			backends={CHANNEL_IN_APP: Boom()},
		)
		self.assertFalse(res.ok)
		self.assertEqual(len(res.deliveries), 1)
		self.assertFalse(res.deliveries[0].ok)
		self.assertEqual(res.deliveries[0].error_code, "backend_exception")
