"""Publisher package.

Sprint 1-2: mock publisher (logs only).
Sprint 3: site publisher (GitHub + Vercel) active when GITHUB_TOKEN is set.
Sprint 4: Meta publisher (Instagram + Facebook) active when META_ENABLED=1.
"""

import asyncio
import logging
import uuid
from typing import Any

from ..config import SETTINGS
from .mock import publish as mock_publish
from .site import publish_to_site, update_social_published
from .meta import publish_instagram, publish_facebook

logger = logging.getLogger("publisher")


async def publish(product: dict[str, Any]) -> dict[str, bool | None]:
    # Ensure a stable id exists for catalog tracking across all publishers
    if not product.get("id"):
        product = {**product, "id": str(uuid.uuid4())}

    destination = product.get("destination", "all")
    publish_site = destination in ("site", "all")
    publish_social = destination in ("social", "all")

    result: dict[str, bool | None] = {"site": None, "instagram": None, "facebook": None}

    # Site publisher
    if publish_site:
        if SETTINGS.github_token:
            result["site"] = await publish_to_site(product)
        else:
            mock_result = await mock_publish(product)
            result["site"] = mock_result.get("site", False)
            logger.info("site_publisher_mock", extra={"reason": "GITHUB_TOKEN not set"})

    # Meta publishers
    if publish_social:
        if SETTINGS.meta_enabled:
            ig_result, fb_result = await asyncio.gather(
                publish_instagram(product),
                publish_facebook(product),
                return_exceptions=True,
            )
            result["instagram"] = ig_result is True
            result["facebook"] = fb_result is True
            if isinstance(ig_result, Exception):
                logger.error("ig_publish_exception", extra={"error": str(ig_result)})
            if isinstance(fb_result, Exception):
                logger.error("fb_publish_exception", extra={"error": str(fb_result)})

            if result["instagram"] or result["facebook"]:
                product_id = product.get("id")
                if product_id and SETTINGS.github_token:
                    await update_social_published(product_id)
                elif not product_id:
                    logger.warning("social_published_skip", extra={"reason": "product has no id"})
        else:
            logger.debug("meta_publisher_disabled", extra={"reason": "META_ENABLED not set"})

    logger.info("publish_dispatched", extra={"destination": destination})
    return result


__all__ = ["publish"]
