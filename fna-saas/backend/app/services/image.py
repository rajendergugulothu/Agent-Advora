"""
Image generation service.

Generates DALL-E images from post concepts and uploads them
to Cloudinary for permanent public hosting.
"""

import asyncio
import uuid
from functools import partial

import cloudinary
import cloudinary.uploader
import httpx
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)
settings = get_settings()

_openai = AsyncOpenAI(api_key=settings.openai_api_key)

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
    secure=True,
)

_DALLE_SIZE = "1024x1024"
_DALLE_QUALITY = "standard"


def _build_image_prompt(image_concept: str, theme: str) -> str:
    return (
        f"Create a clean, professional Instagram post image for a financial advisor. "
        f"Theme: {theme}. "
        f"Design: {image_concept}. "
        f"Style: modern, trustworthy, clear typography, bold colors on white or light background. "
        f"No people's faces. No logos. Text on image must be exactly as specified. "
        f"High contrast, easy to read on mobile."
    )


def _build_slide_prompt(slide: dict, theme: str) -> str:
    headline = slide.get("headline", "")
    body = slide.get("body", "")
    cta = slide.get("cta", "")
    text_parts = f'Headline: "{headline}"'
    if body:
        text_parts += f'. Body text: "{body}"'
    if cta:
        text_parts += f'. CTA: "{cta}"'
    return (
        f"Create a clean, professional Instagram carousel slide for a financial advisor. "
        f"Theme: {theme}. "
        f"{text_parts}. "
        f"Style: modern, bold typography, consistent color scheme, easy to read on mobile. "
        f"No people's faces. No logos. Clean minimal layout."
    )


async def _generate_dalle_image(prompt: str) -> bytes:
    """Call DALL-E and return the image bytes."""
    response = await _openai.images.generate(
        model=settings.openai_image_model,
        prompt=prompt,
        size=_DALLE_SIZE,
        quality=_DALLE_QUALITY,
        n=1,
        response_format="url",
    )
    image_url = response.data[0].url
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(image_url)
        r.raise_for_status()
        return r.content


def _upload_to_cloudinary(image_bytes: bytes, public_id: str) -> str:
    """Upload bytes to Cloudinary and return the secure URL. Runs in executor."""
    result = cloudinary.uploader.upload(
        image_bytes,
        public_id=public_id,
        folder="fna_posts",
        upload_preset=settings.cloudinary_upload_preset,
        overwrite=True,
        resource_type="image",
    )
    return result["secure_url"]


async def _generate_and_upload(prompt: str, public_id: str) -> str:
    """Generate one image and upload it. Returns the Cloudinary URL."""
    image_bytes = await _generate_dalle_image(prompt)
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(
        None, partial(_upload_to_cloudinary, image_bytes, public_id)
    )
    return url


async def generate_single_image(
    image_concept: str,
    theme: str,
    draft_id: str,
) -> str | None:
    """Generate and host a single post image. Returns URL or None on failure."""
    prompt = _build_image_prompt(image_concept, theme)
    public_id = f"draft_{draft_id}_single"
    try:
        url = await _generate_and_upload(prompt, public_id)
        log.info("image_generated", draft_id=draft_id, url=url)
        return url
    except Exception as exc:
        log.error("image_generation_failed", draft_id=draft_id, error=str(exc))
        return None


async def generate_carousel_images(
    slides: list[dict],
    theme: str,
    draft_id: str,
) -> list[str]:
    """
    Generate one image per carousel slide concurrently.
    Returns a list of URLs (empty list if any slide fails).
    """
    tasks = [
        _generate_and_upload(
            _build_slide_prompt(slide, theme),
            f"draft_{draft_id}_slide_{slide.get('slide_number', i + 1)}",
        )
        for i, slide in enumerate(slides)
    ]
    try:
        urls = await asyncio.gather(*tasks)
        log.info("carousel_images_generated", draft_id=draft_id, count=len(urls))
        return list(urls)
    except Exception as exc:
        log.error("carousel_generation_failed", draft_id=draft_id, error=str(exc))
        return []
