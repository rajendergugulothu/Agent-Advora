"""
Instagram Graph API service.

Handles:
- OAuth token exchange and refresh
- Single image posting
- Carousel posting
- Fetching post insights (impressions, reach, likes, etc.)
- Fetching account profile info
"""

from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_token

log = get_logger(__name__)
settings = get_settings()

_GRAPH_BASE = "https://graph.facebook.com/v21.0"
_TIMEOUT = httpx.Timeout(60.0)

# Insights fields available on Instagram media objects
_INSIGHTS_FIELDS = "impressions,reach,likes,comments,shares,saved"
_CAROUSEL_CONTAINER_WAIT_SECONDS = 30


# ── OAuth ─────────────────────────────────────────────────────────────────────

async def exchange_code_for_token(code: str) -> dict:
    """
    Exchange a Meta OAuth authorization code for a short-lived user token.
    Returns the full response dict from Meta.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_GRAPH_BASE}/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": str(settings.meta_oauth_redirect_uri),
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()


async def exchange_for_long_lived_token(short_token: str) -> dict:
    """
    Exchange a short-lived token for a 60-day long-lived token.
    Returns dict with access_token and expires_in (seconds).
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_GRAPH_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_long_lived_token(long_lived_token: str) -> dict:
    """
    Refresh an existing long-lived token before it expires.
    Meta allows refreshing tokens that are at least 24h old.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_GRAPH_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": long_lived_token,
            },
        )
        response.raise_for_status()
        return response.json()


async def get_instagram_account_id(page_id: str, access_token: str) -> str | None:
    """Get the Instagram Business Account ID linked to a Facebook Page."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_GRAPH_BASE}/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": access_token,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("instagram_business_account", {}).get("id")


async def get_instagram_profile(account_id: str, access_token: str) -> dict:
    """Fetch username and profile picture URL for an Instagram account."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_GRAPH_BASE}/{account_id}",
            params={
                "fields": "username,profile_picture_url",
                "access_token": access_token,
            },
        )
        response.raise_for_status()
        return response.json()


async def get_pages(access_token: str) -> list[dict]:
    """Return the Facebook Pages the user manages."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_GRAPH_BASE}/me/accounts",
            params={"access_token": access_token},
        )
        response.raise_for_status()
        return response.json().get("data", [])


# ── Publishing ────────────────────────────────────────────────────────────────

async def post_single_image(
    image_url: str,
    caption: str,
    hashtags: str,
    account_id: str,
    access_token: str,
) -> dict:
    """
    Publish a single-image post to Instagram.
    Returns {"success": True, "post_id": ..., "instagram_url": ...}
    or {"success": False, "error": ...}.
    """
    full_caption = f"{caption}\n\n{hashtags}"

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Step 1: create media container
        container_resp = await client.post(
            f"{_GRAPH_BASE}/{account_id}/media",
            params={
                "image_url": image_url,
                "caption": full_caption,
                "access_token": access_token,
            },
        )
        if not container_resp.is_success:
            return {"success": False, "error": container_resp.text}

        container_id = container_resp.json().get("id")
        if not container_id:
            return {"success": False, "error": "No container ID returned"}

        # Step 2: publish
        publish_resp = await client.post(
            f"{_GRAPH_BASE}/{account_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": access_token,
            },
        )
        if not publish_resp.is_success:
            return {"success": False, "error": publish_resp.text}

        post_id = publish_resp.json().get("id")
        instagram_url = await _get_permalink(post_id, access_token)

    log.info("instagram_post_published", account_id=account_id, post_id=post_id)
    return {"success": True, "post_id": post_id, "instagram_url": instagram_url}


async def post_carousel(
    image_urls: list[str],
    caption: str,
    hashtags: str,
    account_id: str,
    access_token: str,
) -> dict:
    """
    Publish a carousel post to Instagram.
    Creates one child container per image, then publishes the carousel.
    """
    import asyncio

    full_caption = f"{caption}\n\n{hashtags}"

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Step 1: create child containers for each image
        child_ids = []
        for url in image_urls:
            resp = await client.post(
                f"{_GRAPH_BASE}/{account_id}/media",
                params={
                    "image_url": url,
                    "is_carousel_item": "true",
                    "access_token": access_token,
                },
            )
            if not resp.is_success:
                return {"success": False, "error": f"Child container failed: {resp.text}"}
            child_id = resp.json().get("id")
            if not child_id:
                return {"success": False, "error": "No child container ID returned"}
            child_ids.append(child_id)

        # Step 2: create carousel container
        await asyncio.sleep(_CAROUSEL_CONTAINER_WAIT_SECONDS)

        carousel_resp = await client.post(
            f"{_GRAPH_BASE}/{account_id}/media",
            params={
                "media_type": "CAROUSEL",
                "caption": full_caption,
                "children": ",".join(child_ids),
                "access_token": access_token,
            },
        )
        if not carousel_resp.is_success:
            return {"success": False, "error": carousel_resp.text}

        carousel_id = carousel_resp.json().get("id")
        if not carousel_id:
            return {"success": False, "error": "No carousel container ID returned"}

        # Step 3: publish
        publish_resp = await client.post(
            f"{_GRAPH_BASE}/{account_id}/media_publish",
            params={
                "creation_id": carousel_id,
                "access_token": access_token,
            },
        )
        if not publish_resp.is_success:
            return {"success": False, "error": publish_resp.text}

        post_id = publish_resp.json().get("id")
        instagram_url = await _get_permalink(post_id, access_token)

    log.info("instagram_carousel_published", account_id=account_id, post_id=post_id)
    return {"success": True, "post_id": post_id, "instagram_url": instagram_url}


async def _get_permalink(post_id: str, access_token: str) -> str | None:
    """Fetch the public permalink for a published Instagram post."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_GRAPH_BASE}/{post_id}",
                params={"fields": "permalink", "access_token": access_token},
            )
            resp.raise_for_status()
            return resp.json().get("permalink")
    except Exception as exc:
        log.warning("permalink_fetch_failed", post_id=post_id, error=str(exc))
        return None


# ── Insights ──────────────────────────────────────────────────────────────────

async def fetch_post_insights(
    post_id: str,
    access_token: str,
) -> dict | None:
    """
    Fetch engagement metrics for a published post from the Insights API.
    Returns dict with: impressions, reach, likes, comments, shares, saves.
    Returns None if the request fails.

    Note: Insights data is typically available 24h+ after publishing.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{_GRAPH_BASE}/{post_id}/insights",
                params={
                    "metric": _INSIGHTS_FIELDS,
                    "access_token": access_token,
                },
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])

        metrics: dict[str, int] = {}
        for item in data:
            name = item.get("name")
            values = item.get("values", [{}])
            metrics[name] = int(values[0].get("value", 0)) if values else 0

        # Normalize field names (API returns "saved" not "saves")
        return {
            "impressions": metrics.get("impressions", 0),
            "reach": metrics.get("reach", 0),
            "likes": metrics.get("likes", 0),
            "comments": metrics.get("comments", 0),
            "shares": metrics.get("shares", 0),
            "saves": metrics.get("saved", 0),
        }

    except Exception as exc:
        log.error("insights_fetch_failed", post_id=post_id, error=str(exc))
        return None


def token_expires_at(expires_in_seconds: int) -> datetime:
    """Calculate the expiry datetime from a Meta expires_in value."""
    return datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
