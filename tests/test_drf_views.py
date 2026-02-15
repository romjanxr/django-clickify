from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from clickify.models import TrackedLink


@patch("clickify.utils.get_client_ip", return_value=("123.123.123.123", True))
@patch("clickify.utils.get_geolocation", return_value=("Test Country", "Test City"))
class TrackClickAPIViewTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.target = TrackedLink.objects.create(
            name="Test API File",
            slug="test-api-file",
            target_url="https://example.com/test-api-file.zip",
        )

    def test_track_click_api_success(self, mock_get_geolocation, mock_get_client_ip):
        self.assertEqual(self.target.clicks.count(), 0)
        url = reverse("clickify-drf:track_click_api", kwargs={"slug": self.target.slug})

        user_agent = "Test API User Agent 1.0"
        response = self.client.post(url, HTTP_USER_AGENT=user_agent)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("target_url"), self.target.target_url)
        self.assertEqual(self.target.clicks.count(), 1)

        click = self.target.clicks.first()
        self.assertEqual(click.target, self.target)
        self.assertEqual(click.ip_address, "123.123.123.123")
        self.assertEqual(click.user_agent, user_agent)
        self.assertEqual(click.country, "Test Country")
        self.assertEqual(click.city, "Test City")

    def test_track_click_api_nonexistent_slug(
        self, mock_get_geolocation, mock_get_client_ip
    ):
        url = reverse(
            "clickify-drf:track_click_api", kwargs={"slug": "nonexistent-slug"}
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    @override_settings(
        CLICKIFY_RATE_LIMIT="1/m",
        CLICKIFY_ENABLE_RATELIMIT=True,
    )
    def test_track_click_api_rate_limit_exceeded(
        self, mock_get_geolocation, mock_get_client_ip
    ):
        url = reverse("clickify-drf:track_click_api", kwargs={"slug": self.target.slug})

        # First request should be succeed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

        # Second request should be blocked
        response = self.client.post(url)
        self.assertEqual(response.status_code, 429)
        response_data = response.json()
        self.assertIn("error", response_data)
        self.assertIn("too many requests", response_data["error"].lower())

    @override_settings(
        CLICKIFY_RATE_LIMIT="1/m",
        CLICKIFY_ENABLE_RATELIMIT=False,
    )
    def test_track_click_api_rate_limit_disabled(
        self, mock_get_geolocation, mock_get_client_ip
    ):
        url = reverse("clickify-drf:track_click_api", kwargs={"slug": self.target.slug})

        # Both requests should succeed
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_track_click_api_works_without_trailing_slash(
        self, mock_get_geolocation, mock_get_client_ip
    ):
        response = self.client.post(f"/api/track/{self.target.slug}")
        self.assertEqual(response.status_code, 200)
