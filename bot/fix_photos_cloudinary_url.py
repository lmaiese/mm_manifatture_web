"""Fix catalog.json: restore photos from photos_original (undo bad migration).

The migrate_images.py pipeline used Haiku Vision bbox detection to smart-crop
photos before re-uploading to Cloudinary. Results were bad (inaccurate bbox,
double JPEG compression). This script reverts photos to the original URLs stored
in photos_original, which were set by the migration as the backup.

Run from the bot/ directory:
    poetry run python fix_photos_cloudinary_url.py [--dry-run]

After running: commit catalog.json, push, Vercel redeploys automatically.
Orphaned Cloudinary assets (the bad crops) can be cleaned up from the dashboard.
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

CATALOG_PATH = Path(__file__).parent.parent / "web" / "catalog.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    restored = 0
    unchanged = 0
    no_original = 0

    for product in catalog["products"]:
        pid = product["id"][:8]
        originals = product.get("photos_original")

        if not originals:
            print(f"[{pid}] SKIP — no photos_original")
            no_original += 1
            continue

        if product.get("photos") == originals:
            print(f"[{pid}] already matches photos_original — skip")
            unchanged += 1
            continue

        print(f"[{pid}] restore {len(originals)} photo(s)")
        for o in originals:
            print(f"  <- {o[-60:]}")
        product["photos"] = list(originals)
        restored += 1

    print(f"\nRestored: {restored}  Unchanged: {unchanged}  No-original: {no_original}")

    if args.dry_run:
        print("[dry-run] catalog.json NOT modified")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = Path(__file__).parent / f"catalog_backup_{ts}.json"
    shutil.copy2(CATALOG_PATH, backup)
    print(f"Backup: {backup}")

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print("catalog.json updated.")


if __name__ == "__main__":
    main()
