"""Cloudinary photo uploader.

Uploads local photo files to Cloudinary and returns public URLs.
Progress callback allows the caller to update a Telegram message per-photo
so the user sees "Carico foto 1/3..." instead of silence.

Image processing pipeline (applied per photo, before upload):
  1. Smart crop — Claude Haiku vision detects the subject bounding box,
     then crops the largest possible 4:5 rectangle that fully contains it.
     Falls back silently to step 2 on any API or parse error.
  2. Enforce ratio — geometric center-crop to 4:5.
     Required by Instagram Graph API (accepts 4:5 to 1.91:1 only).
     No-op if the image already satisfies the ratio within tolerance.

Activation:
  - Smart crop:   active when ANTHROPIC_API_KEY is set.
  - Enforce ratio: always active.
"""

import asyncio
import base64
import json
import logging
import re
from collections.abc import Awaitable, Callable
from pathlib import Path

import anthropic
import cloudinary
import cloudinary.uploader
from PIL import Image

from .config import SETTINGS

logger = logging.getLogger("cloudinary_uploader")

# Instagram Graph API: aspect ratio must be between 4:5 (0.800) and 1.91:1.
# We target 4:5 (portrait) — maximises vertical space in the feed.
_IG_RATIO_W = 4
_IG_RATIO_H = 5
_IG_RATIO_TOLERANCE = 0.02  # skip enforce_ratio if already within ±2% of target

# Margin added around the Vision bbox before expanding to the target ratio.
# Expressed as a fraction of the shorter image dimension (e.g. 0.04 = 4%).
_BBOX_MARGIN_FRAC = 0.04

# Prompt sent to Claude Haiku vision. English is used for reliability.
_VISION_PROMPT = (
    "Look at this image and locate the main subject — the artisanal garment or "
    "object being sold (e.g. a knitted sweater, cardigan, hat, scarf, or handmade item).\n\n"
    "Return a JSON object with the bounding box that COMPLETELY contains the entire subject. "
    "Include the whole object — nothing should be clipped. "
    "If the subject fills or nearly fills the entire image, return the full frame.\n\n"
    "JSON format (integer percentages 0–100 of image width/height):\n"
    '{"x": <left edge %>, "y": <top edge %>, "w": <width %>, "h": <height %>}\n\n'
    "Constraints:\n"
    "- x + w ≤ 100\n"
    "- y + h ≤ 100\n"
    "- All values are integers\n"
    "Return only the JSON object, nothing else."
)


class UploadError(Exception):
    pass


def _configure() -> None:
    cloudinary.config(
        cloud_name=SETTINGS.cloudinary_cloud_name,
        api_key=SETTINGS.cloudinary_api_key,
        api_secret=SETTINGS.cloudinary_api_secret,
        secure=True,
    )


# ---------- image processing (sync — runs inside asyncio.to_thread) ----------


def _enforce_ratio(img: Image.Image) -> Image.Image:
    """Geometric center-crop to _IG_RATIO_W : _IG_RATIO_H.

    No-op if the image is already within _IG_RATIO_TOLERANCE of the target.
    """
    W, H = img.size
    target = _IG_RATIO_W / _IG_RATIO_H
    current = W / H

    if abs(current - target) / target <= _IG_RATIO_TOLERANCE:
        return img

    if current > target:
        # Image too wide — crop width, keep full height
        new_w = int(H * target)
        x0 = (W - new_w) // 2
        result = img.crop((x0, 0, x0 + new_w, H))
        logger.info(
            "enforce_ratio_applied",
            extra={
                "direction": "crop_width",
                "orig_size": [W, H],
                "new_size": list(result.size),
            },
        )
        return result
    else:
        # Image too tall — crop height, keep full width
        new_h = int(W / target)
        y0 = (H - new_h) // 2
        result = img.crop((0, y0, W, y0 + new_h))
        logger.info(
            "enforce_ratio_applied",
            extra={
                "direction": "crop_height",
                "orig_size": [W, H],
                "new_size": list(result.size),
            },
        )
        return result


def _apply_smart_crop(img: Image.Image, bbox_pct: dict[str, int]) -> Image.Image:
    """Crop the image to a 4:5 rectangle that fully contains the subject bbox.

    Strategy:
      1. Convert bbox from % to pixels and add a small margin.
      2. Expand the bbox to 4:5 by growing the shorter dimension only (never shrink).
      3. Center the resulting rectangle on the bbox center.
      4. Clamp to image boundaries, shifting if we hit an edge.
    """
    W, H = img.size
    target = _IG_RATIO_W / _IG_RATIO_H
    margin = int(_BBOX_MARGIN_FRAC * min(W, H))

    # Convert to pixels + margin
    bx = max(0, int(bbox_pct["x"] / 100 * W) - margin)
    by = max(0, int(bbox_pct["y"] / 100 * H) - margin)
    bw = min(W - bx, int(bbox_pct["w"] / 100 * W) + 2 * margin)
    bh = min(H - by, int(bbox_pct["h"] / 100 * H) + 2 * margin)

    if bw <= 0 or bh <= 0:
        logger.warning("smart_crop_invalid_bbox", extra={"bbox_pct": bbox_pct, "bw": bw, "bh": bh})
        return img

    # Center of the (margined) bbox
    cx = bx + bw / 2
    cy = by + bh / 2

    # Expand to target ratio (only expand, never shrink)
    if (bw / bh) < target:
        # bbox narrower than 4:5 — expand width
        cw = bh * target
        ch = float(bh)
    else:
        # bbox wider than 4:5 — expand height
        cw = float(bw)
        ch = bw / target

    # Center the crop rectangle
    x0 = int(cx - cw / 2)
    y0 = int(cy - ch / 2)
    x1 = x0 + int(cw)
    y1 = y0 + int(ch)

    # Clamp: if we exceed boundaries, shift (don't resize — that would cut the subject)
    if x1 > W:
        x0 -= x1 - W
        x1 = W
    if y1 > H:
        y0 -= y1 - H
        y1 = H
    x0 = max(0, x0)
    y0 = max(0, y0)

    cropped = img.crop((x0, y0, x1, y1))
    logger.info(
        "smart_crop_applied",
        extra={
            "bbox_pct": bbox_pct,
            "bbox_px": {"x": bx, "y": by, "w": bw, "h": bh},
            "crop_px": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
            "orig_size": [W, H],
            "crop_size": list(cropped.size),
        },
    )
    return cropped


def _call_vision_sync(path: Path, api_key: str) -> dict[str, int] | None:
    """Call Claude Haiku vision to get subject bounding box.

    Returns a validated dict {"x","y","w","h"} in 0-100 integer percentages,
    or None on any failure (API error, parse error, invalid values).

    Runs synchronously — must be called inside asyncio.to_thread.
    """
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": _VISION_PROMPT},
                    ],
                }
            ],
        )
        raw = response.content[0].text.strip() if response.content else ""

        # Strip markdown fences (some models add them despite instructions)
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

        # Validate structure and ranges
        bbox: dict[str, int] = {}
        for key in ("x", "y", "w", "h"):
            if key not in parsed:
                raise ValueError(f"missing key '{key}' in Vision response: {raw!r}")
            val = int(parsed[key])
            if not 0 <= val <= 100:
                raise ValueError(f"bbox['{key}']={val} out of range 0-100")
            bbox[key] = val

        if bbox["x"] + bbox["w"] > 100:
            raise ValueError(f"bbox x+w={bbox['x']+bbox['w']} > 100")
        if bbox["y"] + bbox["h"] > 100:
            raise ValueError(f"bbox y+h={bbox['y']+bbox['h']} > 100")

        logger.info("vision_bbox_ok", extra={"path": str(path), "bbox": bbox})
        return bbox

    except Exception as exc:
        logger.warning("vision_bbox_failed", extra={"path": str(path), "error": str(exc)})
        return None


def _process_image_sync(path: Path, api_key: str) -> None:
    """Apply smart crop → enforce ratio, overwrite path in-place.

    Failure contract: on any error, the original file is left untouched.
    Never raises — callers must not depend on this succeeding.
    The upload will always proceed (with or without processing).
    """
    try:
        img = Image.open(path).convert("RGB")
        orig_size = img.size
        smart_crop_used = False

        # Step 1: smart crop via Vision (skipped if no API key)
        if api_key:
            bbox = _call_vision_sync(path, api_key)
            if bbox is not None:
                img = _apply_smart_crop(img, bbox)
                smart_crop_used = True
            else:
                logger.info(
                    "smart_crop_skipped",
                    extra={"path": str(path), "reason": "Vision returned no bbox"},
                )
        else:
            logger.info(
                "smart_crop_skipped",
                extra={"path": str(path), "reason": "ANTHROPIC_API_KEY not set"},
            )

        # Step 2: enforce 4:5 ratio (always)
        img = _enforce_ratio(img)

        # Overwrite the local file
        img.save(path, format="JPEG", quality=92, optimize=True)

        logger.info(
            "image_processed",
            extra={
                "path": str(path),
                "orig_size": list(orig_size),
                "final_size": list(img.size),
                "smart_crop": smart_crop_used,
            },
        )

    except Exception as exc:
        logger.error(
            "image_process_failed",
            extra={"path": str(path), "error": str(exc)},
        )
        # Leave original file untouched — upload continues with unprocessed image


# ---------- public API ----------


async def upload_photos(
    paths: list[str],
    on_progress: Callable[[int, int], Awaitable[None]] | None = None,
    folder: str = "mm_manifatture",
) -> list[str]:
    """Process (crop) then upload photos to Cloudinary.

    Returns list of secure public URLs, one per input path.
    Raises UploadError if a photo is missing or the Cloudinary call fails.

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

        # Image processing: smart crop + ratio enforce (runs in thread pool,
        # never raises — fallback to original on any failure)
        await asyncio.to_thread(_process_image_sync, path, SETTINGS.anthropic_api_key)

        # Upload processed file to Cloudinary
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
