"""
WhatsApp messaging service.

Sends draft approval requests and plain text status updates
to each user's registered WhatsApp number via the Meta Cloud API.
"""

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

_GRAPH_BASE = "https://graph.facebook.com/v21.0"
_TIMEOUT = httpx.Timeout(30.0)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }


async def send_draft_for_approval(
    post: dict,
    draft_id: str,
    recipient_number: str,
) -> str | None:
    """
    Send a draft to the user's WhatsApp for approval.
    Returns the Meta message ID on success, None on failure.

    Sends an interactive message with two buttons:
    - Approve & Post
    - Regenerate
    """
    post_type_label = "Carousel" if post.get("post_type") == "carousel" else "Single Image"
    slide_count = len(post.get("carousel_slides", []))

    body_text = (
        f"*New Draft Ready* ({post_type_label}"
        + (f" — {slide_count} slides" if slide_count else "")
        + f")\n\n"
        f"*Theme:* {post['theme']}\n\n"
        f"*Hook:* {post['hook']}\n\n"
        f"*Caption:*\n{post['caption']}\n\n"
        f"*Hashtags:* {post['hashtags'][:100]}...\n\n"
        f"*Image concept:*\n{post.get('image_concept', '')[:200]}"
    )

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text[:1024]},  # WhatsApp body limit
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"APPROVE_{draft_id}",
                            "title": "Approve & Post",
                        },
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"REGENERATE_{draft_id}",
                            "title": "Regenerate",
                        },
                    },
                ]
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_GRAPH_BASE}/{settings.whatsapp_phone_number_id}/messages",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            log.info(
                "whatsapp_draft_sent",
                draft_id=draft_id,
                recipient=recipient_number,
                message_id=message_id,
            )
            return message_id
    except httpx.HTTPStatusError as exc:
        log.error(
            "whatsapp_send_failed",
            draft_id=draft_id,
            status=exc.response.status_code,
            body=exc.response.text[:500],
        )
        return None
    except Exception as exc:
        log.error("whatsapp_send_error", draft_id=draft_id, error=str(exc))
        return None


async def send_text_message(text: str, recipient_number: str) -> bool:
    """Send a plain text message to the user's WhatsApp number."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
        "type": "text",
        "text": {"body": text[:4096]},
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_GRAPH_BASE}/{settings.whatsapp_phone_number_id}/messages",
                headers=_headers(),
                json=payload,
            )
            response.raise_for_status()
            log.info("whatsapp_text_sent", recipient=recipient_number)
            return True
    except Exception as exc:
        log.error("whatsapp_text_failed", recipient=recipient_number, error=str(exc))
        return False
