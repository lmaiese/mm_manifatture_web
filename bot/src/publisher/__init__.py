"""Publisher package.

Sprint 1-2: mock publisher (logs only).
Sprint 3: site publisher (GitHub + Vercel) active when GITHUB_TOKEN is set.
Sprint 4: Meta publisher (Instagram + Facebook) will be added here.
"""

import logging
from typing import Any

from ..config import SETTINGS
from .mock import publish as mock_publish
from .site import publish_to_site

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

    # Sprint 4: Instagram + Facebook publishers will replace these.
    result["instagram"] = False
    result["facebook"] = False

    return result


__all__ = ["publish"]
