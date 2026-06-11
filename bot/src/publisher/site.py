"""Publish a product to the Vercel static site via GitHub + deploy hook.

Flow:
1. Read catalog.json from GitHub repo (main branch)
2. Append new product entry
3. Commit updated catalog.json back to main
4. POST to Vercel deploy hook — Vercel rebuilds the site in ~30s

Requires: GITHUB_TOKEN, GITHUB_REPO, VERCEL_DEPLOY_HOOK in .env
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import aiohttp
from github import Github, GithubException

from ..config import SETTINGS

logger = logging.getLogger("publisher.site")

CATALOG_PATH = "web/catalog.json"


def _make_product_entry(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title": product.get("title") or "",
        "category": product.get("category") or "",
        "price": float(product.get("price") or 0.0),
        "size": product.get("size"),
        "description_site": product.get("description_site") or product.get("description") or "",
        "description_instagram": product.get("description_instagram") or "",
        "description_facebook": product.get("description_facebook") or "",
        "photos": product.get("photos") or [],
        "published": True,
        "available": True,
        "scheduled_for": product.get("scheduled_for"),
        "target": product.get("target"),
    }


async def publish_to_site(product: dict[str, Any]) -> bool:
    """Update catalog.json on GitHub and trigger Vercel rebuild.

    Returns True on full success, False on partial failure (deploy hook failed
    but catalog was updated).
    """
    github_token = SETTINGS.github_token
    github_repo = SETTINGS.github_repo
    vercel_hook = SETTINGS.vercel_deploy_hook

    if not github_token or not github_repo:
        logger.error("site_publish_skipped", extra={"reason": "GITHUB_TOKEN or GITHUB_REPO missing"})
        return False

    entry = _make_product_entry(product)

    try:
        catalog_updated = await asyncio.to_thread(_update_catalog_on_github, github_token, github_repo, entry)
    except Exception as exc:
        logger.error("catalog_update_failed", extra={"error": str(exc)})
        return False

    if not catalog_updated:
        return False

    # Trigger Vercel deploy hook
    if vercel_hook:
        hook_ok = await _trigger_deploy_hook(vercel_hook)
        if not hook_ok:
            logger.warning("deploy_hook_failed", extra={"product_id": entry["id"]})
            return False
    else:
        logger.warning("deploy_hook_skipped", extra={"reason": "VERCEL_DEPLOY_HOOK not configured"})

    logger.info("site_published", extra={"product_id": entry["id"], "category": entry["category"]})
    return True


def _update_catalog_on_github(token: str, repo_name: str, entry: dict[str, Any]) -> bool:
    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
        file = repo.get_contents(CATALOG_PATH, ref="main")
        raw = file.decoded_content.decode("utf-8")  # type: ignore[union-attr]
        catalog = json.loads(raw)
    except GithubException as exc:
        logger.error("github_read_failed", extra={"error": str(exc)})
        return False
    except json.JSONDecodeError as exc:
        logger.error("catalog_json_invalid", extra={"error": str(exc)})
        return False

    catalog.setdefault("products", [])
    catalog["products"].append(entry)

    updated_raw = json.dumps(catalog, ensure_ascii=False, indent=2)
    commit_msg = f"feat: add product {entry['id'][:8]} — {entry['category']}"

    try:
        repo.update_file(
            path=CATALOG_PATH,
            message=commit_msg,
            content=updated_raw,
            sha=file.sha,  # type: ignore[union-attr]
            branch="main",
        )
        logger.info("catalog_committed", extra={"product_id": entry["id"]})
        return True
    except GithubException as exc:
        logger.error("github_write_failed", extra={"error": str(exc)})
        return False


async def _trigger_deploy_hook(hook_url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(hook_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                ok = resp.status < 300
                logger.info("deploy_hook_triggered", extra={"status": resp.status, "ok": ok})
                return ok
    except Exception as exc:
        logger.error("deploy_hook_error", extra={"error": str(exc)})
        return False


# ---------- read / hide ----------


async def read_published_from_github() -> list[dict[str, Any]]:
    """Return published products from GitHub catalog, newest first. [] on any error."""
    token = SETTINGS.github_token
    repo_name = SETTINGS.github_repo
    if not token or not repo_name:
        return []
    return await asyncio.to_thread(_read_published_sync, token, repo_name)


def _read_published_sync(token: str, repo_name: str) -> list[dict[str, Any]]:
    from github import Github, GithubException

    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
        file = repo.get_contents(CATALOG_PATH, ref="main")
        catalog = json.loads(file.decoded_content.decode("utf-8"))  # type: ignore[union-attr]
        products = [p for p in (catalog.get("products") or []) if p.get("published", True)]
        products.sort(key=lambda p: p.get("created_at") or "", reverse=True)
        return products
    except GithubException as exc:
        logger.warning("read_published_failed", extra={"error": str(exc)})
        return []
    except Exception as exc:
        logger.warning("read_published_error", extra={"error": str(exc)})
        return []


async def read_available_from_github() -> list[dict[str, Any]]:
    """Return published + available (not sold) products, newest first."""
    token = SETTINGS.github_token
    repo_name = SETTINGS.github_repo
    if not token or not repo_name:
        return []
    return await asyncio.to_thread(_read_available_sync, token, repo_name)


def _read_available_sync(token: str, repo_name: str) -> list[dict[str, Any]]:
    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
        file = repo.get_contents(CATALOG_PATH, ref="main")
        catalog = json.loads(file.decoded_content.decode("utf-8"))  # type: ignore[union-attr]
        products = [
            p for p in (catalog.get("products") or [])
            if p.get("published", True) and p.get("available", True)
        ]
        products.sort(key=lambda p: p.get("created_at") or "", reverse=True)
        return products
    except Exception as exc:
        logger.warning("read_available_failed", extra={"error": str(exc)})
        return []


async def read_sold_from_github() -> list[dict[str, Any]]:
    """Return published but sold (available=False) products, newest first."""
    token = SETTINGS.github_token
    repo_name = SETTINGS.github_repo
    if not token or not repo_name:
        return []
    return await asyncio.to_thread(_read_sold_sync, token, repo_name)


def _read_sold_sync(token: str, repo_name: str) -> list[dict[str, Any]]:
    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
        file = repo.get_contents(CATALOG_PATH, ref="main")
        catalog = json.loads(file.decoded_content.decode("utf-8"))  # type: ignore[union-attr]
        products = [
            p for p in (catalog.get("products") or [])
            if p.get("published", True) and not p.get("available", True)
        ]
        products.sort(key=lambda p: p.get("created_at") or "", reverse=True)
        return products
    except Exception as exc:
        logger.warning("read_sold_failed", extra={"error": str(exc)})
        return []


async def update_availability(product_id: str, available: bool) -> bool:
    """Set available=True/False for product_id, commit to GitHub, trigger deploy."""
    token = SETTINGS.github_token
    repo_name = SETTINGS.github_repo
    if not token or not repo_name:
        logger.error("update_availability_skipped", extra={"reason": "missing config"})
        return False
    ok = await asyncio.to_thread(_update_availability_sync, token, repo_name, product_id, available)
    if ok and SETTINGS.vercel_deploy_hook:
        await _trigger_deploy_hook(SETTINGS.vercel_deploy_hook)
    return ok


def _update_availability_sync(token: str, repo_name: str, product_id: str, available: bool) -> bool:
    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
        file = repo.get_contents(CATALOG_PATH, ref="main")
        raw = file.decoded_content.decode("utf-8")  # type: ignore[union-attr]
        catalog = json.loads(raw)
        products = catalog.get("products") or []
        target = next((p for p in products if p.get("id") == product_id), None)
        if target is None:
            logger.warning("update_availability_not_found", extra={"product_id": product_id})
            return False
        target["available"] = available
        action = "sold" if not available else "available"
        repo.update_file(
            path=CATALOG_PATH,
            message=f"chore: mark product {product_id[:8]} as {action}",
            content=json.dumps(catalog, ensure_ascii=False, indent=2),
            sha=file.sha,  # type: ignore[union-attr]
            branch="main",
        )
        logger.info("availability_updated", extra={"product_id": product_id, "available": available})
        return True
    except GithubException as exc:
        logger.error("update_availability_github_failed", extra={"error": str(exc)})
        return False
    except Exception as exc:
        logger.error("update_availability_failed", extra={"error": str(exc)})
        return False


async def hide_product(product_id: str) -> bool:
    """Set published=False for product_id, commit to GitHub, and trigger deploy hook."""
    token = SETTINGS.github_token
    repo_name = SETTINGS.github_repo
    if not token or not repo_name:
        logger.error("hide_product_skipped", extra={"reason": "GITHUB_TOKEN or GITHUB_REPO missing"})
        return False

    ok = await asyncio.to_thread(_hide_product_sync, token, repo_name, product_id)
    if ok and SETTINGS.vercel_deploy_hook:
        await _trigger_deploy_hook(SETTINGS.vercel_deploy_hook)
    return ok


def _hide_product_sync(token: str, repo_name: str, product_id: str) -> bool:
    from github import Github, GithubException

    gh = Github(token)
    try:
        repo = gh.get_repo(repo_name)
        file = repo.get_contents(CATALOG_PATH, ref="main")
        raw = file.decoded_content.decode("utf-8")  # type: ignore[union-attr]
        catalog = json.loads(raw)
        products = catalog.get("products") or []
        target = next((p for p in products if p.get("id") == product_id), None)
        if target is None:
            logger.warning("hide_product_not_found", extra={"product_id": product_id})
            return False
        target["published"] = False
        repo.update_file(
            path=CATALOG_PATH,
            message=f"chore: hide product {product_id[:8]}",
            content=json.dumps(catalog, ensure_ascii=False, indent=2),
            sha=file.sha,  # type: ignore[union-attr]
            branch="main",
        )
        logger.info("product_hidden", extra={"product_id": product_id})
        return True
    except GithubException as exc:
        logger.error("hide_product_github_failed", extra={"error": str(exc)})
        return False
    except Exception as exc:
        logger.error("hide_product_failed", extra={"error": str(exc)})
        return False
