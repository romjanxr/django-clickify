import re

from django.conf import settings
from django.core.cache import cache

from .exceptions import handle_ratelimited_exception
from .utils import get_ratelimit_ip


class Ratelimited(Exception):
    """Fallback exception when django-ratelimit is unavailable."""


def _rate_to_seconds(rate):
    """Convert a rate like `5/m` into `(count, seconds)`."""
    match = re.match(r"^\s*(\d+)\s*/\s*([smhd])\s*$", str(rate))
    if not match:
        return None

    count = int(match.group(1))
    unit = match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return count, multipliers[unit]


def conditional_ratelimit(view_func):
    """Apply rate limiting only when enabled."""
    if not getattr(settings, "CLICKIFY_ENABLE_RATELIMIT", True):
        return view_func

    try:
        from django_ratelimit.decorators import ratelimit
        from django_ratelimit.exceptions import Ratelimited as DjangoRatelimited

        ratelimit_available = True
    except ImportError:
        ratelimit = None
        DjangoRatelimited = Ratelimited
        ratelimit_available = False

    def wrapper(request, *args, **kwargs):
        try:
            if ratelimit_available:
                decorated_view = ratelimit(
                    key=get_ratelimit_ip,
                    rate=lambda r, g: getattr(settings, "CLICKIFY_RATE_LIMIT", "5/m"),
                    block=True,
                )(view_func)
                return decorated_view(request, *args, **kwargs)

            parsed = _rate_to_seconds(getattr(settings, "CLICKIFY_RATE_LIMIT", "5/m"))
            if parsed:
                limit, window_seconds = parsed
                ip = get_ratelimit_ip(None, request)
                cache_key = (
                    f"clickify:ratelimit:{view_func.__module__}."
                    f"{view_func.__qualname__}:{ip}"
                )
                hits = cache.get(cache_key, 0) + 1
                cache.set(cache_key, hits, timeout=window_seconds)
                if hits > limit:
                    raise Ratelimited

            return view_func(request, *args, **kwargs)
        except DjangoRatelimited:
            if hasattr(request, "accepted_renderer"):
                raise
            return handle_ratelimited_exception(request)

    return wrapper
