"""Read/write helpers for web/catalog.json categories.

catalog.json may not have a 'categories' field yet — we create it on demand.
"""

import json
from pathlib import Path
from typing import Any

from .config import SETTINGS


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"products": [], "categories": []}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"products": [], "categories": []}
    if not isinstance(data, dict):
        return {"products": [], "categories": []}
    data.setdefault("products", [])
    data.setdefault("categories", [])
    return data


def list_categories() -> list[str]:
    data = _read(SETTINGS.catalog_path)
    cats = data.get("categories") or []
    return [str(c) for c in cats if c]


def add_category(name: str) -> list[str]:
    name = name.strip()
    if not name:
        return list_categories()
    path = SETTINGS.catalog_path
    data = _read(path)
    cats = [str(c) for c in (data.get("categories") or []) if c]
    if name not in cats:
        cats.append(name)
        data["categories"] = cats
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return cats
