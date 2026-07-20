from __future__ import annotations

from urllib.parse import urlsplit

from bid_screenshot_assistant.adapters.profiles import PlatformBrowserProfile


class UnsafeNavigationError(ValueError):
    """Raised when a platform adapter attempts to leave its verified web boundary."""


def validate_navigation_url(profile: PlatformBrowserProfile, url: str) -> str:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")

    if parsed.scheme != "https":
        raise UnsafeNavigationError("Only HTTPS navigation is permitted")
    if parsed.username or parsed.password:
        raise UnsafeNavigationError("Credentials must not be embedded in URLs")
    if parsed.port not in (None, 443):
        raise UnsafeNavigationError("Non-standard ports are not permitted")
    if hostname not in profile.allowed_hosts:
        raise UnsafeNavigationError(
            f"Host {hostname or '<missing>'} is outside the {profile.platform_id} allowlist"
        )

    return url


def validate_detail_url(profile: PlatformBrowserProfile, url: str) -> str:
    validate_navigation_url(profile, url)
    if not profile.matches_detail_url(url):
        raise UnsafeNavigationError(
            f"URL does not match a verified detail pattern for {profile.platform_id}"
        )
    return url
