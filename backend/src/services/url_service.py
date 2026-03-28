"""URL metadata fetching service."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 10.0
MAX_CONTENT_LENGTH = 500_000  # 500KB limit for HTML content


@dataclass
class UrlMetadata:
    """Parsed metadata from a URL."""

    title: str
    description: str
    thumbnail: str | None
    content: str


async def fetch_url_metadata(url: str) -> UrlMetadata:
    """Fetch and parse metadata from a URL.

    Extracts Open Graph meta tags (og:title, og:description, og:image)
    and page content.

    Args:
        url: The URL to fetch metadata from.

    Returns:
        UrlMetadata with parsed fields. Fields default to empty string on failure.
    """
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "LINE-AI-Secretary/1.0"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                logger.info("Non-HTML content type: %s for %s", content_type, url)
                return UrlMetadata(title=url, description="", thumbnail=None, content="")

            html = resp.text[:MAX_CONTENT_LENGTH]
            return _parse_html_metadata(html, url)

    except httpx.HTTPStatusError as e:
        logger.warning("HTTP error fetching %s: %s", url, e.response.status_code)
        return UrlMetadata(title=url, description="", thumbnail=None, content="")
    except Exception:
        logger.exception("Failed to fetch URL metadata: %s", url)
        return UrlMetadata(title=url, description="", thumbnail=None, content="")


def _parse_html_metadata(html: str, url: str) -> UrlMetadata:
    """Parse OG meta tags and basic content from HTML string."""
    title = _extract_meta(html, "og:title") or _extract_title(html) or url
    description = _extract_meta(html, "og:description") or _extract_meta_name(html, "description") or ""
    thumbnail = _extract_meta(html, "og:image") or None

    # Extract visible text content (simplified)
    content = _extract_text_content(html)

    return UrlMetadata(
        title=title,
        description=description,
        thumbnail=thumbnail,
        content=content,
    )


def _extract_meta(html: str, property_name: str) -> str:
    """Extract content from <meta property="..." content="..."> tag."""
    pattern = rf'<meta\s+[^>]*property=["\']({re.escape(property_name)})["\'][^>]*content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(2).strip()

    # Try reversed attribute order: content before property
    pattern_rev = rf'<meta\s+[^>]*content=["\']([^"\']*)["\'][^>]*property=["\']({re.escape(property_name)})["\']'
    match_rev = re.search(pattern_rev, html, re.IGNORECASE)
    if match_rev:
        return match_rev.group(1).strip()

    return ""


def _extract_meta_name(html: str, name: str) -> str:
    """Extract content from <meta name="..." content="..."> tag."""
    pattern = rf'<meta\s+[^>]*name=["\']({re.escape(name)})["\'][^>]*content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return ""


def _extract_title(html: str) -> str:
    """Extract content from <title> tag."""
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _extract_text_content(html: str) -> str:
    """Extract visible text content from HTML (simplified)."""
    # Remove script and style tags
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Limit length
    return text[:2000]
