#!/usr/bin/env python3
"""
place_fragment.py

Attempt to place a fragment within the Epic of Gilgamesh by passing the
full canonical text of each tablet to Claude alongside the fragment ATF.

Usage:
    python place_fragment.py K.19276
    python place_fragment.py K.19276 --tablets III IV V
"""

import argparse
import json
from pathlib import Path

import anthropic
from utils import load_env

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

TABLETS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def load_fragment(fragment_id: str) -> dict:
    with open(DATA_DIR / "ebl_fragments.json") as f:
        for frag in json.load(f):
            if frag["_id"] == fragment_id:
                return frag
    raise ValueError(f"Fragment {fragment_id} not found")


def load_tablet_atf(numeral: str) -> str:
    path = DATA_DIR / "gilgamesh" / f"tablet_{numeral}.json"
    with open(path) as f:
        return json.load(f).get("atf", "")


def check_tablet(fragment: dict, tablet_numeral: str, client: anthropic.Anthropic) -> dict:
    tablet_atf = load_tablet_atf(tablet_numeral)
    frag_id = fragment["_id"]
    frag_atf = fragment.get("atf", "").strip()
    notes = fragment.get("notes", {}).get("text", "")

    prompt = f"""You are an expert Assyriologist specialising in the Standard Babylonian Epic of Gilgamesh.

Below is the complete canonical ATF text of Tablet {tablet_numeral}, followed by an unplaced fragment from Kuyunjik (Assurbanipal's library, Neo-Assyrian period).

Your task: determine whether this fragment could plausibly belong somewhere in Tablet {tablet_numeral}.

Work systematically:
1. Look at the preserved signs in the fragment — names, words, formulaic phrases, determinatives
2. Scan the tablet text for passages where those signs could fit into the gaps ([...], x, broken lines)
3. Consider whether the narrative context around any candidate gap is consistent with what the fragment preserves
4. If you find a plausible fit, specify the line numbers and explain exactly how the fragment's signs align with the gap

Be precise and honest. If the fragment does not fit this tablet, say so clearly and explain why.

---

TABLET {tablet_numeral} — CANONICAL ATF TEXT:

{tablet_atf}

---

FRAGMENT {frag_id} — ATF:

{frag_atf}

Scholar notes on file: {notes if notes else "none"}

---

Does this fragment fit anywhere in Tablet {tablet_numeral}? If yes, where exactly and how do the signs align?"""

    print(f"  Checking Tablet {tablet_numeral}...", end=" ", flush=True)

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    fits = any(w in text.lower() for w in ["fits", "match", "plausible", "could belong", "aligns", "consistent with"])
    print("possible fit" if fits else "no fit")

    return {
        "tablet": tablet_numeral,
        "verdict": text,
        "possible_fit": fits,
        "tokens": response.usage.input_tokens + response.usage.output_tokens,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fragment_id", help="Fragment ID, e.g. K.19276")
    parser.add_argument(
        "--tablets", nargs="+", default=["II", "III", "IV", "V", "VI"],
        help="Tablets to check (default: II III IV V VI)",
    )
    args = parser.parse_args()

    load_env()
    client = anthropic.Anthropic()

    print(f"Loading fragment {args.fragment_id}...")
    fragment = load_fragment(args.fragment_id)
    print(f"ATF:\n{fragment.get('atf','')}\n")
    print(f"Checking against tablets: {', '.join(args.tablets)}\n")

    results = []
    for tablet in args.tablets:
        result = check_tablet(fragment, tablet, client)
        results.append(result)

    # Save
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"placement_{args.fragment_id.replace('.', '_')}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*62}")
    print(f"PLACEMENT RESULTS FOR {args.fragment_id}")
    print(f"{'='*62}")

    fits = [r for r in results if r["possible_fit"]]
    if not fits:
        print("No tablet match found.")
    else:
        for r in fits:
            print(f"\nTablet {r['tablet']} — POSSIBLE FIT")
            print("-" * 40)
            print(r["verdict"])

    print(f"\nFull results saved to {out_path}")
    total_tokens = sum(r["tokens"] for r in results)
    print(f"Total tokens used: {total_tokens:,}")


if __name__ == "__main__":
    main()
