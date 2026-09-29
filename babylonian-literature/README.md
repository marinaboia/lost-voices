# Babylonian Literature

Hunt for missing fragments and lost lines of cuneiform literature — especially Gilgamesh — using the eBL and CDLI open datasets.

## Mission

### The problem: Gilgamesh is half missing

The Epic of Gilgamesh is the oldest major work of literature on Earth — written on 12 clay tablets, roughly 3,000 lines in its Standard Babylonian version. About 40–50% of the text is gone. Large stretches of Tablet IV are missing. Tablet X (where Gilgamesh meets the tavern-keeper and the ferryman on his journey to find immortality) has whole sections lost. Tablet III is barely there.

The most recent major discovery happened in 2014, when a fragment in a museum in Sulaymaniyah (Iraqi Kurdistan) was identified and added 20 entirely new lines to Tablet V — the Cedar Forest episode where Gilgamesh and Enkidu fight the monster Humbaba. The fragment had been sitting in a drawer, unrecognised. That is exactly the kind of find this project is looking for.

Measured against the canonical eBL text, **70% of all lines have at least one gap**:

| Tablet | Content | Gap lines | Gap % |
|--------|---------|-----------|-------|
| I | 300 | 148 | 49% |
| II | 187 | 143 | 76% |
| III | 209 | 149 | 71% |
| IV | 156 | 155 | **99%** |
| V | 281 | 235 | 84% |
| VI | 195 | 109 | 56% |
| VII | 220 | 193 | 88% |
| VIII | 216 | 182 | 84% |
| IX | 137 | 112 | 82% |
| X | 328 | 263 | 80% |
| XI | 339 | 97 | 29% |
| XII | 139 | 104 | 75% |
| **Total** | **2707** | **1890** | **70%** |

Tablet XI (the Flood tablet) is the best-preserved at 29% gaps — it was the most copied and distributed. Tablet IV is almost entirely lost. Tablet X, where Gilgamesh wanders the wilderness after Enkidu's death and meets the tavern-keeper Siduri, is 80% broken.

### Where the missing pieces are

The full eBL dataset has 23,289 fragments. Only 35 are explicitly tagged as Gilgamesh — because most unidentified fragments haven't been placed yet. Almost every line in those 35 has `[...]` breaks or unreadable signs. For example, fragment `K.18183` covers just 6 lines of Tablet IX and half of those are broken:

```
1'. [x] x x [...]
2'. 2 DANN[A ...]
3'. ša₂-pat ek-l[i-tum₃-ma ...]
4'. ul i-na-a[n-din ...]
```

The most promising targets are the thousands of unassigned Neo-Assyrian fragments from Kuyunjik — the site of Assurbanipal's library at Nineveh, the largest text collection in antiquity, and the source of most known Gilgamesh tablets. The eBL dataset alone has 250 unplaced Kuyunjik fragments. None of them have been matched against the gaps in Gilgamesh.

### The approach

Tens of thousands of clay tablets from ancient Mesopotamia sit in museum collections, many never fully published. Fragments that once belonged to the same tablet are scattered across institutions and have never been matched. The goal here is to build an agent that proposes joins — "fragment X continues fragment Y" — and missing-line restorations, with confidence scores that a human curator can verify against the physical tablets.

The current best method uses overlapping n-grams of cuneiform signs. There is room to do better: fuzzy matching for spelling variants and broken signs, parallel-version detection, and meaning-level similarity rather than exact sign runs.

A verified find would be the first new lines of Gilgamesh discovered by AI.

## Datasets

Run `bash download_data.sh` from this directory to fetch everything into `data/` (not committed to git).

| File | Size | Description |
|---|---|---|
| `data/ebl_fragments.json` | ~70 MB | Full eBL dataset — ~25k transliterated tablets from LMU Munich. Snapshot: 1 Sept 2023. License: CC BY-NC-SA 4.0. |
| `data/ebl_fragments_sample.json` | ~4 MB | 1k tablet sample from the same source — good for fast iteration. |
| `data/cdliatf_unblocked.atf` | ~83 MB | CDLI full ATF dump — hundreds of thousands of tablets in standard cuneiform transliteration format. Frozen Aug 2022. |
| `data/cdli_cat.csv` | ~148 MB | CDLI catalogue — metadata (provenance, period, genre) for all tablets in the ATF dump. |
| `data/gilgamesh/tablet_I.json` … `tablet_XII.json` | ~2 MB total | Canonical text of all 12 Standard Babylonian tablets from the eBL API. Each file includes the ATF text, English translation, manuscript variants, and gap markers. This is the "puzzle board" — the known text with holes that unidentified fragments may fill. |

### Key fields in `ebl_fragments.json`

Each fragment is a JSON object with:
- `_id` / `museumNumber` — physical accession number (e.g. `1848,0720.121`)
- `atf` — transliterated cuneiform text; `[...]` marks broken or missing sections
- `signs` — raw sign names (e.g. `ABZ449 ABZ480`) for n-gram matching
- `collection` — excavation site (Babylon, Kuyunjik/Nineveh, Sippar, Nippur)
- `script.period` — date (mostly Neo-Babylonian and Neo-Assyrian)
- `museum` — physical location (932/1000 in the British Museum)
- `genres` — content category (Divination, Literary, Administrative, etc.)

### ATF format (`.atf` files)

Standard format used by both eBL and CDLI. Lines starting with `@` are structural markers (obverse, reverse, column). Sign transliterations use subscript numbers for disambiguation (`U₄`, `KAM₂`). `#` marks uncertain readings; `x` marks unreadable signs.

## Pipeline

1. **Calibrate** — hide the 1,250 known joins already in eBL and see how many the agent rediscovers. Establishes a real precision/recall baseline.
2. **Match** — run across all unassigned fragments, score candidates.
3. **Propose** — output top 20–50 joins with confidence scores.
4. **Verify** — send to Enrique Jiménez (eBL team, LMU Munich) to check against physical tablets.

## Sources

- [eBL API (GitHub)](https://github.com/ElectronicBabylonianLiterature/ebl-api)
- [eBL dataset (Zenodo)](https://doi.org/10.5281/zenodo.10018951)
- [Transliterated Cuneiform Tablets of the eBL Platform (JOHD)](https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.148)
- [About: eBL](https://www.ebl.lmu.de/about)
- [LMU Munich harnesses AI (Nature)](https://www.nature.com/articles/d42473-020-00366-8)
- [CDLI tools and data list](https://cdli-gh.github.io/guides/guide_tools_list.html)
