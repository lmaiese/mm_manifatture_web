"""bulk_publish.py — Retroactive social publishing for existing catalog products.

Reads catalog.json, filters publishable products, enqueues them in the bot DB
at one-per-day intervals. The bot's queue_worker picks them up automatically.

Zero external dependencies — runs without activating the bot venv.

Usage:
    python3 bulk_publish.py \
        --catalog ../web/catalog.json \
        --db bot.sqlite \
        --chat-id <TELEGRAM_ADMIN_CHAT_ID> \
        [--slot 10] \
        [--start 2026-06-15] \
        [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bulk-enqueue catalog products for social publishing.")
    p.add_argument("--catalog", required=True, help="Path to web/catalog.json")
    p.add_argument("--db",      required=True, help="Path to bot.sqlite")
    p.add_argument("--chat-id", required=True, type=int, dest="chat_id",
                   help="Telegram admin chat_id (receives publication confirmations)")
    p.add_argument("--slot",    type=int, default=10,
                   help="Hour (UTC, 0-23) for daily publication. Default: 10")
    p.add_argument("--start",   default=None,
                   help="First publication date YYYY-MM-DD. Default: tomorrow")
    p.add_argument("--dry-run", action="store_true",
                   help="Print plan without writing to DB")
    return p.parse_args()


# ---------- validation ----------

def validate_args(args: argparse.Namespace) -> None:
    errors = []

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        errors.append(f"catalog not found: {catalog_path.resolve()}")

    db_path = Path(args.db)
    if not db_path.exists():
        errors.append(f"DB not found: {db_path.resolve()}")

    if not (0 <= args.slot <= 23):
        errors.append(f"--slot must be 0-23, got {args.slot}")

    if args.start is not None:
        try:
            datetime.strptime(args.start, "%Y-%m-%d")
        except ValueError:
            errors.append(f"--start must be YYYY-MM-DD, got {args.start!r}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


# ---------- catalog loading ----------

def load_products(catalog_path: Path) -> list[dict]:
    with catalog_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        # Support both {"products": [...]} and flat {id: {...}} formats
        if "products" in raw:
            return raw["products"]
        return list(raw.values())

    print("ERROR: unrecognised catalog format", file=sys.stderr)
    sys.exit(1)


# ---------- filtering ----------

def _first_cloudinary_photo(product: dict) -> str | None:
    for url in product.get("photos") or []:
        if "res.cloudinary.com" in str(url):
            return url
    return None


def _is_publishable(product: dict) -> tuple[bool, str]:
    pid = product.get("id", "")

    if str(pid).startswith("demo-"):
        return False, "demo product"

    if product.get("published") is not True:
        return False, "not published on site"

    if not _first_cloudinary_photo(product):
        return False, "no Cloudinary photo"

    if not (product.get("description_instagram") or "").strip():
        return False, "missing description_instagram"

    return True, "ok"


# ---------- deduplication ----------

def _already_handled_photos(db_path: Path) -> set[str]:
    """Return set of photos[0] URLs already in queue or published_products."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    handled: set[str] = set()

    try:
        for table, col in [("publication_queue", "product_data"),
                            ("published_products", "product_data")]:
            try:
                rows = conn.execute(f"SELECT {col} FROM {table}").fetchall()
            except sqlite3.OperationalError:
                continue
            for row in rows:
                try:
                    data = json.loads(row[0] or "{}")
                    photos = data.get("photos") or []
                    if photos:
                        handled.add(str(photos[0]))
                except (json.JSONDecodeError, TypeError):
                    continue
    finally:
        conn.close()

    return handled


# ---------- scheduling ----------

def _build_publish_at(date: datetime, slot: int) -> str:
    dt = date.replace(hour=slot, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    return dt.isoformat()


def _start_date(args: argparse.Namespace) -> datetime:
    if args.start:
        return datetime.strptime(args.start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


# ---------- enqueue ----------

def _enqueue(db_path: Path, chat_id: int, product: dict, publish_at: str) -> None:
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        conn.execute(
            """
            INSERT INTO publication_queue (chat_id, product_data, enqueued_at, publish_at, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (
                chat_id,
                json.dumps(product, ensure_ascii=False, default=str),
                datetime.now(timezone.utc).isoformat(),
                publish_at,
            ),
        )
    finally:
        conn.close()


# ---------- main ----------

def main() -> None:
    args = parse_args()
    validate_args(args)

    catalog_path = Path(args.catalog)
    db_path = Path(args.db)

    all_products = load_products(catalog_path)
    already_handled = _already_handled_photos(db_path)

    publishable: list[dict] = []
    skipped_demo = skipped_not_published = skipped_no_photo = skipped_no_desc = skipped_duplicate = 0

    for product in all_products:
        if not isinstance(product, dict):
            continue
        ok, reason = _is_publishable(product)
        if not ok:
            if reason == "demo product":
                skipped_demo += 1
            elif reason == "not published on site":
                skipped_not_published += 1
            elif reason == "no Cloudinary photo":
                skipped_no_photo += 1
            else:
                skipped_no_desc += 1
            continue

        first_photo = _first_cloudinary_photo(product)
        if first_photo in already_handled:
            skipped_duplicate += 1
            continue

        # Force destination to social-only
        product = {**product, "destination": "social"}
        publishable.append(product)

    print(f"\nProdotti nel catalog:            {len(all_products)}")
    print(f"  Skip — demo:                   {skipped_demo}")
    print(f"  Skip — non pubblicati su sito: {skipped_not_published}")
    print(f"  Skip — nessuna foto Cloud.:    {skipped_no_photo}")
    print(f"  Skip — desc IG mancante:       {skipped_no_desc}")
    print(f"  Skip — già in coda/pubblicati: {skipped_duplicate}")
    print(f"Da accodare:                     {len(publishable)}")

    if not publishable:
        print("\nNessun prodotto da accodare.")
        return

    start = _start_date(args)
    plan: list[tuple[str, str]] = []

    for i, product in enumerate(publishable):
        date = start + timedelta(days=i)
        publish_at = _build_publish_at(date, args.slot)
        title = (product.get("title") or product.get("category") or product.get("id") or "?")
        plan.append((publish_at, title))

    print(f"\nRange: {plan[0][0][:10]} → {plan[-1][0][:10]}  (slot {args.slot:02d}:00 UTC)")
    print()

    label = "[DRY RUN]" if args.dry_run else "[ACCODATO]"
    for (publish_at, title), product in zip(plan, publishable):
        print(f"  {label}  {publish_at[:16]} UTC — {title}")
        if not args.dry_run:
            _enqueue(db_path, args.chat_id, product, publish_at)

    if args.dry_run:
        print("\nDry run completato — nessuna scrittura su DB.")
    else:
        print(f"\n{len(publishable)} prodotti accodati. Il bot li publicherà automaticamente.")


if __name__ == "__main__":
    main()
