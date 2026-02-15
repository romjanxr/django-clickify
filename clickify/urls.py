from django.urls import path

from .views import track_click

app_name = "clickify"

urlpatterns = [
    # Canonical URL (used by reverse/track_url).
    path("<slug:slug>/", track_click, name="track_click"),
    # Backward-compatible alias without trailing slash.
    path("<slug:slug>", track_click),
]
