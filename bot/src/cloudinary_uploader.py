"""Cloudinary photo uploader.

Uploads local photo files to Cloudinary and returns public URLs.
Progress callback allows the caller to update a Telegram message per-photo
so the user sees "Carico foto 1/3..." instead of silence.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

import cloudinary
import cloudinary.uploader

from .config import SETTINGS

logger = logging.getLogger("cloudinary_uploader")


class UploadError(Exception):
    pass


def _configure() -> None:
    cloudinary.config(
        cloud_name=SETTINGS.cloudinary_cloud_name,
        api_key=SETTINGS.cloudinary_api_key,
        api_secret=SETTINGS.cloudinary_api_secret,
        secure=True,
    )


async def upload_photos(
    paths: list[str],
    on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    folder: str = "mm_manifatture",
) -> list[str]:
    """Upload photos and return list of secure public URLs.

    on_progress(done, total) is awaited after each successful upload so the
    caller can update a Telegram message with progress feedback.
    """
    if not (SETTINGS.cloudinary_cloud_name and SETTINGS.cloudinary_api_key and SETTINGS.cloudinary_api_secret):
        raise UploadError("Cloudinary credentials not configured")

    _configure()
    urls: list[str] = []
    total = len(paths)

    for i, path_str in enumerate(paths, start=1):
        path = Path(path_str)
        if not path.exists():
            logger.error("upload_file_missing", extra={"path": path_str, "index": i})
            raise UploadError(f"Photo not found: {path_str}")
        try:
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                str(path),
                folder=folder,
                resource_type="image",
                use_filename=False,
                unique_filename=True,
            )
        except Exception as exc:
            logger.error("upload_failed", extra={"path": path_str, "error": str(exc)})
            raise UploadError(f"Upload failed for {path.name}: {exc}") from exc

        url = result.get("secure_url", "")
        urls.append(url)
        logger.info("photo_uploaded", extra={"path": path_str, "url": url, "index": i, "total": total})

        if on_progress is not None:
            await on_progress(i, total)

    return urls
