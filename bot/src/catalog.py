"""Read/write helpers for web/catalog.json categories.

catalog.json may not have a 'categories' field yet — we create it on demand.
"""

import json
import logging
from pathlib import Path
from typing import Any

from .config import SETTINGS

logger = logging.getLogger("catalog")


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"products": [], "categories": []}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("catalog_read_failed", extra={"path": str(path), "error": str(exc)})
        return {"products": [], "categories": []}
    if not isinstance(data, dict):
        return {"products": [], "categories": []}
    data.setdefault("products", [])
    data.setdefault("categories", [])
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)
    except OSError as exc:
        logger.error("catalog_write_failed", extra={"path": str(path), "error": str(exc)})
        tmp.unlink(missing_ok=True)
        raise


def list_categories() -> list[str]:
    data = _read(SETTINGS.catalog_path)
    cats = data.get("categories") or []
    return [str(c) for c in cats if c]


def add_category(name: str) -> list[str]:
    name = name.strip().title()
    if not name:
        return list_categories()
    path = SETTINGS.catalog_path
    data = _read(path)
    cats = [str(c) for c in (data.get("categories") or []) if c]
    if name.lower() not in [c.lower() for c in cats]:
        cats.append(name)
        data["categories"] = cats
        _write(path, data)
        logger.info("category_written", extra={"cat_name": name, "total": len(cats)})
    return cats
