from django.test import TestCase
from django.urls import reverse

from clickify.models import ClickLog, TrackedLink


class RefParameterTest(TestCase):
    def setUp(self):
        self.link = TrackedLink.objects.create(
            slug="test-slug", target_url="https://example.com"
        )

    def test_click_with_ref_get(self):
        """Test GET request with string ref parameter"""
        url = reverse("clickify:track_click", args=[self.link.slug])
        response = self.client.get(f"{url}?ref=my_campaign")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.link.target_url)

        log = ClickLog.objects.last()
        self.assertEqual(log.ref, "my_campaign")
        self.assertEqual(log.target, self.link)

    def test_click_with_ref_post(self):
        """Test POST request with string ref parameter"""
        url = reverse("clickify:track_click", args=[self.link.slug])
        response = self.client.post(url, {"ref": "post_campaign"})

        self.assertEqual(response.status_code, 302)
        log = ClickLog.objects.last()
        self.assertEqual(log.ref, "post_campaign")
        self.assertEqual(log.target, self.link)

    def test_click_with_ref_bytes(self):
        """Test GET request with bytes input for ref"""
        url = reverse("clickify:track_click", args=[self.link.slug])
        # Simulate bytes input by encoding to UTF-8
        response = self.client.get(f"{url}?ref={b'byte_campaign'.decode()}")

        self.assertEqual(response.status_code, 302)
        log = ClickLog.objects.last()
        self.assertEqual(log.ref, "byte_campaign")
        self.assertEqual(log.target, self.link)

    def test_click_with_ref_integer(self):
        """Test GET request with integer input for ref"""
        url = reverse("clickify:track_click", args=[self.link.slug])
        response = self.client.get(f"{url}?ref=123")

        self.assertEqual(response.status_code, 302)
        log = ClickLog.objects.last()
        self.assertEqual(log.ref, "123")  # Should be stored as string
        self.assertEqual(log.target, self.link)

    def test_click_without_ref(self):
        """Test request without ref parameter"""
        url = reverse("clickify:track_click", args=[self.link.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        log = ClickLog.objects.last()
        self.assertIsNone(log.ref)
        self.assertEqual(log.target, self.link)
