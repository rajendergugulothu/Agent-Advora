"""
WhatsApp webhook endpoints.

GET  /webhook  — Meta verification challenge
POST /webhook  — Incoming messages (button replies from users)

Multi-tenant routing: the draft_id embedded in the button reply ID
is used to look up which user owns the draft, then the appropriate
scheduler action is triggered.
"""

import json
import uuid

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import verify_meta_signature
from app.db.database import AsyncSessionFactory
from app.db.models import Draft, UserProfile, WebhookEvent

router = APIRouter()
settings = get_settings()
log = get_logger(__name__)


@router.get("")
async def verify_webhook(request: Request):
    """Meta calls this once to verify your webhook URL."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_webhook_verify_token:
        log.info("webhook_verified")
        return Response(content=challenge, media_type="text/plain")

    log.warning("webhook_verification_failed", token_received=token)
    return Response(content="Forbidden", status_code=403)


@router.post("")
async def receive_whatsapp(request: Request):
    """
    Handle incoming WhatsApp webhook events.
    Validates the Meta signature, logs the event, and routes button replies
    to the correct user's approval handler.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    signature_valid = verify_meta_signature(raw_body, signature)

    if not signature_valid:
        log.warning("webhook_invalid_signature")

        # Log the rejected event for audit purposes
        async with AsyncSessionFactory() as db:
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception:
                payload = {}
            db.add(WebhookEvent(
                raw_payload=payload,
                signature_valid=False,
                processed=False,
                error="Invalid signature",
            ))
        return Response(content="Invalid signature", status_code=401)

    try:
        body = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        return Response(content="Invalid JSON", status_code=400)

    log.info("webhook_received", preview=json.dumps(body)[:300])

    # Log the valid event
    async with AsyncSessionFactory() as db:
        event = WebhookEvent(raw_payload=body, signature_valid=True, processed=False)
        db.add(event)
        await db.flush()
        event_id = event.id

    await _process_webhook(body, event_id)
    return {"status": "ok"}


async def _process_webhook(body: dict, event_id: uuid.UUID) -> None:
    """Extract button replies and route to the correct handler."""
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages", [])

        for message in messages:
            if message.get("type") == "interactive":
                reply = message["interactive"].get("button_reply", {})
                reply_id = reply.get("id", "")
                if reply_id:
                    await _route_button_reply(reply_id)

        async with AsyncSessionFactory() as db:
            from sqlalchemy import update
            await db.execute(
                update(WebhookEvent)
                .where(WebhookEvent.id == event_id)
                .values(processed=True)
            )

    except (KeyError, IndexError, TypeError) as exc:
        log.info("webhook_non_message_event", error=str(exc))
        async with AsyncSessionFactory() as db:
            from sqlalchemy import update
            await db.execute(
                update(WebhookEvent)
                .where(WebhookEvent.id == event_id)
                .values(processed=True, error=f"Parse skip: {exc}")
            )


async def _route_button_reply(reply_id: str) -> None:
    """
    Parse APPROVE_<draft_id> or REGENERATE_<draft_id> and call the scheduler.

    The draft_id is the source of truth for which user owns the action.
    """
    action, _, draft_id_str = reply_id.partition("_")
    if not draft_id_str:
        log.warning("webhook_malformed_reply_id", reply_id=reply_id)
        return

    try:
        draft_uuid = uuid.UUID(draft_id_str)
    except ValueError:
        log.warning("webhook_invalid_draft_id", draft_id=draft_id_str)
        return

    async with AsyncSessionFactory() as db:
        draft = await db.get(Draft, draft_uuid)
        if not draft:
            log.warning("webhook_draft_not_found", draft_id=draft_id_str)
            return
        user_id = str(draft.user_id)

    from app.services.scheduler import get_scheduler

    if action == "APPROVE":
        log.info("webhook_approve", draft_id=draft_id_str, user_id=user_id)
        await get_scheduler().handle_approve(draft_id_str, user_id)
    elif action == "REGENERATE":
        log.info("webhook_regenerate", draft_id=draft_id_str, user_id=user_id)
        await get_scheduler().handle_regenerate(draft_id_str, user_id)
    else:
        log.warning("webhook_unknown_action", action=action, reply_id=reply_id)
