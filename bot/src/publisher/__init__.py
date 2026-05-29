"""Publisher package.

Sprint 1-2: mock publisher (logs only).
Sprint 3: site publisher (GitHub + Vercel) active when GITHUB_TOKEN is set.
Sprint 4: Meta publisher (Instagram + Facebook) active when META_ENABLED=1.
"""

import asyncio
import logging
from typing import Any

from ..config import SETTINGS
from .mock import publish as mock_publish
from .site import publish_to_site
from .meta import publish_instagram, publish_facebook

logger = logging.getLogger("publisher")


async def publish(product: dict[str, Any]) -> dict[str, bool]:
    result: dict[str, bool] = {"site": False, "instagram": False, "facebook": False}

    # Site publisher: active when GitHub token is configured.
    if SETTINGS.github_token:
        result["site"] = await publish_to_site(product)
    else:
        mock_result = await mock_publish(product)
        result["site"] = mock_result.get("site", False)
        logger.info("site_publisher_mock", extra={"reason": "GITHUB_TOKEN not set"})

    # Meta publishers: active when META_ENABLED=1 and credentials are set.
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
    else:
        logger.info("meta_publisher_disabled", extra={"reason": "META_ENABLED not set"})

    return result


__all__ = ["publish"]
