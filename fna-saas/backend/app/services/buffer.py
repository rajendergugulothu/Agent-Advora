"""
Buffer API service.

Replaces the Instagram Graph API posting layer.
Uses Buffer's GraphQL API to schedule/publish posts to Instagram.

Each user supplies their own Buffer API token and channel ID,
stored encrypted in the DB (buffer_access_token, buffer_channel_id).

Docs: https://developers.buffer.com
"""

import httpx

from app.core.logging import get_logger

log = get_logger(__name__)

_BUFFER_API_URL = "https://api.buffer.com"
_TIMEOUT = httpx.Timeout(60.0)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _headers(access_token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


async def _run_mutation(query: str, variables: dict, access_token: str) -> dict:
    """Execute a GraphQL mutation against the Buffer API."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(
            _BUFFER_API_URL,
            headers=_headers(access_token),
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        return response.json()


# ── Channel helpers ───────────────────────────────────────────────────────────

async def get_channels(access_token: str) -> list[dict]:
    """
    Return all channels connected to this Buffer account.
    Useful during onboarding to let the user pick their Instagram channel.
    """
    query = """
    query {
        channels {
            id
            name
            service
        }
    }
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(
            _BUFFER_API_URL,
            headers=_headers(access_token),
            json={"query": query},
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("channels", [])


# ── Publishing ────────────────────────────────────────────────────────────────

async def post_single_image(
    image_url: str,
    caption: str,
    hashtags: str,
    channel_id: str,
    access_token: str,
) -> dict:
    """
    Publish a single image post to Instagram via Buffer.

    Buffer requires the image to be hosted at a publicly accessible URL.
    Cloudinary URLs (already used in the image service) work perfectly.

    Returns {"success": True, "post_id": ...}
    or      {"success": False, "error": ...}
    """
    full_caption = f"{caption}\n\n{hashtags}"

    mutation = """
    mutation CreateImagePost($input: CreatePostInput!) {
        createPost(input: $input) {
            ... on PostActionSuccess {
                post {
                    id
                    dueAt
                    text
                }
            }
            ... on MutationError {
                message
            }
        }
    }
    """

    variables = {
        "input": {
            "text": full_caption,
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "mediaUrls": [image_url],
        }
    }

    try:
        data = await _run_mutation(mutation, variables, access_token)
        result = data.get("data", {}).get("createPost", {})

        # Check for GraphQL-level error
        if "message" in result:
            log.error("buffer_post_failed", channel_id=channel_id, error=result["message"])
            return {"success": False, "error": result["message"]}

        post = result.get("post", {})
        post_id = post.get("id")

        log.info("buffer_post_queued", channel_id=channel_id, post_id=post_id)
        return {"success": True, "post_id": post_id}

    except httpx.HTTPStatusError as exc:
        log.error("buffer_http_error", status=exc.response.status_code, body=exc.response.text)
        return {"success": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text}"}

    except Exception as exc:
        log.error("buffer_unexpected_error", error=str(exc))
        return {"success": False, "error": str(exc)}


async def post_carousel(
    image_urls: list[str],
    caption: str,
    hashtags: str,
    channel_id: str,
    access_token: str,
) -> dict:
    """
    Publish a carousel (multi-image) post to Instagram via Buffer.

    Passes all image URLs in a single createPost call.
    Buffer handles carousel creation on the Instagram side.

    Returns {"success": True, "post_id": ...}
    or      {"success": False, "error": ...}
    """
    full_caption = f"{caption}\n\n{hashtags}"

    mutation = """
    mutation CreateCarouselPost($input: CreatePostInput!) {
        createPost(input: $input) {
            ... on PostActionSuccess {
                post {
                    id
                    dueAt
                    text
                }
            }
            ... on MutationError {
                message
            }
        }
    }
    """

    variables = {
        "input": {
            "text": full_caption,
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": "addToQueue",
            "mediaUrls": image_urls,          # multiple URLs = carousel
        }
    }

    try:
        data = await _run_mutation(mutation, variables, access_token)
        result = data.get("data", {}).get("createPost", {})

        if "message" in result:
            log.error("buffer_carousel_failed", channel_id=channel_id, error=result["message"])
            return {"success": False, "error": result["message"]}

        post = result.get("post", {})
        post_id = post.get("id")

        log.info("buffer_carousel_queued", channel_id=channel_id, post_id=post_id, slides=len(image_urls))
        return {"success": True, "post_id": post_id, "image_urls": image_urls}

    except httpx.HTTPStatusError as exc:
        log.error("buffer_http_error", status=exc.response.status_code, body=exc.response.text)
        return {"success": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text}"}

    except Exception as exc:
        log.error("buffer_unexpected_error", error=str(exc))
        return {"success": False, "error": str(exc)}
