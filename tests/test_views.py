from unittest.mock import patch

from django.contrib import messages
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from clickify.models import TrackedLink


@patch("clickify.utils.get_client_ip", return_value=("123.123.123.123", True))
@patch("clickify.utils.get_geolocation", return_value=("Test Country", "Test City"))
class TrackClickViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.target = TrackedLink.objects.create(
            name="Test File",
            slug="test-file",
            target_url="https://example.com/test-file.zip",
        )

    def test_click_creates_log_and_redirects(
        self, mock_get_geolocation, mock_get_client_ip
    ):
        self.assertEqual(self.target.clicks.count(), 0)

        url = reverse("clickify:track_click", kwargs={"slug": self.target.slug})

        # We can set a specific user agent for the test client
        user_agent = "Test User Agent 1.0"
        response = self.client.get(url, HTTP_USER_AGENT=user_agent)

        # Check for successfull redirects
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.target.target_url)

        # Check that the click was recorded
        self.assertEqual(self.target.clicks.count(), 1)

        # Check the created object in detail
        click = self.target.clicks.first()
        self.assertIsNotNone(click)
        self.assertEqual(click.target, self.target)
        # default ip for the test client
        self.assertEqual(click.ip_address, "123.123.123.123")
        self.assertEqual(click.user_agent, user_agent)
        self.assertEqual(click.country, "Test Country")  # check for mock data
        self.assertEqual(click.city, "Test City")  # check for mock data

    def test_nonexistent_slug(self, mock_get_geolocation, mock_get_client_ip):
        url = reverse("clickify:track_click", kwargs={"slug": "nonexistent-slug"})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(
        CLICKIFY_RATE_LIMIT="1/m",
        CLICKIFY_ENABLE_RATELIMIT=True,
    )
    def test_rate_limit_exceeded(self, mock_get_geolocation, mock_get_client_ip):
        url = reverse("clickify:track_click", kwargs={"slug": self.target.slug})

        # First request should succeed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Second request should be blocked and redirect back
        response = self.client.get(url, HTTP_REFERER="/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

        # Check for the error message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertIn("too many requests", str(messages_list[0]).lower())

    @override_settings(
        CLICKIFY_RATE_LIMIT="1/m",
        CLICKIFY_ENABLE_RATELIMIT=False,
    )
    def test_rate_limit_disabled(self, mock_get_geolocation, mock_get_client_ip):
        url = reverse("clickify:track_click", kwargs={"slug": self.target.slug})

        # Both requests should succeed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_track_click_works_without_trailing_slash(
        self, mock_get_geolocation, mock_get_client_ip
    ):
        response = self.client.get(f"/track/{self.target.slug}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.target.target_url)
