#!/usr/bin/env python3
"""
ngram_matcher.py

Sign-level n-gram matcher that proposes *line positions* in the Standard
Babylonian Epic of Gilgamesh for eBL fragments. No API calls.

Unlike eBL's ngram-matcher (which scores whole texts — see related_work.md),
n-grams here are indexed per manuscript line, so a hit points to a specific
poem line. Fragment lines are then scored along "diagonals": a fragment whose
line i hits poem line j and whose line i+1 hits j+1 scores much higher than
scattered hits. N-grams are weighted by how rare they are across the whole
eBL Fragmentarium (IDF), so formulaic sequences count for little.

Usage:
    python ngram_matcher.py --fragment K.16980
    python ngram_matcher.py --benchmark
    python ngram_matcher.py --all

Inputs:
    data/gilgamesh/signs_<TABLET>.json   per-manuscript sign lines (eBL API)
    data/gilgamesh/tablet_<TABLET>.json  chapter lines + manuscript line entries
    data/ebl_fragments.json              fragments with `signs` and `atf`

Outputs:
    results/ngram_benchmark.json         leave-one-manuscript-out recall
    results/ngram_matches.csv            best candidate per fragment (--all)
"""

import argparse
import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

TABLETS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

N_VALUES = (2, 3, 4)
BROKEN = "X"
# Poem lines whose best witness preserves fewer readable signs than this are
# treated as gaps — places where a fragment could contribute new text.
GAP_THRESHOLD = 3
# Manuscripts number lines differently, so a fragment's next line may land one
# line before or after where a strict diagonal would put it.
DIAGONAL_SLACK = 1


# ---------------------------------------------------------------------------
# Signs and n-grams
# ---------------------------------------------------------------------------

def tokenize(sign_line: str) -> list[str]:
    return [BROKEN if "?" in tok else tok for tok in sign_line.split()]


def line_ngrams(tokens: list[str]) -> set[tuple[str, ...]]:
    """N-grams within one line, skipping any that contain a broken sign."""
    grams = set()
    for n in N_VALUES:
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i : i + n])
            if BROKEN not in gram:
                grams.add(gram)
    return grams


def readable(tokens: list[str]) -> int:
    return sum(tok != BROKEN for tok in tokens)


# ---------------------------------------------------------------------------
# Poem index
# ---------------------------------------------------------------------------

@dataclass
class PoemLine:
    tablet: str
    pos: int  # index into the chapter's line list; consecutive lines differ by 1
    label: str  # edition line number, e.g. "116" or "12′"
    reconstruction: str
    witnesses: dict[str, list[str]] = field(default_factory=dict)  # siglum → tokens

    @property
    def best_readable(self) -> int:
        return max((readable(t) for t in self.witnesses.values()), default=0)

    @property
    def is_gap(self) -> bool:
        return self.best_readable < GAP_THRESHOLD


def _line_label(number: dict) -> str:
    if number.get("type") == "LineNumberRange":
        return f"{_line_label(number['start'])}–{_line_label(number['end'])}"
    prime = "′" if number.get("hasPrime") else ""
    return f"{number.get('prefixModifier') or ''}{number['number']}{number.get('suffixModifier') or ''}{prime}"


def _reconstruction_text(variant: dict) -> str:
    return " ".join(
        tok.get("cleanValue", "")
        for tok in variant.get("reconstruction", [])
        if tok.get("type") not in ("LanguageShift",)
    ).strip()


def _siglum(ms: dict) -> str:
    return f"{ms['provenance']}{ms['period']}{ms['type']}{ms['siglumDisambiguator']}"


def load_poem() -> tuple[dict[tuple[str, int], PoemLine], dict[str, str]]:
    """
    Returns (lines keyed by (tablet, pos), manuscript key → museum number).

    eBL's chapter `signs` list holds one string per manuscript: its text lines
    in chapter order (empty lines excluded), then colophon and unplaced lines.
    We walk the chapter lines in the same order to map each sign line back to
    its poem position.
    """
    lines: dict[tuple[str, int], PoemLine] = {}
    museum_numbers: dict[str, str] = {}

    for tablet in TABLETS:
        chapter = json.loads((DATA_DIR / "gilgamesh" / f"tablet_{tablet}.json").read_text())
        signs = json.loads((DATA_DIR / "gilgamesh" / f"signs_{tablet}.json").read_text())

        for pos, line in enumerate(chapter["lines"]):
            lines[(tablet, pos)] = PoemLine(
                tablet=tablet,
                pos=pos,
                label=_line_label(line["number"]),
                reconstruction=_reconstruction_text(line["variants"][0]),
            )

        for ms, sign_text in zip(signs["manuscripts"], signs["signs"]):
            if not sign_text:
                continue
            ms_id = str(ms["id"])
            ms_key = f"{tablet}:{_siglum(ms)}"
            museum = ms.get("museumNumber") or {}
            if museum.get("prefix"):
                museum_numbers[ms_key] = f"{museum['prefix']}.{museum['number']}"

            positions = [
                pos
                for pos, line in enumerate(chapter["lines"])
                for variant in line["variants"]
                for entry in variant["manuscripts"]
                if str(entry["manuscriptId"]) == ms_id and entry["line"]["type"] == "TextLine"
            ]
            # Lines beyond `positions` are colophon / unplaced lines — skipped.
            for pos, sign_line in zip(positions, sign_text.split("\n")):
                lines[(tablet, pos)].witnesses[ms_key] = tokenize(sign_line)

    return lines, museum_numbers


class PoemIndex:
    def __init__(self, lines: dict[tuple[str, int], PoemLine], idf: dict):
        self.lines = lines
        self.idf = idf
        self.max_idf = max(idf.values()) if idf else 1.0
        # n-gram → list of (tablet, pos, manuscript key)
        self.postings: dict[tuple, list[tuple[str, int, str]]] = defaultdict(list)
        for (tablet, pos), line in lines.items():
            for ms_key, tokens in line.witnesses.items():
                for gram in line_ngrams(tokens):
                    self.postings[gram].append((tablet, pos, ms_key))
        # Number of distinct poem lines each n-gram occurs on. IDF alone misses
        # formulas that are rare in the Fragmentarium but recur throughout the
        # epic, e.g. "ana {d}GIŠ-gim₂-maš" ("to Gilgamesh").
        self.poem_df = {
            gram: len({(t, p) for t, p, _ in posts}) for gram, posts in self.postings.items()
        }

    def weight(self, gram: tuple) -> float:
        return self.idf.get(gram, self.max_idf) / self.poem_df.get(gram, 1)

    def line_hits(
        self, tokens: list[str], exclude_ms: Optional[str] = None
    ) -> dict[tuple[str, int], float]:
        """Score every poem line sharing n-grams with one fragment line."""
        shared: dict[tuple[str, int], set] = defaultdict(set)
        for gram in line_ngrams(tokens):
            for tablet, pos, ms_key in self.postings.get(gram, ()):
                if ms_key != exclude_ms:
                    shared[(tablet, pos)].add(gram)
        return {key: sum(self.weight(g) for g in grams) for key, grams in shared.items()}


def build_idf() -> dict[tuple, float]:
    """Line-level document frequency of each n-gram across the Fragmentarium."""
    fragments = json.loads((DATA_DIR / "ebl_fragments.json").read_text())
    df: Counter = Counter()
    n_lines = 0
    for frag in fragments:
        for sign_line in (frag.get("signs") or "").split("\n"):
            tokens = tokenize(sign_line)
            if readable(tokens) == 0:
                continue
            n_lines += 1
            df.update(line_ngrams(tokens))
    return {gram: math.log((n_lines + 1) / (count + 1)) for gram, count in df.items()}


# ---------------------------------------------------------------------------
# Diagonal scoring
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    tablet: str
    start: int  # poem position of the block's first line
    score: float
    aligned: list[tuple[int, Optional[int], float]]  # (block line, poem pos or None, score)


def place_block(
    index: PoemIndex,
    block: list[list[str]],
    exclude_ms: Optional[str] = None,
    top_k: int = 10,
) -> list[Candidate]:
    """
    Rank start positions for a block of consecutive fragment lines.

    Each hit of block line i on poem line j votes for start = j − i. A start's
    score sums, over block lines, the best hit within ±DIAGONAL_SLACK of where
    that line should land. Requiring agreement between lines is what separates
    a real placement from a formula that recurs throughout the epic.
    """
    hits_per_line = [index.line_hits(tokens, exclude_ms) for tokens in block]

    starts = {
        (tablet, pos - i)
        for i, hits in enumerate(hits_per_line)
        for tablet, pos in hits
    }

    candidates = []
    for tablet, start in starts:
        aligned = []
        for i, hits in enumerate(hits_per_line):
            best_pos, best = None, 0.0
            for slack in range(-DIAGONAL_SLACK, DIAGONAL_SLACK + 1):
                s = hits.get((tablet, start + i + slack), 0.0)
                if s > best:
                    best_pos, best = start + i + slack, s
            aligned.append((i, best_pos, best))
        score = sum(s for _, _, s in aligned)
        candidates.append(Candidate(tablet, start, score, aligned))

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:top_k]


# ---------------------------------------------------------------------------
# Fragments
# ---------------------------------------------------------------------------

ATF_TEXT_LINE = re.compile(r"^\S+\.\s")


def fragment_blocks(frag: dict) -> list[tuple[str, list[str], list[list[str]]]]:
    """
    Split a fragment into blocks of consecutive lines (one per surface/column),
    returning (block label, ATF lines, sign tokens per line).

    eBL `signs` has one line per ATF text line, in order, so the two can be
    zipped. Obverse and reverse sit far apart in the poem, so each is placed
    separately.
    """
    sign_lines = (frag.get("signs") or "").split("\n")
    blocks: list[tuple[str, list[str], list[list[str]]]] = []
    label, atf_block, sign_block = "", [], []
    i = 0
    for raw in (frag.get("atf") or "").splitlines():
        if raw.startswith("@") and not raw.startswith("@h"):
            if sign_block:
                blocks.append((label, atf_block, sign_block))
            label = (label.split(" ")[0] + " " if raw.startswith("@column") else "") + raw[1:]
            atf_block, sign_block = [], []
        elif ATF_TEXT_LINE.match(raw):
            if i < len(sign_lines):
                atf_block.append(raw)
                sign_block.append(tokenize(sign_lines[i]))
            i += 1
    if sign_block:
        blocks.append((label, atf_block, sign_block))
    return blocks


def load_fragments() -> dict[str, dict]:
    fragments = json.loads((DATA_DIR / "ebl_fragments.json").read_text())
    return {f["_id"]: f for f in fragments}


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def describe_candidate(index: PoemIndex, cand: Candidate, atf_lines: list[str]) -> str:
    out = [f"  Tablet {cand.tablet}, from line {index.lines[(cand.tablet, max(cand.start, 0))].label if (cand.tablet, max(cand.start, 0)) in index.lines else '?'} — score {cand.score:.1f}"]
    for i, pos, s in cand.aligned:
        target = pos if pos is not None else cand.start + i
        line = index.lines.get((cand.tablet, target))
        if line is None:
            where, status = "(outside tablet)", ""
        else:
            where = f"{cand.tablet} {line.label}"
            status = "GAP" if line.is_gap else f"{len(line.witnesses)} wit."
        out.append(f"    {atf_lines[i][:45]:45s} → {where:10s} {s:5.1f}  {status}")
        if line is not None:
            out.append(f"    {'':45s}   {line.reconstruction[:70]}")
    return "\n".join(out)


def run_fragment(index: PoemIndex, frag: dict, top_k: int) -> None:
    print(f"\n{frag['_id']}")
    for label, atf_lines, block in fragment_blocks(frag):
        print(f"\n [{label or 'text'}] {len(block)} lines, {sum(map(readable, block))} readable signs")
        for cand in place_block(index, block, top_k=top_k):
            if cand.score == 0:
                break
            print(describe_candidate(index, cand, atf_lines))


def run_all(index: PoemIndex, fragments: dict[str, dict], known: set[str]) -> None:
    rows = []
    for frag_id, frag in fragments.items():
        if frag_id in known or not frag.get("signs"):
            continue
        for label, _, block in fragment_blocks(frag):
            if sum(map(readable, block)) < 4:
                continue
            cands = place_block(index, block, top_k=2)
            if not cands or cands[0].score == 0:
                continue
            best = cands[0]
            runner_up = cands[1].score if len(cands) > 1 else 0.0
            matched = sum(1 for _, pos, s in best.aligned if s > 0)
            start = index.lines.get((best.tablet, best.start))
            notes = " ".join([
                str((frag.get("notes") or {}).get("text", "")),
                frag.get("description") or "",
                str(frag.get("traditional_reference") or ""),
            ])
            rows.append({
                "fragment": frag_id,
                # eBL already identifies it as Gilgamesh (e.g. a join to a known
                # manuscript) — useful as a sanity check, not a discovery.
                "known_gilgamesh": bool(re.search(r"gilg", notes, re.IGNORECASE)),
                "genre": "; ".join("/".join(g.get("category") or []) for g in frag.get("genres") or []),
                "block": label,
                "lines": len(block),
                "lines_matched": matched,
                "tablet": best.tablet,
                "start_line": start.label if start else f"pos {best.start}",
                "score": round(best.score, 2),
                "margin": round(best.score - runner_up, 2),
                "fills_gap": any(
                    s == 0 and index.lines.get((best.tablet, best.start + i)) is not None
                    and index.lines[(best.tablet, best.start + i)].is_gap
                    for i, _, s in best.aligned
                ),
            })

    rows.sort(key=lambda r: (r["lines_matched"] >= 2, r["score"]), reverse=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / "ngram_matches.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} fragment blocks to {path}")
    for r in rows[:25]:
        print(r)


def run_benchmark(index: PoemIndex, sample: int, seed: int) -> None:
    """
    Leave-one-manuscript-out: cut each manuscript into 1–3 line windows, query
    with that manuscript excluded from the index, and check whether the true
    position comes back.

    A window is "matchable" only if some other manuscript witnesses at least
    one of its lines with a shared n-gram — otherwise no sign matcher could
    find it, and it would only measure gaps in the edition.
    """
    by_ms: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for key, line in sorted(index.lines.items(), key=lambda kv: (TABLETS.index(kv[0][0]), kv[0][1])):
        for ms_key in line.witnesses:
            by_ms[ms_key].append(key)

    windows = []
    for ms_key, keys in by_ms.items():
        for length in (1, 2, 3):
            for i in range(len(keys) - length + 1):
                run = keys[i : i + length]
                # Only consecutive poem lines form a realistic fragment.
                if any(b[1] - a[1] != 1 for a, b in zip(run, run[1:])):
                    continue
                block = [index.lines[k].witnesses[ms_key] for k in run]
                if sum(map(readable, block)) < 4:
                    continue
                windows.append((ms_key, length, run, block))

    random.Random(seed).shuffle(windows)
    if sample:
        windows = windows[:sample]

    stats: dict = defaultdict(lambda: Counter())
    for ms_key, length, run, block in windows:
        tablet, true_start = run[0]
        matchable = any(
            index.line_hits(tokens, exclude_ms=ms_key).get(k, 0) > 0
            for k, tokens in zip(run, block)
        )
        cands = place_block(index, block, exclude_ms=ms_key, top_k=10)
        rank = next(
            (r for r, c in enumerate(cands, 1)
             if c.tablet == tablet and abs(c.start - true_start) <= DIAGONAL_SLACK and c.score > 0),
            None,
        )
        for bucket in (f"{length} line(s)", "all"):
            s = stats[bucket]
            s["windows"] += 1
            s["matchable"] += matchable
            if matchable:
                for k in (1, 5, 10):
                    s[f"top{k}"] += rank is not None and rank <= k

    report = {}
    print(f"\nLeave-one-manuscript-out benchmark ({len(windows)} windows)")
    print(f"{'':12s} {'windows':>8s} {'matchable':>10s} {'top1':>7s} {'top5':>7s} {'top10':>7s}")
    for bucket in ("1 line(s)", "2 line(s)", "3 line(s)", "all"):
        s = stats[bucket]
        m = max(s["matchable"], 1)
        row = {
            "windows": s["windows"],
            "matchable": s["matchable"],
            **{f"top{k}": round(s[f"top{k}"] / m, 3) for k in (1, 5, 10)},
        }
        report[bucket] = row
        print(f"{bucket:12s} {row['windows']:8d} {row['matchable']:10d} "
              f"{row['top1']:7.1%} {row['top5']:7.1%} {row['top10']:7.1%}")
    print("Recall is over matchable windows; a hit is the right tablet with start within "
          f"±{DIAGONAL_SLACK} line.")

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "ngram_benchmark.json").write_text(json.dumps(report, indent=2))


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fragment", nargs="+", help="fragment id(s) to place, e.g. K.16980")
    mode.add_argument("--benchmark", action="store_true", help="leave-one-manuscript-out recall")
    mode.add_argument("--all", action="store_true", help="best candidate for every fragment")
    parser.add_argument("--top", type=int, default=5, help="candidates to show per block")
    parser.add_argument("--sample", type=int, default=5000, help="benchmark windows (0 = all)")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print("Loading poem and building index …")
    lines, museum_numbers = load_poem()
    index = PoemIndex(lines, build_idf())
    n_witness_lines = sum(len(l.witnesses) for l in lines.values())
    print(f"  {len(lines)} poem lines, {n_witness_lines} manuscript lines, {len(index.postings)} n-grams")

    if args.benchmark:
        run_benchmark(index, args.sample, args.seed)
        return

    fragments = load_fragments()
    if args.fragment:
        for frag_id in args.fragment:
            run_fragment(index, fragments[frag_id], args.top)
    else:
        run_all(index, fragments, known=set(museum_numbers.values()))


if __name__ == "__main__":
    main()
