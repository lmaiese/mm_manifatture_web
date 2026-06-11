"""Migration script: re-process all Cloudinary photos through the 4:5 smart-crop pipeline.

Run from the bot/ directory:
    poetry run python migrate_images.py [--dry-run]

What it does:
  1. Reads web/catalog.json
  2. Creates a timestamped backup of catalog.json (always, even in dry-run)
  3. For each product with Cloudinary URLs (skips demo /products/... paths):
     - Downloads the original image (10s timeout)
     - Applies smart crop (Haiku Vision bbox) + enforce 4:5 ratio
     - Uploads the processed image to Cloudinary (new public_id, new URL)
     - Saves the original URL in photos_original (backup, not rendered)
     - Updates photos with the new cropped URL
  4. Writes updated catalog.json

NOTE: --dry-run still calls the Haiku Vision API (~1 token per photo) to validate
      the full pipeline. Skip --dry-run entirely if you want to avoid API costs.

Idempotent: re-running skips photos already listed in migrate_images_log.json as
"done". Delete the log to re-process everything.
"""

import argparse
import json
import shutil
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# Must come after load_dotenv so SETTINGS picks up the env vars.
import cloudinary
import cloudinary.uploader
from PIL import Image

from src.cloudinary_uploader import (
    _apply_smart_crop,
    _call_vision_sync,
    _enforce_ratio,
)
from src.config import SETTINGS

CATALOG_PATH = Path(__file__).parent.parent / "web" / "catalog.json"
LOG_PATH = Path(__file__).parent / "migrate_images_log.json"
CLOUDINARY_FOLDER = "mm_manifatture"
DOWNLOAD_TIMEOUT_S = 10


def _is_cloudinary_url(url: str) -> bool:
    return url.startswith("https://res.cloudinary.com/")


def _load_log() -> dict:
    if LOG_PATH.exists():
        with open(LOG_PATH) as f:
            return json.load(f)
    return {}


def _save_log(log: dict) -> None:
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def _backup_catalog() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Store in bot/ (not web/) to avoid git tracking or Vercel serving the backup.
    backup_path = Path(__file__).parent / f"catalog_backup_{ts}.json"
    shutil.copy2(CATALOG_PATH, backup_path)
    return backup_path


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as resp:
        dest.write_bytes(resp.read())


def _configure_cloudinary() -> None:
    cloudinary.config(
        cloud_name=SETTINGS.cloudinary_cloud_name,
        api_key=SETTINGS.cloudinary_api_key,
        api_secret=SETTINGS.cloudinary_api_secret,
        secure=True,
    )


def _process_and_upload(url: str, dry_run: bool) -> str:
    """Download → process → upload. Returns new Cloudinary URL (or original on dry-run)."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    out_path = tmp_path.parent / (tmp_path.stem + "_out.jpg")

    try:
        print(f"    download ...", end=" ", flush=True)
        _download(url, tmp_path)
        print("ok", flush=True)

        img = Image.open(tmp_path).convert("RGB")
        orig_size = img.size

        # Step 1: smart crop via Haiku Vision
        smart_crop_used = False
        if SETTINGS.anthropic_api_key:
            bbox = _call_vision_sync(tmp_path, SETTINGS.anthropic_api_key)
            if bbox is not None:
                img = _apply_smart_crop(img, bbox)
                smart_crop_used = True
                print(f"    haiku bbox {bbox} → smart crop applied")
            else:
                print("    haiku returned no bbox → center crop only")
        else:
            print("    ANTHROPIC_API_KEY not set → center crop only")

        # Step 2: enforce 4:5 (safety net for rounding edge cases)
        img = _enforce_ratio(img)
        final_size = img.size
        print(f"    {orig_size} → {final_size}  smart_crop={smart_crop_used}")

        if dry_run:
            print("    [dry-run] skipping upload")
            return url  # original URL unchanged

        # Save processed image to a separate output file (never overwrites original tmp)
        img.save(out_path, format="JPEG", quality=92, optimize=True)

        print(f"    upload ...", end=" ", flush=True)
        result = cloudinary.uploader.upload(
            str(out_path),
            folder=CLOUDINARY_FOLDER,
            resource_type="image",
            use_filename=False,
            unique_filename=True,
        )
        new_url = result["secure_url"]
        print(f"ok → {new_url}")
        return new_url

    finally:
        tmp_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process images (including Haiku Vision calls) but skip Cloudinary upload",
    )
    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print(f"ERROR: catalog not found at {CATALOG_PATH}", file=sys.stderr)
        sys.exit(1)

    if not dry_run_safe(args.dry_run):
        sys.exit(1)

    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    backup_path = _backup_catalog()
    print(f"Backup: {backup_path}")

    if not args.dry_run:
        _configure_cloudinary()

    log = _load_log()
    products = catalog["products"]

    cloudinary_photos = [
        (p["id"], url)
        for p in products
        for url in p.get("photos", [])
        if _is_cloudinary_url(url)
    ]
    print(f"Catalog: {len(products)} products, {len(cloudinary_photos)} Cloudinary photos")
    if args.dry_run:
        print("DRY RUN — uploads skipped (Haiku Vision calls will still happen)\n")
    print()

    done = 0
    skipped = 0
    errors = 0

    for product in products:
        pid = product["id"]

        # photos_original = the first-ever original URLs, set once and never overwritten.
        # Always iterate over originals so re-runs don't re-crop already-cropped images.
        if "photos_original" not in product:
            product["photos_original"] = list(product.get("photos", []))
        originals = product["photos_original"]

        new_photos = []
        for orig_url in originals:
            if not _is_cloudinary_url(orig_url):
                new_photos.append(orig_url)
                continue

            if orig_url in log and log[orig_url]["status"] == "done":
                new_url = log[orig_url]["new_url"]
                print(f"[{pid[:8]}] SKIP already migrated → {new_url[-40:]}")
                new_photos.append(new_url)
                skipped += 1
                continue

            print(f"[{pid[:8]}] {orig_url[-60:]}")
            try:
                new_url = _process_and_upload(orig_url, args.dry_run)
                if not args.dry_run:
                    log[orig_url] = {"status": "done", "new_url": new_url, "orig_url": orig_url}
                    _save_log(log)  # persist after each photo so partial runs are recoverable
                new_photos.append(new_url)
                done += 1
            except Exception as exc:
                print(f"    ERROR: {exc}")
                if not args.dry_run:
                    log[orig_url] = {"status": "error", "error": str(exc), "orig_url": orig_url}
                    _save_log(log)
                new_photos.append(orig_url)  # keep original on failure
                errors += 1

        product["photos"] = new_photos

    if not args.dry_run:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        print(f"\ncatalog.json updated (backup at {backup_path})")
    else:
        print(f"\n[dry-run] catalog.json NOT modified (backup still created at {backup_path})")

    print(f"Done: {done} processed, {skipped} skipped, {errors} errors")
    if errors:
        print(f"WARNING: {errors} photos failed — kept original URLs, check log for details")
    print(f"Log: {LOG_PATH}")


def dry_run_safe(dry_run: bool) -> bool:
    """Validate credentials before starting."""
    missing = []
    if not SETTINGS.cloudinary_cloud_name:
        missing.append("CLOUDINARY_CLOUD_NAME")
    if not SETTINGS.cloudinary_api_key:
        missing.append("CLOUDINARY_API_KEY")
    if not SETTINGS.cloudinary_api_secret:
        missing.append("CLOUDINARY_API_SECRET")
    if not dry_run and missing:
        print(f"ERROR: missing credentials: {', '.join(missing)}", file=sys.stderr)
        return False
    if not SETTINGS.anthropic_api_key:
        print("WARNING: ANTHROPIC_API_KEY not set — smart crop disabled, center crop only")
    return True


if __name__ == "__main__":
    main()
