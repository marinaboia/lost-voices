# Semantic filter — run 1 findings

**Date:** 2026-09-30  
**Script:** `semantic_filter.py`  
**Model:** claude-opus-5-5  
**Fragments analysed:** 1,044 (pre-filtered from 23,289 eBL fragments by score ≥ 4)  
**Batch ID:** `msgbatch_01EXZwxpJKPkFgjynLvLRE4X`

## Method

Each candidate fragment was passed to Claude with:
- A system prompt describing all 12 tablets, character name spellings, key vocabulary, and sample canonical lines (cached across all requests)
- The fragment's full ATF transliteration and provenance metadata
- A request to score 0–1 and explain its reasoning

Pre-filter scoring (to select the 1,044 candidates):

| Signal | Points |
|---|---|
| Gilgamesh character name in ATF | +5 |
| Literature or Narrative genre tag | +3 |
| Kuyunjik provenance | +2 |
| Neo-Assyrian script period | +1 |

Fragments scoring ≥ 4 (i.e. at least two independent signals) were submitted to the model.

## Results

Full results: `results/semantic_filter_results.json`  
Top candidates: `results/semantic_filter_top.csv`

| Fragment | Confidence | Model hypothesis | eBL status |
|---|---|---|---|
| K.16024 | 0.95 | Tablet XI, Uruk-wall closing passage (XI 323ff.) | Already identified — description says "Gilgamesh tablet 11" |
| K.15145 | 0.90 | Tablet I, prologue lines 12–17 (walls of Uruk and Eanna) | Already identified — notes say "(+) Rm.785+ — Gilgamesh I" |
| K.19276 | 0.60 | Tablet II–III or V (speech formula + cedar forest signs) | **Unidentified** — description: "Uncertain. Neo-Assyrian." |
| K.21863 | 0.60 | Tablet VI (Ishtar address) or VII | Tentatively noted "Gilg VII?" by a scholar, unplaced |
| K.16980 | 0.35 | Tablet I or VII–VIII (Enkidu "born in the steppe") | Scholar note "cf. Gilg I 222-223" but unplaced |

Scores below 0.35 represent fragments where the model found only generic literary language or weak circumstantial signals (Kuyunjik provenance alone). 1,039 of 1,044 fragments scored below 0.35.

## Key observations

**The top two results validate the approach.** K.16024 and K.15145 are both already known Gilgamesh fragments — the model identified them correctly and matched them to specific line ranges without being told. Our pre-filter missed them because the identification was in the `description` and `notes` fields rather than `traditional_reference` (now fixed for future runs).

**K.19276 is the most interesting result.** It has no Gilgamesh identification anywhere in the eBL record — the model found it purely from the ATF text, identifying Gilgamesh's name twice in the standard Ninevite spelling, a speech-introduction formula (`[M]U-ar₂ ana {d}GIŠ-gim₂-[maš]`), and possible cedar forest signs (`[{giš}TIR? {giš}]EREN`). The notes only cross-reference three similar fragments (K.19260, K.19267, K.19334) with no content identification.

**K.21863** is tagged `Gilgameš` in eBL genres and noted "Gilg VII?" but never formally placed. The model disagreed on the tablet — it read the repeated feminine suffix `-ki` as Tablet VI (Gilgamesh addressing Ishtar) rather than VII. Worth adjudicating.

## Next steps — pilot study

The three genuinely unplaced fragments warrant a closer look:

1. **K.19276** — attempt to position within Tablets II, III, or V by matching the preserved signs against the known gaps in those tablets. The speech formula and cedar forest signs narrow the search space considerably.

2. **K.21863** — resolve the VI vs VII ambiguity. Compare line-endings against Tablet VI (Ishtar rejection, lines 1–79) and Tablet VII (Enkidu's lament and forest incantation) to see which gap the fragment fits.

3. **K.16980** — test the scholar's note "cf. Gilg I 222-223". If the Enkidu epithet "born in the steppe" fits that passage, check whether the surrounding signs are consistent with the gap context in Tablet I.

A matching script would take each fragment's preserved signs and attempt alignment against the canonical text gaps, tolerating broken signs (`x`, `[...]`, `#`) and spelling variants.
