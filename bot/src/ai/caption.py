"""AI caption generator — Claude Haiku.

Generates three channel-specific captions (site, instagram, facebook) from
product data. Reads few-shot examples from caption_examples.json so the tone
can be calibrated without touching code.

Failure contract: raises CaptionError on hard failure. Caller catches and
shows explicit fallback confirmation to the user — no silent degradation.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic

from ..config import SETTINGS

logger = logging.getLogger("ai.caption")

_MODEL = "claude-haiku-4-5-20251001"


class CaptionError(Exception):
    pass


@dataclass
class CaptionResult:
    site: str
    instagram: str
    facebook: str


def _load_examples(path: Path) -> list[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("examples", [])
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("caption_examples_load_failed", extra={"path": str(path), "error": str(exc)})
        return []


def _build_prompt(
    description: str,
    price: float,
    size: str | None,
    category: str,
    examples: list[dict[str, Any]],
) -> str:
    few_shot = ""
    for ex in examples[:3]:
        inp = ex.get("input", {})
        out = ex.get("output", {})
        few_shot += (
            f"\n---\nEsempio:\n"
            f"Descrizione: {inp.get('description', '')}\n"
            f"Prezzo: €{inp.get('price', 0):.2f}\n"
            f"Taglia: {inp.get('size') or 'non specificata'}\n"
            f"Categoria: {inp.get('category', '')}\n"
            f"Output JSON:\n{json.dumps(out, ensure_ascii=False)}\n"
        )

    size_str = size if size else "non specificata"
    return f"""Sei l'assistente di un negozio di artigianato italiano.
Dato un prodotto, genera tre testi promozionali: uno per il sito web (breve, descrittivo, SEO-friendly), uno per Instagram (con emoji e 3-5 hashtag), uno per Facebook (più lungo, conversazionale).

Rispondi SOLO con un oggetto JSON con chiavi "site", "instagram", "facebook".
Scrivi in italiano. Tono caldo, artigianale, autentico — non commerciale.
{few_shot}
---
Prodotto da descrivere:
Descrizione: {description}
Prezzo: €{price:.2f}
Taglia: {size_str}
Categoria: {category}

Output JSON:"""


async def generate_captions(
    description: str,
    price: float,
    size: str | None,
    category: str,
) -> CaptionResult:
    if not SETTINGS.anthropic_api_key:
        raise CaptionError("ANTHROPIC_API_KEY not configured")

    examples = _load_examples(SETTINGS.caption_examples_path)
    prompt = _build_prompt(description, price, size, category, examples)

    client = anthropic.Anthropic(api_key=SETTINGS.anthropic_api_key)
    try:
        response = await asyncio.to_thread(
            client.messages.create,
            model=_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        logger.error("caption_api_error", extra={"error": str(exc)})
        raise CaptionError(str(exc)) from exc

    raw = response.content[0].text.strip() if response.content else ""
    logger.info(
        "caption_generated",
        extra={"model": _MODEL, "input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens},
    )

    try:
        # Strip markdown code fences if the model wraps JSON in ```
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        return CaptionResult(
            site=str(parsed.get("site", description)),
            instagram=str(parsed.get("instagram", description)),
            facebook=str(parsed.get("facebook", description)),
        )
    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("caption_parse_failed", extra={"raw": raw[:200], "error": str(exc)})
        raise CaptionError(f"JSON parse failed: {exc}") from exc
