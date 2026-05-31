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
import re
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

# Brand voice — kept in a constant so it can be reviewed and updated independently
# from prompt logic without touching the function signatures.
_SYSTEM_PROMPT = """\
Sei la voce digitale di M&M Manifatture di Scarpa Monica, un piccolo laboratorio \
artigianale a Gioi, nel Cilento (SA). Monica crea a mano maglioncini in lana per \
bambini, bambole di pezza con viso dipinto, sciarpe e accessori artigianali. \
Ogni pezzo è unico, prodotto con materiali selezionati, su ordinazione o in serie \
limitatissime.

TONO E VOCE
- Caldo, autentico, artigianale. Mai commerciale, mai urlato.
- Parla come Monica: con cura per i dettagli, con affetto per il lavoro manuale.
- Non usare superlativi vuoti (bellissimo, fantastico, straordinario).
- Non usare call-to-action aggressivi (acquista ora, non perdere l'occasione).
- Italiano corretto, registro medio-alto.
- I capi in lana (maglioncini, sciarpe) sono prodotti stagionali — evoca caldo, autunno/inverno.
- Le bambole e i pezzi regalo sono senza stagione — evoca l'emozione del dono e del pezzo unico.

REGOLE INVARIANTI
- Non inventare materiali, colori o caratteristiche non presenti nella descrizione.
- Se la taglia non è specificata, non menzionarla — non scrivere "taglia unica" o simili.
- Il prezzo va sempre incluso nel testo.
- Non promettere disponibilità a magazzino: i pezzi sono artigianali e limitati.

ANTIPATTERN — non scrivere mai così:
✗ "Questo bellissimo maglioncino è perfetto per..." (apre con aggettivo vuoto + nome prodotto)
✗ "Scopri la nostra nuova collezione..." (linguaggio da brand fast fashion)
✗ "Acquista ora prima che sia tardi!" (urgenza artificiale)
✗ "Un prodotto di altissima qualità..." (claim non verificabile)
✗ "Taglia unica, adatta a tutti." (quando la taglia non è specificata)
✗ "#handmade #love #style" (hashtag anglofoni generici)

OUTPUT
Rispondi esclusivamente con un oggetto JSON valido con chiavi "site", "instagram", \
"facebook". Nessun testo prima o dopo il JSON. Nessun markdown fence.\
"""

_FORMAT_SPEC = """\
SPECIFICHE PER CANALE

SITO (chiave "site")
- 60-120 parole. Prosa descrittiva, due o tre frasi.
- Prima frase: apri con il materiale o la tecnica — MAI con "Questo [prodotto]" o "Scopri".
  Esempio corretto: "Maglioncino in lana merinos avorio, lavorato a punto arroz..."
  Esempio sbagliato: "Questo maglioncino è realizzato in lana merinos..."
- Seconda frase: uso, sensazione o beneficio per chi lo usa o lo regala.
- Terza frase (opzionale): dimensione o taglia se rilevante + prezzo.
- SEO: includi almeno una volta la categoria del prodotto in forma naturale.
- Zero emoji. Zero hashtag. Zero esclamazioni.

INSTAGRAM (chiave "instagram")
- Caption: massimo 150 caratteri, incluse emoji. Una o due frasi evocative.
- Deve reggere da sola, senza hashtag: chi legge capisce il prodotto anche senza i tag.
- Usa 2-3 emoji pertinenti, non decorativi — solo se aggiungono significato.
- A capo doppio, poi 3-5 hashtag italiani mirati separati da spazio.
- Hashtag: specifici di prodotto e territorio (#artigianatolocaliano, #fattaamano, \
#cilento, #maglionchinobambino). Evita hashtag generici o anglofoni (#love, #handmade).
- Formato esatto: "<caption>\\n\\n#tag1 #tag2 #tag3"

FACEBOOK (chiave "facebook")
- 150-250 parole. Tono conversazionale e narrativo — racconta una storia breve.
- Inizia con un'osservazione o una scena, non con il nome del prodotto.
- Puoi citare Monica per nome quando è naturale nella narrazione — non è obbligatorio.
- Chiudi con il prezzo e al massimo 1-2 emoji (non obbligatorie).
- No hashtag.\
"""


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
    for ex in examples[:4]:
        inp = ex.get("input", {})
        out = ex.get("output", {})
        few_shot += (
            "\n---\n"
            f"ESEMPIO\n"
            f"Descrizione: {inp.get('description', '')}\n"
            f"Prezzo: €{inp.get('price', 0):.2f}\n"
            f"Taglia: {inp.get('size') or 'non specificata'}\n"
            f"Categoria: {inp.get('category', '')}\n"
            f"Output JSON:\n{json.dumps(out, ensure_ascii=False, indent=2)}\n"
        )

    # If description is minimal (short or vague), instruct the model to lean on
    # category and price rather than pad with invented details.
    description_note = ""
    if len(description.strip()) < 40:
        description_note = (
            "\nNOTA: la descrizione è sintetica. "
            "Non inventare materiali o colori. "
            "Compensa con il calore del brand: il gesto artigianale, il tempo di lavorazione, "
            "l'emozione del regalo — elementi validi anche senza dettagli tecnici.\n"
        )

    size_str = size if size else "non specificata"
    price_str = f"€{price:.2f}".replace(".", ",")

    return (
        f"Esempi del tono e formato atteso:{few_shot}"
        f"---\n"
        f"{_FORMAT_SPEC}\n"
        f"---\n"
        f"PRODOTTO DA DESCRIVERE\n"
        f"Descrizione: {description}\n"
        f"Prezzo: {price_str}\n"
        f"Taglia: {size_str}\n"
        f"Categoria: {category}\n"
        f"{description_note}"
        f"\nOutput JSON:"
    )


def _strip_fences(raw: str) -> str:
    """Remove markdown code fences that some models add despite instructions."""
    raw = raw.strip()
    # Handle ```json ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


async def generate_captions(
    description: str,
    price: float,
    size: str | None,
    category: str,
) -> CaptionResult:
    if not SETTINGS.anthropic_api_key:
        raise CaptionError("ANTHROPIC_API_KEY not configured")
    if not description or not description.strip():
        raise CaptionError("description is required for caption generation")

    examples = _load_examples(SETTINGS.caption_examples_path)
    prompt = _build_prompt(description, price, size, category, examples)

    client = anthropic.Anthropic(api_key=SETTINGS.anthropic_api_key)
    try:
        response = await asyncio.to_thread(
            client.messages.create,
            model=_MODEL,
            max_tokens=800,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as exc:
        logger.error("caption_api_error", extra={"error": str(exc)})
        raise CaptionError(str(exc)) from exc

    raw = response.content[0].text.strip() if response.content else ""
    logger.info(
        "caption_generated",
        extra={
            "model": _MODEL,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    )

    try:
        parsed = json.loads(_strip_fences(raw))
        # Validate all three keys are non-empty strings
        site = str(parsed.get("site", "")).strip()
        instagram = str(parsed.get("instagram", "")).strip()
        facebook = str(parsed.get("facebook", "")).strip()
        if not (site and instagram and facebook):
            raise ValueError(f"missing keys in response: {list(parsed.keys())}")
        return CaptionResult(site=site, instagram=instagram, facebook=facebook)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.error("caption_parse_failed", extra={"raw": raw[:300], "error": str(exc)})
        raise CaptionError(f"JSON parse failed: {exc}") from exc
