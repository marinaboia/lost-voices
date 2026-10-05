#!/usr/bin/env python3
"""
lemma_eval.py

Compares Claude models on converting transliterated Akkadian to dictionary
forms (lemmas), scored against the eBL edition of SB Gilgamesh, where every
manuscript word carries its lemma (e.g. `TE-ka` → lētu, `li-im-haṣ` → mahāṣu).

The model is not told the text is Gilgamesh. It is asked for the lemma of each
numbered word, or nothing for words with no legible signs.

Sample: chunks of consecutive lines from single manuscripts —
  * chunks centred on lines from manuscript pairs that share no sign n-grams
    (the spelling-variant cases the n-gram matcher misses), and
  * random chunks.

Usage:
    python lemma_eval.py                      # default arms, default sample
    python lemma_eval.py --arms sonnet-low opus-medium --pairs 10 --random 10

Outputs (results/lemma_eval/):
    sample.json            the chunks sent (reproducible with --seed)
    raw_<arm>.jsonl        one API result per chunk (cached; reruns skip done chunks)
    report.json            metrics per arm
"""

import argparse
import json
import random
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

from ngram_matcher import TABLETS, _siglum, line_ngrams, load_poem, readable
from utils import load_env

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "results" / "lemma_eval"

ARMS = {
    "sonnet-low": ("claude-sonnet-5-5", "low"),
    "sonnet-medium": ("claude-sonnet-5-5", "medium"),
    "opus-low": ("claude-opus-5-5", "low"),
    "opus-medium": ("claude-opus-5-5", "medium"),
}
# Standard per-million-token prices (input, output); the Batch API halves these.
PRICES = {"claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0)}

# Function words shared by almost any two lines; excluded when asking whether a
# manuscript pair shares vocabulary.
# A broken sign or gap with nothing restored, e.g. x, [x, x], [...], (x).
BARE_BREAK = re.compile(r"\[?\(?x\)?\]?|\[?\.\.\.\]?")

STOP_LEMMAS = {"ana", "ina", "u", "ša", "ul", "lā", "la", "ištu", "itti", "kī", "kīma", "ma", "šū", "šī", "anāku", "atta"}

SYSTEM_PROMPT = """You are an Assyriologist. You will receive lines of an Akkadian text written in cuneiform, given as eBL ATF transliteration. Every word is numbered.

For each numbered word, give its lemma: the dictionary headword in normalized Akkadian, as cited in the CAD or the eBL dictionary (e.g. amēlu, mahāṣu, ina, šarru, lētu). Give an empty string when the word cannot be identified from what is written.

Rules:
- Work only from the signs that are written. Square brackets [ ] mark signs that are broken away; anything inside them is a modern restoration, not evidence. A word wholly inside brackets, a lone x, or [...] gets an empty string.
- A partly broken word (e.g. ṣ]a-mu-u₂) may be lemmatized if the visible signs are enough to identify it.
- # marks a damaged but readable sign, ? an uncertain reading, ! a corrected scribal error; read through them.
- Logograms (written in capitals, e.g. LU₂, DUMU, TE-ka, UGU-šu₂) stand for Akkadian words; give the Akkadian lemma (amēlu, māru, lētu, eli).
- Determinatives in braces ({d}, {giš}, {lu₂}, {ki}) belong to the word they mark; they are not words themselves.
- Give the bare headword without suffixes or inflection: verbs as the infinitive (mahāṣu), nouns in the nominative singular (amēlu).
- Proper names: the name as normally cited (e.g. Šamaš, Uruk).
- Do not identify the composition, and do not supply words from memory of any known text."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "integer"},
                    "lemmas": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "n": {"type": "integer"},
                                "lemma": {"type": "string"},
                            },
                            "required": ["n", "lemma"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["line", "lemmas"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["lines"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Gold data: manuscript words with their edition lemmas
# ---------------------------------------------------------------------------

READING_TYPES = {"Reading", "Logogram", "Number", "CompoundGrapheme", "Grapheme"}


def _flatten_parts(token: dict):
    for part in token.get("parts", []) or []:
        yield part
        yield from _flatten_parts(part)


def word_info(token: dict) -> dict:
    """Value, gold lemma, and whether any sign of the word is legible."""
    parts = list(_flatten_parts(token))
    readings = [p for p in parts if p.get("type") in READING_TYPES]
    visible = any(
        "BROKEN_AWAY" not in (p.get("enclosureType") or [])
        or "[" in p.get("value", "") or "]" in p.get("value", "")
        for p in readings
    )
    lemmas = token.get("uniqueLemma") or []
    return {
        "value": token.get("value", ""),
        "gold": [re.sub(r"\s+[IVX]+$", "", l) for l in lemmas],
        "visible": visible,
        "logogram": any(p.get("type") == "Logogram" for p in readings),
        "damaged": any(
            "BROKEN_AWAY" in (p.get("enclosureType") or []) or "#" in p.get("value", "")
            for p in readings
        ),
    }


def load_manuscript_lines() -> dict[tuple[str, int, str], dict]:
    """(tablet, pos, manuscript key) → {period, words}."""
    out = {}
    for tablet in TABLETS:
        chapter = json.loads((DATA_DIR / "gilgamesh" / f"tablet_{tablet}.json").read_text())
        by_id = {str(ms["id"]): ms for ms in chapter["manuscripts"]}
        for pos, line in enumerate(chapter["lines"]):
            for variant in line["variants"]:
                for entry in variant["manuscripts"]:
                    if entry["line"]["type"] != "TextLine":
                        continue
                    ms = by_id[str(entry["manuscriptId"])]
                    words = [
                        word_info(t) for t in entry["line"]["content"]
                        if t.get("type") in ("Word", "AkkadianWord", "LoneDeterminative")
                    ]
                    out[(tablet, pos, f"{tablet}:{_siglum(ms)}")] = {
                        "period": ms.get("period", ""),
                        "words": words,
                    }
    return out


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def no_overlap_pairs(lines) -> list[tuple]:
    """Manuscript pairs of one poem line, both legible, sharing no sign n-gram."""
    pairs = []
    for (tablet, pos), line in lines.items():
        sigla = [k for k, toks in line.witnesses.items() if readable(toks) >= 5]
        for i, a in enumerate(sigla):
            for b in sigla[i + 1 :]:
                if not line_ngrams(line.witnesses[a]) & line_ngrams(line.witnesses[b]):
                    pairs.append((tablet, pos, a, b))
    return pairs


def chunk_around(ms_lines, tablet, pos, ms_key, before=2, after=2):
    keys = [
        (tablet, p, ms_key) for p in range(pos - before, pos + after + 1)
        if (tablet, p, ms_key) in ms_lines
    ]
    return keys


def build_sample(n_pairs: int, n_random: int, seed: int) -> dict:
    rng = random.Random(seed)
    poem, _ = load_poem()
    ms_lines = load_manuscript_lines()

    pairs = no_overlap_pairs(poem)
    rng.shuffle(pairs)
    pairs = pairs[:n_pairs]

    chunks = []
    for tablet, pos, a, b in pairs:
        for ms_key in (a, b):
            chunks.append({"keys": chunk_around(ms_lines, tablet, pos, ms_key), "target": [tablet, pos, ms_key]})

    candidates = [k for k, v in ms_lines.items() if sum(w["visible"] for w in v["words"]) >= 3]
    rng.shuffle(candidates)
    for tablet, pos, ms_key in candidates[:n_random]:
        chunks.append({"keys": chunk_around(ms_lines, tablet, pos, ms_key), "target": None})

    for i, c in enumerate(chunks):
        c["id"] = f"c{i:03d}"
        c["keys"] = [list(k) for k in c["keys"]]
    return {
        "pairs": [list(p) for p in pairs],
        "chunks": chunks,
    }


# ---------------------------------------------------------------------------
# Model calls
# ---------------------------------------------------------------------------

def chunk_prompt(chunk: dict, ms_lines: dict) -> str:
    first = tuple(chunk["keys"][0])
    period = ms_lines[first]["period"]
    out = [f"Script period: {period}", ""]
    for i, key in enumerate(chunk["keys"], 1):
        words = ms_lines[tuple(key)]["words"]
        out.append(f"Line {i}: " + " ".join(f"{n}:{w['value']}" for n, w in enumerate(words, 1)))
    out.append("\nGive the lemma of every numbered word in every line.")
    return "\n".join(out)


def call_model(client, model: str, effort: str, prompt: str) -> dict:
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        output_config={
            "effort": effort,
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
        messages=[{"role": "user", "content": prompt}],
    )
    result = {
        "stop_reason": response.stop_reason,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    if response.stop_reason == "refusal":
        result["output"] = None
        return result
    text = next((b.text for b in response.content if b.type == "text"), "")
    result["output"] = json.loads(text) if text else None
    return result


def run_arm(arm: str, sample: dict, ms_lines: dict, workers: int) -> list[dict]:
    model, effort = ARMS[arm]
    path = OUT_DIR / f"raw_{arm}.jsonl"
    done = {}
    if path.exists():
        for row in map(json.loads, path.read_text().splitlines()):
            if "error" not in row:  # retry failed calls on the next run
                done[row["id"]] = row
    todo = [c for c in sample["chunks"] if c["id"] not in done]
    print(f"{arm}: {len(done)} cached, {len(todo)} to run")

    client = anthropic.Anthropic()

    def work(chunk):
        try:
            res = call_model(client, model, effort, chunk_prompt(chunk, ms_lines))
        except anthropic.APIStatusError as exc:
            res = {"error": f"{exc.status_code}: {exc.message}"}
        except anthropic.APIConnectionError as exc:
            res = {"error": f"connection: {exc}"}
        except json.JSONDecodeError as exc:
            res = {"error": f"json: {exc}"}
        res["id"] = chunk["id"]
        return res

    with ThreadPoolExecutor(max_workers=workers) as pool, open(path, "a") as f:
        for res in pool.map(work, todo):
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            done[res["id"]] = res
            status = res.get("error") or res.get("stop_reason")
            print(f"  {res['id']} {status}")

    return [done[c["id"]] for c in sample["chunks"] if c["id"] in done]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def norm(lemma: str, lenient: bool = False) -> str:
    s = unicodedata.normalize("NFC", lemma.strip().lower())
    s = s.replace("ḫ", "h").replace("’", "ʾ").replace("'", "ʾ")
    s = re.sub(r"\s+[ivx]+$", "", s)
    if lenient:
        # Ignore vowel length (ā/â → a); keep consonant distinctions (š, ṣ, ṭ).
        s = "".join(
            c for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn" or c in "̣̌"
        )
        s = unicodedata.normalize("NFC", s)
    return s


def score_arm(results: list[dict], sample: dict, ms_lines: dict, model: str) -> dict:
    by_id = {r["id"]: r for r in results}
    counts = {k: [0, 0, 0] for k in ("all", "logogram", "damaged", "clean")}  # strict, lenient, total
    abstained = restored = restorations = 0
    errors = refusals = 0
    in_tok = out_tok = 0
    predicted: dict[tuple, list[str]] = {}
    mistakes = []

    for chunk in sample["chunks"]:
        res = by_id.get(chunk["id"])
        if res is None:
            continue
        if "error" in res:
            errors += 1
            continue
        in_tok += res["input_tokens"]
        out_tok += res["output_tokens"]
        if res["output"] is None:
            refusals += 1
            continue
        out_lines = {l["line"]: {x["n"]: x["lemma"] for x in l["lemmas"]} for l in res["output"]["lines"]}

        for i, key in enumerate(chunk["keys"], 1):
            words = ms_lines[tuple(key)]["words"]
            preds = out_lines.get(i, {})
            predicted[tuple(key)] = [preds.get(n, "") for n in range(1, len(words) + 1)]
            for n, w in enumerate(words, 1):
                pred = preds.get(n, "").strip()
                if not w["visible"]:
                    # Bare x / [...] are trivially left blank; what matters is
                    # whether the model treats editorial restorations as evidence.
                    if not BARE_BREAK.fullmatch(w["value"].replace("#", "")):
                        restorations += 1
                        restored += bool(pred)
                    continue
                if not w["gold"]:
                    continue
                cats = ["all", "logogram" if w["logogram"] else ("damaged" if w["damaged"] else "clean")]
                if w["logogram"] and w["damaged"]:
                    cats.append("damaged")
                strict = any(norm(pred) == norm(g) for g in w["gold"])
                lenient = any(norm(pred, True) == norm(g, True) for g in w["gold"])
                abstained += not pred
                for c in cats:
                    counts[c][0] += strict
                    counts[c][1] += lenient
                    counts[c][2] += 1
                if not lenient and len(mistakes) < 40:
                    mistakes.append({"word": w["value"], "gold": w["gold"], "pred": pred})

    # Do the manuscript pairs that share no sign n-grams now share a lemma?
    def content_lemmas(key, source):
        if source == "gold":
            words = ms_lines[tuple(key)]["words"]
            lems = [g for w in words if w["visible"] for g in w["gold"]]
        else:
            lems = predicted.get(tuple(key), [])
        return {norm(l, True) for l in lems if l} - {norm(s, True) for s in STOP_LEMMAS}

    pair_hits = {"model": 0, "gold": 0, "total": 0}
    for tablet, pos, a, b in sample["pairs"]:
        ka, kb = (tablet, pos, a), (tablet, pos, b)
        if ka not in predicted or kb not in predicted:
            continue
        pair_hits["total"] += 1
        pair_hits["model"] += bool(content_lemmas(ka, "model") & content_lemmas(kb, "model"))
        pair_hits["gold"] += bool(content_lemmas(ka, "gold") & content_lemmas(kb, "gold"))

    p_in, p_out = PRICES[model]
    cost = (in_tok * p_in + out_tok * p_out) / 1e6
    total = counts["all"][2]
    return {
        "accuracy": {
            c: {"strict": round(s / t, 3) if t else None, "lenient": round(l / t, 3) if t else None, "words": t}
            for c, (s, l, t) in counts.items()
        },
        "abstained": round(abstained / total, 3) if total else None,
        "restorations_lemmatized": f"{restored}/{restorations}",
        "pairs_sharing_content_lemma": pair_hits,
        "errors": errors,
        "refusals": refusals,
        "tokens": {"input": in_tok, "output": out_tok},
        "cost_standard_usd": round(cost, 2),
        "cost_batch_usd": round(cost / 2, 2),
        "sample_mistakes": mistakes,
    }


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--arms", nargs="+", default=list(ARMS), choices=list(ARMS))
    parser.add_argument("--pairs", type=int, default=15, help="no-overlap manuscript pairs (2 chunks each)")
    parser.add_argument("--random", type=int, default=15, help="random chunks")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true", help="build the sample and show one prompt")
    args = parser.parse_args()

    load_env()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ms_lines = load_manuscript_lines()

    sample_path = OUT_DIR / "sample.json"
    if sample_path.exists():
        sample = json.loads(sample_path.read_text())
        print(f"Using existing sample ({len(sample['chunks'])} chunks); delete {sample_path.name} to resample")
    else:
        sample = build_sample(args.pairs, args.random, args.seed)
        sample_path.write_text(json.dumps(sample, ensure_ascii=False, indent=1))
    n_lines = sum(len(c["keys"]) for c in sample["chunks"])
    print(f"Sample: {len(sample['chunks'])} chunks, {n_lines} lines, {len(sample['pairs'])} pairs")

    if args.dry_run:
        print("\n" + SYSTEM_PROMPT + "\n\n---\n" + chunk_prompt(sample["chunks"][0], ms_lines))
        return

    report = {}
    for arm in args.arms:
        results = run_arm(arm, sample, ms_lines, args.workers)
        report[arm] = score_arm(results, sample, ms_lines, ARMS[arm][0])

    prev = json.loads((OUT_DIR / "report.json").read_text()) if (OUT_DIR / "report.json").exists() else {}
    prev.update(report)
    (OUT_DIR / "report.json").write_text(json.dumps(prev, ensure_ascii=False, indent=2))

    print(f"\n{'arm':14s} {'all':>6s} {'logo':>6s} {'damgd':>6s} {'clean':>6s} {'abst':>6s} {'restored':>9s} {'pairs':>7s} {'$std':>6s}")
    for arm, r in report.items():
        a = r["accuracy"]
        p = r["pairs_sharing_content_lemma"]
        print(f"{arm:14s} {a['all']['lenient'] or 0:6.1%} {a['logogram']['lenient'] or 0:6.1%} "
              f"{a['damaged']['lenient'] or 0:6.1%} {a['clean']['lenient'] or 0:6.1%} {r['abstained'] or 0:6.1%} "
              f"{r['restorations_lemmatized']:>9s} {p['model']:>3d}/{p['total']:<3d} {r['cost_standard_usd']:6.2f}")
    print("Accuracy is lenient (vowel length ignored). Pairs: model lemmas share a content word "
          "(gold upper bound in report.json).")


if __name__ == "__main__":
    main()
