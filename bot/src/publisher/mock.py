"""Mock publisher used in Sprint 1.

Logs a structured event, sleeps 1.5s to mimic real I/O, returns success per
channel. The real publisher will land in Sprint 3/4.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("publisher.mock")

CHANNELS = ("site", "instagram", "facebook")


async def publish(product: dict[str, Any]) -> dict[str, bool]:
    logger.info(
        "mock_publish",
        extra={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "product": product,
            "channels": list(CHANNELS),
        },
    )
    await asyncio.sleep(1.5)
    return {channel: True for channel in CHANNELS}
