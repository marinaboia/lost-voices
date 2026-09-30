#!/usr/bin/env python3
"""
semantic_filter.py

LLM-based semantic pre-filtering: uses Claude to assess whether unassigned eBL
fragments could plausibly belong to the Standard Babylonian Epic of Gilgamesh.

Runs the Batches API for cost-effective bulk classification (50% discount +
prompt caching on the shared Gilgamesh context). Falls back to sequential
streaming calls for small test runs.

Usage:
    python semantic_filter.py
    python semantic_filter.py --sample 20
    python semantic_filter.py --sample 20 --sequential
    python semantic_filter.py --resume BATCH_ID

API key is read from .env in this directory (copy .env.example → .env and fill it in).
You can also set ANTHROPIC_API_KEY in the environment directly.

Outputs:
    results/semantic_filter_results.json   full annotated candidate list
    results/semantic_filter_top.csv        high-confidence subset
"""

import argparse
import csv
import json
import os
import re
import time
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from typing import Optional
from utils import load_env

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"
BATCH_STATE_FILE = RESULTS_DIR / "batch_state.json"

# Confidence threshold for "worth examining"
DEFAULT_THRESHOLD = 0.35

# How many lines of a tablet's ATF to include as examples
TABLET_EXAMPLE_LINES = 8


# ---------------------------------------------------------------------------
# Candidate loading + pre-filtering
# ---------------------------------------------------------------------------

GILGAMESH_NAMES_RE = re.compile(
    r"GI[ŠŠ][₂2]?[-.]?gim|giš[-.]?gim|GIŠ[-.]?GIM|dGIŠ\b|"
    r"en[-.]?ki[-.]?du|EN[-.]?KI[-.]?DU|"
    r"hum[-.]?ba[-.]?ba|hu[-.]?wa[-.]?wa|"
    r"ut[-.]?na[-.]?piš|si[-.]?du[-.]?ri",
    re.IGNORECASE,
)


def load_candidates(max_n: Optional[int] = None, min_score: int = 1) -> list[dict]:
    full_path = DATA_DIR / "ebl_fragments.json"
    sample_path = DATA_DIR / "ebl_fragments_sample.json"
    path = full_path if full_path.exists() else sample_path
    if not path.exists():
        raise FileNotFoundError(
            "No eBL fragment data found — run download_data.sh first."
        )

    print(f"Loading fragments from {path.name} …")
    with open(path) as f:
        fragments = json.load(f)
    print(f"  Total fragments: {len(fragments)}")

    candidates = []
    for frag in fragments:
        atf = frag.get("atf") or ""
        if len(atf.strip()) < 40:
            continue

        coll = frag.get("collection") or ""
        genre_cats = [
            c
            for g in (frag.get("genres") or [])
            for c in (g.get("category") or [])
        ]

        # Skip already-identified Gilgamesh fragments
        refs = frag.get("traditional_reference") or []
        notes = str((frag.get("notes") or {}).get("text", ""))
        desc = frag.get("description") or ""
        if any("gilgamesh" in str(r).lower() for r in refs):
            continue
        if "gilgamesh" in notes.lower() or "gilgameš" in notes.lower():
            continue
        if "gilgamesh" in desc.lower() or "gilgameš" in desc.lower():
            continue

        score = 0

        # Strongest signal: character name in ATF
        if GILGAMESH_NAMES_RE.search(atf):
            score += 5

        # Kuyunjik = Assurbanipal's library, source of ~90% of known Gilgamesh tablets
        if "Kuyunjik" in coll:
            score += 2

        # Literary genre
        if "Literature" in genre_cats or "Narrative" in genre_cats:
            score += 3

        # Neo-Assyrian script (the standard Gilgamesh period)
        period = (frag.get("script") or {}).get("period") or ""
        if "Neo-Assyrian" in period:
            score += 1

        if score >= min_score:
            frag["_score"] = score
            candidates.append(frag)

    candidates.sort(key=lambda x: x["_score"], reverse=True)
    print(f"  Candidates after pre-filtering: {len(candidates)}")

    if max_n:
        candidates = candidates[:max_n]
        print(f"  Limiting to top {len(candidates)}")

    return candidates


# ---------------------------------------------------------------------------
# System prompt construction
# ---------------------------------------------------------------------------

def load_tablet_atf_snippets() -> str:
    """Pull brief representative ATF lines from each Gilgamesh tablet."""
    snippets = []
    for numeral in ["I", "IV", "V", "VII", "IX", "XI"]:
        path = DATA_DIR / "gilgamesh" / f"tablet_{numeral}.json"
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        atf = data.get("atf") or ""
        # Grab the first real transliteration lines (skip headers)
        lines = [
            ln
            for ln in atf.splitlines()
            if ln and not ln.startswith(("#", "&", "$", "@")) and ". " in ln
        ][:TABLET_EXAMPLE_LINES]
        if lines:
            snippets.append(f"Tablet {numeral}:\n" + "\n".join(lines))

    return "\n\n".join(snippets)


def build_system_prompt() -> str:
    tablet_examples = load_tablet_atf_snippets()
    return f"""You are an expert Assyriologist specialising in the Standard Babylonian (SB) \
Epic of Gilgamesh — the world's oldest major literary work, composed on 12 clay tablets \
around 1200 BCE. Your task is to assess whether individual cuneiform fragments from the \
Electronic Babylonian Library (eBL) dataset could plausibly belong to this epic.

## The 12 tablets (brief content)

| Tablet | Content |
|--------|---------|
| I   | Gilgamesh of Uruk; creation of Enkidu by the gods |
| II  | Enkidu's civilisation; journey to Uruk; wrestling |
| III | Preparations for the cedar forest expedition |
| IV  | Journey to Lebanon cedar forest (99% lost — almost entirely missing) |
| V   | Battle with Humbaba the monster; felling of cedars |
| VI  | Ishtar's proposal; Bull of Heaven episode |
| VII | Death of Enkidu; his dream of the underworld |
| VIII| Gilgamesh's lament and Enkidu's burial |
| IX  | Gilgamesh wanders in grief; scorpion-men; mountain of sunrise |
| X   | Tavern-keeper Siduri; ferryman Ur-Shanabi; sea crossing |
| XI  | Utnapishti's flood narrative; plant of immortality; snake |
| XII | Sumerian appendix; Enkidu in the underworld |

## Key characters and cuneiform spellings

- **Gilgamesh**: dGIŠ, GIŠ-gim₂-maš, GIŠ-GIM-MAŠ, d{{GIŠ}}
- **Enkidu**: den-ki-du₁₀, EN-KI-DU₁₀
- **Humbaba / Huwawa**: hum-ba-ba, hu-wa-wa
- **Utnapishti** (flood hero): ut-na-piš-tim, UD-ZI
- **Siduri** (tavern-keeper): si-du-ri
- **Ur-Shanabi** (ferryman): ur-ša-na-bi
- **Ninsun** (Gilgamesh's mother): dnin-sun₂
- **Shamash** (solar patron): dUTU
- **Ishtar / Inanna**: diš-tar, INANNA

## Distinctive vocabulary and themes

- Cedar forest / Lebanon: GIŠ.TIRI, e-la-nu (cedar), šadû (mountain)
- Bull of Heaven: gu₄ AN-e, GU₄.AN.NA
- Plant of immortality: šammu (plant) + rejuvenation language
- Flood / deluge: a-bu-bu (abūbu), e-le-ep-pu (boat), GIŠ.MÁ
- Underworld: erṣetim, KI.GAL, māt lā târim ("land of no return")
- Scorpion-men (Tablet IX): aqrabu-amēlu, GIR₂.TAB.LÚ.U₁₈.LU
- Stone things / stone ones (Tablet XI): stone-pushers of the boat
- 2/3 divine, 1/3 human: šina šalušta, šīrū
- Royal city Uruk: UNUG, KI.EN.GI
- Lapis lazuli walls: uqnâ + dūru (wall)
- Typical formulaic pairs / repeated lines (oral-formulaic tradition)

## Provenance indicators

**Strong positive signal**:
- Kuyunjik (Nineveh / Assurbanipal's library, 7th c. BCE) — source of ~90% of known Gilgamesh tablets
- Neo-Assyrian script
- Literature / Narrative genre tag

**Neutral / weak**:
- Babylonian provenances (Sippar, Nippur, Babylon) — later Gilgamesh copies exist but are rarer
- Divination, Medical, Administrative genres (Gilgamesh names sometimes appear non-literarily)

## Sample lines from the canonical text

{tablet_examples}

---

For each fragment you receive, reason carefully about:
1. Whether any Gilgamesh character names appear (with their typical cuneiform variants)
2. Whether vocabulary, themes, or narrative elements match any of the 12 tablets
3. Whether the textual structure (poetic metre, repeated phrases, line patterns) fits Gilgamesh
4. Whether provenance and period are consistent
5. Whether the genre tags are consistent or misleading

Be conservative: many Kuyunjik fragments are divination or medical texts that mention Gilgamesh
names incidentally. Weight genuine narrative/literary language heavily. Give a low score when
the match is superficial (a name in a non-narrative context) and a high score when multiple
independent signals converge.

Respond ONLY with a JSON object — no prose before or after:
{{
  "confidence": <float 0.0–1.0>,
  "reasoning": "<2–4 sentences explaining the key signals or their absence>",
  "signals": ["<specific text element 1>", "…"],
  "tablet_hypothesis": "<e.g. 'possibly Tablet IX, scorpion-men passage' or '' if unclear>"
}}
"""


# ---------------------------------------------------------------------------
# Per-fragment prompt
# ---------------------------------------------------------------------------

def fragment_user_message(frag: dict) -> str:
    frag_id = frag.get("_id") or ""
    coll = frag.get("collection") or ""
    period = (frag.get("script") or {}).get("period") or ""
    genre_cats = [
        c
        for g in (frag.get("genres") or [])
        for c in (g.get("category") or [])
    ]
    desc = frag.get("description") or ""
    atf = (frag.get("atf") or "").strip()[:2500]

    lines = [f"Fragment: {frag_id}"]
    if coll:
        lines.append(f"Provenance: {coll}")
    if period:
        lines.append(f"Script period: {period}")
    if genre_cats:
        lines.append(f"Genre: {', '.join(genre_cats)}")
    if desc:
        lines.append(f"Description: {desc}")
    lines.append(f"\nATF transliteration:\n{atf}")
    lines.append(
        "\nAssess whether this fragment could be from the Epic of Gilgamesh. "
        "Reply with the JSON object only."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Classification: sequential (streaming, good for small sets)
# ---------------------------------------------------------------------------

def classify_sequential(
    candidates: list[dict],
    client: anthropic.Anthropic,
    system_prompt: str,
) -> dict[str, dict]:
    results: dict[str, dict] = {}

    for i, frag in enumerate(candidates):
        frag_id = frag.get("_id") or f"frag_{i}"
        print(f"  [{i+1}/{len(candidates)}] {frag_id} … ", end="", flush=True)

        try:
            response = client.messages.create(
                model="claude-opus-5-5",
                max_tokens=1024,
                thinking={"type": "adaptive"},
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {"role": "user", "content": fragment_user_message(frag)}
                ],
            )
            text = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            parsed = _parse_json_output(text)
            results[frag_id] = parsed
            print(f"confidence={parsed['confidence']:.2f}")

        except Exception as exc:
            print(f"ERROR: {exc}")
            results[frag_id] = _error_result(str(exc))

    return results


# ---------------------------------------------------------------------------
# Classification: Batches API (50% cost discount, async)
# ---------------------------------------------------------------------------

def submit_batch(
    candidates: list[dict],
    client: anthropic.Anthropic,
    system_prompt: str,
) -> str:
    """Submit a batch and return the batch ID."""
    RESULTS_DIR.mkdir(exist_ok=True)

    requests = [
        Request(
            custom_id=_custom_id(i, frag),
            params=MessageCreateParamsNonStreaming(
                model="claude-opus-5-5",
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[
                    {"role": "user", "content": fragment_user_message(frag)}
                ],
            ),
        )
        for i, frag in enumerate(candidates)
    ]

    print(f"Submitting batch of {len(requests)} requests …")
    batch = client.messages.batches.create(requests=requests)
    print(f"  Batch ID: {batch.id}")
    print(f"  Status:   {batch.processing_status}")

    # Persist batch ID + candidate index so the script can be resumed
    state = {
        "batch_id": batch.id,
        "candidates": [f.get("_id") for f in candidates],
        "submitted_at": time.time(),
    }
    with open(BATCH_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    return batch.id


def poll_batch(batch_id: str, client: anthropic.Anthropic) -> None:
    """Block until the batch has ended, printing status updates."""
    print("Polling for completion (checks every 30 s) …")
    consecutive_errors = 0
    while True:
        try:
            batch = client.messages.batches.retrieve(batch_id)
            consecutive_errors = 0
            c = batch.request_counts
            print(
                f"  {batch.processing_status:12s} | "
                f"processing: {c.processing:4d} | "
                f"succeeded: {c.succeeded:4d} | "
                f"errored: {c.errored:4d}"
            )
            if batch.processing_status == "ended":
                break
        except Exception as exc:
            consecutive_errors += 1
            print(f"  [network error #{consecutive_errors}: {exc}] retrying in 30 s …")
            if consecutive_errors >= 10:
                print(f"  Too many errors. Re-run with: --resume {batch_id}")
                raise
        time.sleep(30)


def collect_batch_results(
    batch_id: str,
    client: anthropic.Anthropic,
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for result in client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            text = next(
                (b.text for b in result.result.message.content if b.type == "text"),
                "",
            )
            results[result.custom_id] = _parse_json_output(text)
        else:
            results[result.custom_id] = _error_result(result.result.type)
    return results


def classify_with_batches(
    candidates: list[dict],
    client: anthropic.Anthropic,
    system_prompt: str,
) -> dict[str, dict]:
    batch_id = submit_batch(candidates, client, system_prompt)
    poll_batch(batch_id, client)
    raw = collect_batch_results(batch_id, client)

    # Re-key by fragment ID (batch keys are custom IDs, not fragment IDs)
    results: dict[str, dict] = {}
    for i, frag in enumerate(candidates):
        cid = _custom_id(i, frag)
        frag_id = frag.get("_id") or f"frag_{i}"
        results[frag_id] = raw.get(cid, _error_result("missing"))
    return results


# ---------------------------------------------------------------------------
# Result assembly + persistence
# ---------------------------------------------------------------------------

def assemble_and_save(
    candidates: list[dict],
    results: dict[str, dict],
    threshold: float,
) -> list[dict]:
    annotated = []
    for frag in candidates:
        frag_id = frag.get("_id") or ""
        r = results.get(frag_id, _error_result("not found"))
        genre_cats = [
            c
            for g in (frag.get("genres") or [])
            for c in (g.get("category") or [])
        ]
        annotated.append(
            {
                "id": frag_id,
                "collection": frag.get("collection") or "",
                "period": (frag.get("script") or {}).get("period") or "",
                "genres": genre_cats,
                "filter_score": frag.get("_score", 0),
                "atf_preview": (frag.get("atf") or "")[:300],
                "confidence": r.get("confidence", 0.0),
                "reasoning": r.get("reasoning", ""),
                "signals": r.get("signals", []),
                "tablet_hypothesis": r.get("tablet_hypothesis", ""),
            }
        )

    annotated.sort(key=lambda x: x["confidence"], reverse=True)

    RESULTS_DIR.mkdir(exist_ok=True)

    json_path = RESULTS_DIR / "semantic_filter_results.json"
    with open(json_path, "w") as f:
        json.dump(annotated, f, indent=2, ensure_ascii=False)
    print(f"\nFull results: {json_path}")

    top = [x for x in annotated if x["confidence"] >= threshold]
    csv_path = RESULTS_DIR / "semantic_filter_top.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id", "collection", "period", "genres", "filter_score",
                "confidence", "tablet_hypothesis", "signals", "reasoning", "atf_preview",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in top:
            writer.writerow(
                {**row, "signals": "; ".join(row["signals"])}
            )
    print(f"Top candidates (>= {threshold}): {csv_path}")

    return annotated


def print_summary(annotated: list[dict], threshold: float) -> None:
    top = [x for x in annotated if x["confidence"] >= threshold]
    print(f"\n{'='*62}")
    print(f"HIGH-CONFIDENCE CANDIDATES  (confidence >= {threshold}): {len(top)}")
    print(f"{'='*62}")
    for item in top[:25]:
        print(f"\n  {item['id']}  [{item['collection']}, {item['period']}]")
        print(f"  confidence: {item['confidence']:.2f}")
        if item["tablet_hypothesis"]:
            print(f"  hypothesis: {item['tablet_hypothesis']}")
        if item["signals"]:
            print(f"  signals:    {', '.join(item['signals'][:4])}")
        print(f"  reasoning:  {item['reasoning'][:180]}")
    if len(top) > 25:
        print(f"\n  … and {len(top) - 25} more")

    print(f"\n{'='*62}")
    print(f"SUMMARY  (total analysed: {len(annotated)})")
    print(f"  high   (>= 0.70): {sum(1 for x in annotated if x['confidence'] >= 0.70)}")
    print(f"  medium (0.35–0.70): {sum(1 for x in annotated if 0.35 <= x['confidence'] < 0.70)}")
    print(f"  low    (< 0.35): {sum(1 for x in annotated if x['confidence'] < 0.35)}")
    print(f"{'='*62}\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _custom_id(i: int, frag: dict) -> str:
    frag_id = re.sub(r"[^a-zA-Z0-9_-]", "_", frag.get("_id") or f"frag_{i}")
    return f"{i}_{frag_id}"[:64]


def _parse_json_output(text: str) -> dict:
    """Extract the JSON object from Claude's response text."""
    text = text.strip()
    # Strip any markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text.strip())
    # Find the outermost { … }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return _error_result(f"no JSON found in: {text[:120]}")
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        return _error_result(f"JSON parse error: {e}")


def _error_result(msg: str) -> dict:
    return {
        "confidence": 0.0,
        "reasoning": f"[error: {msg}]",
        "signals": [],
        "tablet_hypothesis": "",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample", type=int, metavar="N",
        help="Process only the top N candidates (useful for testing)",
    )
    parser.add_argument(
        "--sequential", action="store_true",
        help="Force sequential API calls instead of the Batches API",
    )
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Confidence threshold for top-candidates output (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--min-score", type=int, default=4, dest="min_score",
        help="Minimum pre-filter score to include (default: 4 — ~1k fragments with 2+ signals)",
    )
    parser.add_argument(
        "--resume", metavar="BATCH_ID",
        help="Resume collection of a previously submitted batch",
    )
    args = parser.parse_args()

    load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found.")
        print("       Copy .env.example → .env and add your key.")
        raise SystemExit(1)

    client = anthropic.Anthropic(api_key=api_key)
    RESULTS_DIR.mkdir(exist_ok=True)

    # -- Resume mode: collect results from an already-submitted batch -------
    if args.resume:
        print(f"Resuming batch {args.resume} …")
        if not BATCH_STATE_FILE.exists():
            print("ERROR: no batch_state.json found; cannot map custom_ids back to fragments.")
            raise SystemExit(1)
        with open(BATCH_STATE_FILE) as f:
            state = json.load(f)
        if state["batch_id"] != args.resume:
            print(f"WARNING: batch_state.json references {state['batch_id']}, not {args.resume}")

        # Reload the candidates in the same order so IDs line up
        all_candidates = load_candidates()
        id_set = set(state["candidates"])
        candidates = [f for f in all_candidates if f.get("_id") in id_set]

        poll_batch(args.resume, client)
        raw = collect_batch_results(args.resume, client)
        results: dict[str, dict] = {}
        for i, frag in enumerate(candidates):
            cid = _custom_id(i, frag)
            frag_id = frag.get("_id") or f"frag_{i}"
            results[frag_id] = raw.get(cid, _error_result("missing"))

        annotated = assemble_and_save(candidates, results, args.threshold)
        print_summary(annotated, args.threshold)
        return

    # -- Normal mode --------------------------------------------------------
    candidates = load_candidates(max_n=args.sample, min_score=args.min_score)
    if not candidates:
        print("No candidates found.")
        raise SystemExit(0)

    # Skip fragments already in the results file
    results_path = RESULTS_DIR / "semantic_filter_results.json"
    cached: dict[str, dict] = {}
    if results_path.exists():
        with open(results_path) as f:
            for row in json.load(f):
                if row.get("confidence", 0) > 0 or row.get("signals"):
                    cached[row["id"]] = {
                        "confidence": row["confidence"],
                        "reasoning": row["reasoning"],
                        "signals": row["signals"],
                        "tablet_hypothesis": row["tablet_hypothesis"],
                    }
        if cached:
            before = len(candidates)
            candidates = [c for c in candidates if c.get("_id") not in cached]
            print(f"  Skipping {before - len(candidates)} already-classified fragments (cached)")

    if not candidates:
        print("All candidates already classified — loading cached results.")
        annotated = assemble_and_save(
            load_candidates(max_n=args.sample, min_score=args.min_score),
            cached, args.threshold,
        )
        print_summary(annotated, args.threshold)
        return

    print("\nBuilding system prompt (loading Gilgamesh tablet ATFs) …")
    system_prompt = build_system_prompt()
    print(f"  System prompt length: {len(system_prompt):,} chars")

    use_sequential = args.sequential or len(candidates) <= 20
    mode = "sequential" if use_sequential else "Batches API"
    print(f"\nClassifying {len(candidates)} fragments via {mode} …")

    if use_sequential:
        new_results = classify_sequential(candidates, client, system_prompt)
    else:
        new_results = classify_with_batches(candidates, client, system_prompt)

    # Merge new results with cached ones before saving
    all_results = {**cached, **new_results}
    all_candidates = load_candidates(max_n=args.sample, min_score=args.min_score)
    annotated = assemble_and_save(all_candidates, all_results, args.threshold)
    print_summary(annotated, args.threshold)


if __name__ == "__main__":
    main()
