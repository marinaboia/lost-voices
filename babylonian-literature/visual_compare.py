#!/usr/bin/env python3
"""
visual_compare.py

Compare a fragment photo against one or more tablet witness photos using
Claude's vision. Useful for checking whether a fragment is visually
consistent with a proposed placement (script style, line density, rulings).

Usage:
    python visual_compare.py K.19276 --witnesses tablet_v/K.3252 tablet_v/K.8591
    python visual_compare.py K.19276 --witnesses tablet_v/K.3252 --atf "obv 6'. [... spoke to Gilgamesh]"
    python visual_compare.py K.21863 --witnesses tablet_v/Sm.209

Fragment image must exist at data/images/<fragment_id>.jpg
Witness images must exist at data/images/<witness>.jpg

Outputs:
    results/visual_compare_<fragment_id>.txt
"""

import argparse
import base64
from pathlib import Path

import anthropic
from utils import load_env

DATA_DIR = Path(__file__).parent / "data" / "images"
RESULTS_DIR = Path(__file__).parent / "results"


def load_image_b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()


def build_content(fragment_id: str, witness_ids: list[str], atf_note: str) -> list:
    content = []

    # Fragment image
    frag_path = DATA_DIR / f"{fragment_id}.jpg"
    if not frag_path.exists():
        raise FileNotFoundError(f"Fragment image not found: {frag_path}")
    content.append({"type": "text", "text": f"IMAGE 1 — Fragment {fragment_id} (the unplaced fragment):"})
    content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": load_image_b64(frag_path)}})

    # Witness images
    for i, wid in enumerate(witness_ids, start=2):
        w_path = DATA_DIR / f"{wid}.jpg"
        if not w_path.exists():
            raise FileNotFoundError(f"Witness image not found: {w_path}")
        content.append({"type": "text", "text": f"IMAGE {i} — Witness {wid} (known Gilgamesh tablet):"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": load_image_b64(w_path)}})

    # Prompt
    atf_section = f"\nProposed ATF / placement note:\n{atf_note}\n" if atf_note else ""
    witnesses_str = ", ".join(witness_ids)
    prompt = f"""You are an expert Assyriologist examining cuneiform tablet photographs from the British Museum.

IMAGE 1 is fragment {fragment_id} — an unplaced Kuyunjik (Neo-Assyrian) fragment.
IMAGES 2+ are known Gilgamesh tablet witnesses ({witnesses_str}) from the same Kuyunjik collection.
{atf_section}
Please assess the following, being specific and honest about what is and is not visible:

1. How many lines of cuneiform are visible on the obverse of {fragment_id}?
2. Is a horizontal ruling line visible on {fragment_id}?
3. Are the fragments visually consistent in cuneiform style, sign size, and line density?
4. Does the physical size and line count of {fragment_id} support or contradict the proposed placement?
5. Can you make out any individual signs or sign groups on {fragment_id}? If so, which?
6. What would be needed to confirm or refute the placement from a physical standpoint?"""

    content.append({"type": "text", "text": prompt})
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fragment_id", help="Fragment ID, e.g. K.19276")
    parser.add_argument(
        "--witnesses", nargs="+", required=True,
        help="Witness image IDs relative to data/images/, e.g. tablet_v/K.3252",
    )
    parser.add_argument(
        "--atf", default="",
        help="Optional ATF or placement note to include in the prompt",
    )
    args = parser.parse_args()

    load_env()
    client = anthropic.Anthropic()

    print(f"Comparing {args.fragment_id} against: {', '.join(args.witnesses)}")
    content = build_content(args.fragment_id, args.witnesses, args.atf)

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=16000,
        messages=[{"role": "user", "content": content}],
    )

    text = next((b.text for b in response.content if b.type == "text"), "[no text output]")
    print(text)

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"visual_compare_{args.fragment_id.replace('.', '_')}.txt"
    with open(out_path, "w") as f:
        f.write(text)
    print(f"\nSaved to {out_path}")
    print(f"Tokens used: {response.usage.input_tokens:,} in / {response.usage.output_tokens:,} out")


if __name__ == "__main__":
    main()
