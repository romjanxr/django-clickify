import uuid

from django.db import models


class TrackedLink(models.Model):
    """Represents a link that can be tracked.

    This model decouples the link from its actual URL,
      allowing the URL to change without losing the click history.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        help_text="A user-friendly name for tracked link, e.g., Monthly Report PDF",
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="A unique slug for the URL. E.g., 'monthly-report-pdf' ",
    )
    target_url = models.URLField(
        max_length=2048,
        help_text="The actual URL to the destination (e.g., on S3, a blog post, an affiliate link, etc.) - Not mandatory",
        blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ClickLog(models.Model):
    """Logs a single click event for a TrackedLink."""

    target = models.ForeignKey(
        TrackedLink, on_delete=models.CASCADE, related_name="clicks"
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    ref = models.TextField(default="",blank=True, null=True)

    def __str__(self):
        return f"Click on {self.target.name} at {self.timestamp}"
