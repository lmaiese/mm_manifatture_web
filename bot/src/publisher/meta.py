"""Meta Graph API publisher — Instagram and Facebook.

Instagram flow (single photo):
    POST /{ig_user_id}/media  → container_id
    POST /{ig_user_id}/media_publish → published media id

Instagram flow (carousel, N > 1):
    POST /{ig_user_id}/media for each photo → [child_id, ...]
    Poll each child until STATUS == FINISHED
    POST /{ig_user_id}/media  carousel container → carousel_id
    POST /{ig_user_id}/media_publish → published media id

Facebook flow (single photo):
    POST /{page_id}/photos → photo post id

Facebook flow (multiple photos):
    POST /{page_id}/photos?published=false for each photo → [photo_id, ...]
    POST /{page_id}/feed  with attached_media=[...] → post id

Requires: INSTAGRAM_USER_ID, INSTAGRAM_ACCESS_TOKEN,
          FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN in .env
          META_ENABLED=1 to activate (otherwise falls back to mock)
"""

import asyncio
import logging
from typing import Any

import aiohttp

from ..config import SETTINGS

logger = logging.getLogger("publisher.meta")

_GRAPH_BASE = "https://graph.facebook.com/v19.0"
_CONTAINER_POLL_INTERVAL = 3   # seconds between status polls
_CONTAINER_POLL_MAX = 10       # max attempts before timeout


class MetaPublishError(Exception):
    pass


# ---------- Instagram ----------


async def _ig_create_container(
    session: aiohttp.ClientSession,
    ig_user_id: str,
    token: str,
    image_url: str,
    caption: str,
    is_carousel_item: bool = False,
) -> str:
    params: dict[str, Any] = {
        "image_url": image_url,
        "access_token": token,
    }
    if is_carousel_item:
        params["is_carousel_item"] = "true"
    else:
        params["caption"] = caption

    async with session.post(
        f"{_GRAPH_BASE}/{ig_user_id}/media",
        params=params,
        timeout=aiohttp.ClientTimeout(total=20),
    ) as resp:
        data = await resp.json()
        if "error" in data:
            raise MetaPublishError(f"IG container error: {data['error']}")
        return data["id"]


async def _ig_wait_container_ready(
    session: aiohttp.ClientSession,
    container_id: str,
    token: str,
) -> None:
    for attempt in range(_CONTAINER_POLL_MAX):
        try:
            async with session.get(
                f"{_GRAPH_BASE}/{container_id}",
                params={"fields": "status_code", "access_token": token},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                status = data.get("status_code", "")
                if status == "FINISHED":
                    return
                if status == "ERROR":
                    raise MetaPublishError(f"IG container {container_id} failed: {data}")
        except MetaPublishError:
            raise
        except Exception as exc:
            logger.warning(
                "ig_container_poll_error",
                extra={"container_id": container_id, "attempt": attempt, "error": str(exc)},
            )
        await asyncio.sleep(_CONTAINER_POLL_INTERVAL)
    raise MetaPublishError(f"IG container {container_id} timed out after {_CONTAINER_POLL_MAX} attempts")


async def _ig_publish_container(
    session: aiohttp.ClientSession,
    ig_user_id: str,
    token: str,
    container_id: str,
) -> str:
    async with session.post(
        f"{_GRAPH_BASE}/{ig_user_id}/media_publish",
        params={"creation_id": container_id, "access_token": token},
        timeout=aiohttp.ClientTimeout(total=20),
    ) as resp:
        data = await resp.json()
        if "error" in data:
            raise MetaPublishError(f"IG publish error: {data['error']}")
        return data["id"]


async def publish_instagram(product: dict[str, Any]) -> bool:
    ig_user_id = SETTINGS.instagram_user_id
    token = SETTINGS.instagram_access_token
    if not ig_user_id or not token:
        logger.error("ig_publish_skipped", extra={"reason": "INSTAGRAM credentials missing"})
        return False

    photo_urls: list[str] = product.get("photos") or []
    if not photo_urls:
        logger.error("ig_publish_skipped", extra={"reason": "no photo URLs"})
        return False

    caption = product.get("description_instagram") or product.get("description_site") or ""

    try:
        async with aiohttp.ClientSession() as session:
            if len(photo_urls) == 1:
                container_id = await _ig_create_container(session, ig_user_id, token, photo_urls[0], caption)
                await _ig_wait_container_ready(session, container_id, token)
                media_id = await _ig_publish_container(session, ig_user_id, token, container_id)
            else:
                # Carousel
                child_ids: list[str] = []
                for url in photo_urls:
                    cid = await _ig_create_container(session, ig_user_id, token, url, "", is_carousel_item=True)
                    await _ig_wait_container_ready(session, cid, token)
                    child_ids.append(cid)

                async with session.post(
                    f"{_GRAPH_BASE}/{ig_user_id}/media",
                    params={
                        "media_type": "CAROUSEL",
                        "children": ",".join(child_ids),
                        "caption": caption,
                        "access_token": token,
                    },
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    data = await resp.json()
                    if "error" in data:
                        raise MetaPublishError(f"IG carousel container error: {data['error']}")
                    carousel_id = data["id"]

                await _ig_wait_container_ready(session, carousel_id, token)
                media_id = await _ig_publish_container(session, ig_user_id, token, carousel_id)

        logger.info("ig_published", extra={"media_id": media_id, "category": product.get("category")})
        return True

    except MetaPublishError as exc:
        logger.error("ig_publish_failed", extra={"error": str(exc)})
        return False
    except Exception as exc:
        logger.error("ig_publish_error", extra={"error": str(exc)})
        return False


# ---------- Facebook ----------


async def _fb_upload_photo_unpublished(
    session: aiohttp.ClientSession,
    page_id: str,
    token: str,
    image_url: str,
) -> str:
    async with session.post(
        f"{_GRAPH_BASE}/{page_id}/photos",
        params={
            "url": image_url,
            "published": "false",
            "access_token": token,
        },
        timeout=aiohttp.ClientTimeout(total=20),
    ) as resp:
        data = await resp.json()
        if "error" in data:
            raise MetaPublishError(f"FB photo upload error: {data['error']}")
        return data["id"]


async def publish_facebook(product: dict[str, Any]) -> bool:
    page_id = SETTINGS.facebook_page_id
    token = SETTINGS.facebook_access_token
    if not page_id or not token:
        logger.error("fb_publish_skipped", extra={"reason": "FACEBOOK credentials missing"})
        return False

    photo_urls: list[str] = product.get("photos") or []
    if not photo_urls:
        logger.error("fb_publish_skipped", extra={"reason": "no photo URLs"})
        return False

    caption = product.get("description_facebook") or product.get("description_site") or ""

    try:
        async with aiohttp.ClientSession() as session:
            if len(photo_urls) == 1:
                async with session.post(
                    f"{_GRAPH_BASE}/{page_id}/photos",
                    params={
                        "url": photo_urls[0],
                        "caption": caption,
                        "access_token": token,
                    },
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    data = await resp.json()
                    if "error" in data:
                        raise MetaPublishError(f"FB photo post error: {data['error']}")
                    post_id = data.get("post_id") or data.get("id")
            else:
                # Multi-photo post via feed + attached_media
                photo_ids: list[str] = []
                for url in photo_urls:
                    pid = await _fb_upload_photo_unpublished(session, page_id, token, url)
                    photo_ids.append(pid)

                attached = [{"media_fbid": pid} for pid in photo_ids]
                async with session.post(
                    f"{_GRAPH_BASE}/{page_id}/feed",
                    json={
                        "message": caption,
                        "attached_media": attached,
                        "access_token": token,
                    },
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    data = await resp.json()
                    if "error" in data:
                        raise MetaPublishError(f"FB feed post error: {data['error']}")
                    post_id = data.get("id")

        logger.info("fb_published", extra={"post_id": post_id, "category": product.get("category")})
        return True

    except MetaPublishError as exc:
        logger.error("fb_publish_failed", extra={"error": str(exc)})
        return False
    except Exception as exc:
        logger.error("fb_publish_error", extra={"error": str(exc)})
        return False
