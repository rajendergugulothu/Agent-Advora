"""
Security utilities:
- Fernet symmetric encryption for stored tokens (Instagram, WhatsApp)
- HMAC signature verification for Meta webhooks
"""

import base64
import hashlib
import hmac

from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()

# ── Token encryption ──────────────────────────────────────────────────────────
# Fernet requires a URL-safe base64-encoded 32-byte key.
# We derive it from the 64-char hex ENCRYPTION_KEY in .env.

def _build_fernet() -> Fernet:
    raw = bytes.fromhex(settings.encryption_key)   # 32 bytes from 64-char hex
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)

_fernet = _build_fernet()


def encrypt_token(plaintext: str) -> str:
    """Encrypt a credential string before storing in the database."""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a stored credential string."""
    return _fernet.decrypt(ciphertext.encode()).decode()


# ── Meta webhook signature ────────────────────────────────────────────────────

def verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Validate the X-Hub-Signature-256 header sent by Meta on every webhook call.
    Must receive the raw, unmodified request body bytes.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        settings.whatsapp_app_secret.encode(),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    provided = signature_header.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)
