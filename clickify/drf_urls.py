from django.urls import path

from .drf_views import TrackClickAPIView

app_name = "clickify-drf"

urlpatterns = [
    # Canonical URL (used by reverse).
    path("<slug:slug>/", TrackClickAPIView.as_view(), name="track_click_api"),
    # Backward-compatible alias without trailing slash.
    path("<slug:slug>", TrackClickAPIView.as_view()),
]
