import ipaddress
import json
from urllib.error import ContentTooShortError, HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .models import ClickLog

# ------------------- IP & Rate Limit -------------------


def get_client_ip(request):
    """Get the client IP address from the request, considering common proxy headers.

    Returns:
        (ip: str, is_routable: bool)

    """
    # Headers to check in order of preference
    ip_headers = getattr(
        settings,
        "CLICKIFY_IP_HEADERS",
        [
            "HTTP_X_FORWARDED_FOR",
            "HTTP_X_REAL_IP",
            "HTTP_X_FORWARDED",
            "HTTP_X_CLUSTER_CLIENT_IP",
            "HTTP_FORWARDED_FOR",
            "HTTP_FORWARDED",
            "REMOTE_ADDR",
        ],
    )

    def is_routable_ip(ip):
        """Check if an IP is public/routable."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            # Returns True if public, False if private, loopback, link-local, reserved, unspecified
            return not (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            )
        except ValueError:
            return False  # Invalid IP

    for header in ip_headers:
        ip_list = request.META.get(header, "")
        if ip_list:
            # Some headers can contain multiple IPs (comma separated)
            for ip in [ip.strip() for ip in ip_list.split(",")]:
                if ip and ip.lower() != "unknown":
                    return ip, is_routable_ip(ip)

    # Fallback
    ip = request.META.get("REMOTE_ADDR", "")
    return ip, is_routable_ip(ip) if ip else False


def get_ratelimit_ip(group, request):
    """Custom key for django-ratelimit using IP logic"""
    ip, _ = get_client_ip(request)
    return ip or "anonymous"


# ------------------- GeoIP -------------------


def get_geoip(ip):
    """Fetch geolocation data for the IP from ip-api.com"""
    url = f"http://ip-api.com/json/{ip}?fields=status,country,city"
    try:
        req = Request(url, headers={"User-Agent": "clickify/1.0"})
        with urlopen(req, timeout=2) as response:
            return json.load(response)
    except (URLError, HTTPError, ContentTooShortError, json.JSONDecodeError):
        return {}


def get_geolocation(ip_address):
    """Get country and city for a given IP address"""
    # Geolocation can be disabled globally in settings
    if not getattr(settings, "CLICKIFY_GEOLOCATION", True) or not ip_address:
        return None, None

    data = get_geoip(ip_address)
    if data.get("status") == "success":
        return data.get("country"), data.get("city")
    return None, None


# ------------------- Safe Parameter Fetch -------------------


def get_request_param(request, key):
    """Safely fetch a parameter from GET or POST and return it as a string or None.

    Args:
        request: Django HttpRequest object
        key (str): Parameter name

    Returns:
        str or None

    """
    value = request.GET.get(key) or request.POST.get(key) or None

    if isinstance(value, bytes | bytearray):
        value = value.decode("utf-8", errors="ignore")
    elif value is not None and not isinstance(value, str):
        value = str(value)

    return value


# ------------------- Click Log -------------------


def create_click_log(target, request):
    """Create a ClickLog object.

    This contains the core tracking logic that can be reused by both the
    standard view and the DRF API view.
    """
    ip, is_routable = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    country, city = (None, None)
    if is_routable:
        country, city = get_geolocation(ip)

    ref = get_request_param(request, "ref")
    ClickLog.objects.create(
        target=target,
        ip_address=ip,
        user_agent=user_agent,
        country=country,
        city=city,
        ref=ref,
    )
