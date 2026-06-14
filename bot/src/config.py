"""Centralized configuration loaded from .env.

Single import point so handlers don't read os.environ scattered around.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BOT_ROOT.parent


def _parse_chat_ids(raw: str) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            out.append(int(chunk))
        except ValueError:
            continue
    return out


def _parse_slots(raw: str) -> list[int]:
    out: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        try:
            h = int(chunk)
            if 0 <= h <= 23:
                out.append(h)
        except ValueError:
            continue
    return out or [10, 13, 18, 21]


def _int_or_none(raw: str | None) -> int | None:
    if not raw:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


@dataclass(frozen=True)
class Settings:
    telegram_token: str = field(repr=False)
    allowed_chat_ids: list[int] = field(default_factory=list)
    admin_chat_id: int | None = None
    photos_dir: Path = BOT_ROOT / "photos"
    db_path: Path = BOT_ROOT / "bot.sqlite"
    catalog_path: Path = PROJECT_ROOT / "web" / "catalog.json"
    inactivity_minutes: int = 30
    # Sprint 2
    anthropic_api_key: str = field(default="", repr=False)
    cloudinary_cloud_name: str = field(default="", repr=False)
    cloudinary_api_key: str = field(default="", repr=False)
    cloudinary_api_secret: str = field(default="", repr=False)
    caption_examples_path: Path = BOT_ROOT / "data" / "caption_examples.json"
    # Sprint 3
    github_token: str = field(default="", repr=False)
    github_repo: str = "lmaiese/mm_manifatture_web"
    vercel_deploy_hook: str = field(default="", repr=False)
    # Sprint 4 — Meta Graph API
    instagram_user_id: str = field(default="", repr=False)
    instagram_access_token: str = field(default="", repr=False)
    facebook_page_id: str = field(default="", repr=False)
    facebook_access_token: str = field(default="", repr=False)
    meta_enabled: bool = False
    meta_app_id: str = field(default="", repr=False)
    meta_app_secret: str = field(default="", repr=False)
    # Sprint 5 — Scheduler
    publication_slots: list[int] = field(default_factory=lambda: [10, 13, 18, 21])
    daily_report_enabled: bool = False


def load_settings() -> Settings:
    token = os.environ.get("TELEGRAM_TOKEN", "")
    # Accept both TELEGRAM_ALLOWED_CHAT_ID (legacy singular) and plural form
    raw_allowed = os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS") or os.environ.get(
        "TELEGRAM_ALLOWED_CHAT_ID", ""
    )
    allowed = _parse_chat_ids(raw_allowed)
    admin = _int_or_none(os.environ.get("TELEGRAM_ADMIN_CHAT_ID"))

    photos_dir = Path(os.environ.get("PHOTOS_DIR") or (BOT_ROOT / "photos"))
    db_path = Path(os.environ.get("DB_PATH") or (BOT_ROOT / "bot.sqlite"))
    catalog_path = Path(
        os.environ.get("CATALOG_PATH") or (PROJECT_ROOT / "web" / "catalog.json")
    )
    try:
        inactivity = int(os.environ.get("INACTIVITY_MINUTES") or 30)
    except ValueError:
        inactivity = 30

    photos_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        telegram_token=token,
        allowed_chat_ids=allowed,
        admin_chat_id=admin,
        photos_dir=photos_dir,
        db_path=db_path,
        catalog_path=catalog_path,
        inactivity_minutes=inactivity,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        cloudinary_cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
        cloudinary_api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
        cloudinary_api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        github_repo=os.environ.get("GITHUB_REPO", "lmaiese/mm_manifatture_web"),
        vercel_deploy_hook=os.environ.get("VERCEL_DEPLOY_HOOK", ""),
        instagram_user_id=os.environ.get("INSTAGRAM_USER_ID", ""),
        instagram_access_token=os.environ.get("INSTAGRAM_ACCESS_TOKEN", ""),
        facebook_page_id=os.environ.get("FACEBOOK_PAGE_ID", ""),
        facebook_access_token=os.environ.get("FACEBOOK_ACCESS_TOKEN", ""),
        meta_enabled=os.environ.get("META_ENABLED", "0") == "1",
        meta_app_id=os.environ.get("META_APP_ID", ""),
        meta_app_secret=os.environ.get("META_APP_SECRET", ""),
        publication_slots=_parse_slots(os.environ.get("PUBLICATION_SLOTS", "10,13,18,21")),
        daily_report_enabled=os.environ.get("DAILY_REPORT_ENABLED", "0") == "1",
    )


SETTINGS = load_settings()
