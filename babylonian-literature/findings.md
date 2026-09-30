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

**K.19276 is the most interesting result.** See the placement study below.

**K.21863** is tagged `Gilgameš` in eBL genres and noted "Gilg VII?" but never formally placed. The model disagreed on the tablet — it read the repeated feminine suffix `-ki` as Tablet VI (Gilgamesh addressing Ishtar) rather than VII. Worth adjudicating.

## Next steps — pilot study

The three genuinely unplaced fragments warrant a closer look:

1. **K.19276** — attempt to position within Tablets II, III, or V by matching the preserved signs against the known gaps in those tablets. The speech formula and cedar forest signs narrow the search space considerably.

2. **K.21863** — resolve the VI vs VII ambiguity. Compare line-endings against Tablet VI (Ishtar rejection, lines 1–79) and Tablet VII (Enkidu's lament and forest incantation) to see which gap the fragment fits.

3. **K.16980** — test the scholar's note "cf. Gilg I 222-223". If the Enkidu epithet "born in the steppe" fits that passage, check whether the surrounding signs are consistent with the gap context in Tablet I.

A matching script would take each fragment's preserved signs and attempt alignment against the canonical text gaps, tolerating broken signs (`x`, `[...]`, `#`) and spelling variants.

---

## K.19276 — placement study

**Script:** `place_fragment.py`  
**Method:** Full canonical ATF of each tablet passed to claude-opus-5-5 alongside the fragment, tablet by tablet, with a prompt asking the model to attempt line-by-line alignment against the gaps.  
**Full output:** `results/placement_K_19276.json`

### Fragment

```
@obverse
1'. [...] x x [x x]
2'. [... {d}GIŠ-gi]m₂-maš x [x x]
3'. [...] TUR ša₂? [x x]
4'. [...] MAŠ?# U₂# AŠ? [x x]
$ single ruling
5'. [...] x x ka-a-ar ina BARA₂# ri-[x x]
6'. [... M]U-ar₂# ana {d}GIŠ-gim₂-[maš]
7'. [...] mi#-na#-a# x x x a x [x x]
@reverse
2'. [... {giš}TIR? {giš}]EREN ga mu [...]
```

### Fragment status

Deeper inspection of the eBL record reveals more than was initially visible:

- **`publication: "Gilgamesh II 035, ZZ"`** — the fragment is catalogued in Andrew George's definitive edition *The Babylonian Gilgamesh Epic* (Oxford, 2003), Volume II, entry 035. "ZZ" is George's notation for fragments suspected to belong to the epic but whose position is unknown.
- **George transliterated it himself** — the record shows a `HistoricalTransliteration` by `George` dated 1977–2012.
- **Revised five times by the eBL team** — including two revisions by Jiménez (George's successor at eBL) as recently as October 2021.
- **Still unplaced** — no text assignment, no genre tag, no `traditional_reference` as of the September 2023 eBL snapshot.
- **Cross-references are unrelated** — K.19260 is a glass-making text, K.19267 incantations, K.19334 a birth-omen series. The "cf." note is likely a physical shelf comparison, not a content link.

In short: George knew about this fragment, included it in his catalogue as a suspected Gilgamesh piece, but could not place it. The eBL team has returned to it multiple times and also left it unplaced.

### Proposed placement — Tablet V, lines 115–116

After checking Tablets II through VI, the model found a plausible fit only in **Tablet V**:

| Fragment line | Proposed = Tablet V line | Alignment |
|---|---|---|
| obv. 1′–4′ | within gap V 107–114 | Unverifiable; Gilgamesh's name in 2′ suits the confrontation scene after Humbaba's roar (V 106) |
| ruling | section break before Humbaba's speech | Consistent with manuscript conventions |
| obv. 5′ | narrative line before V 115 (lost in all witnesses) | ARG Folio 114 reading `IGI-MIN-šu₂` ("his eyes") suits a description of Humbaba before he speaks |
| **obv. 6′** | **V 115** | `[{d}hum-ba-ba pa-a-šu₂ DU₃-ma DUG₄.GA M]U-ar₂ ana {d}GIŠ-gim₂-[maš]` — Humbaba opens his mouth and speaks to Gilgamesh. `MU-ar₂` is a Nineveh spelling variant of `MU-ra` (*izakkara*). |
| **obv. 7′** | **V 116** | `[lim-tal-ku lil-lu {d}GIŠ-gim₂-maš nu-ʾ-u₂ a-me-lu] mi-na-a tal-l[i-kam a-di IGI-ia]` — "Gilgamesh, you fool, why have you come before me?" The `a` trace after `mi-na-a` would be `a-[di]`. |

Tablet V line 116 is Humbaba's famous taunt: *"Gilgamesh, you fool — why have you come before me?"* It is one of the most recognisable lines in the epic.

### What this placement would and would not contribute

Lines 115–116 are **not lost** — they already survive in UrkNB1, the Neo-Babylonian witness from Uruk. Placing K.19276 would not add new text to the epic. The contribution is narrower but still meaningful:

- **A second witness** — K.19276 would be the first Kuyunjik (Nineveh) copy of these two lines, allowing comparison between the Nineveh and Uruk scribal traditions for the same passage.
- **Textual variants** — any spelling differences between the two traditions (e.g. `MU-ar₂` vs `MU-ra`) are of interest to editors of the text.
- **Closing an open question** — George catalogued this fragment as ZZ (suspected Gilgamesh, position unknown) over twenty years ago. Confirming its placement resolves that.

The broken lines 1′–4′ fall within the completely-lost gap V 107–114, but they are too damaged on the fragment to yield readable new text.

### Caveats

- The placement rests on two short sequences (the speech formula and *mīnâ*) and one unexplained line (5′).
- The reverse cedar signs are consistent with the Humbaba episode but not independently diagnostic.
- Other tablets with a "said to Gilgamesh" + question structure (II–IV, VI–VII) cannot be formally excluded.
- The spelling `MU-ar₂` vs `MU-ra` is a minor variant consistent with Nineveh manuscripts but adds a small uncertainty.

### Image analysis

Fragment photos were retrieved from the eBL API (`data/images/K.19276.jpg`) and compared against the main Kuyunjik Tablet V witnesses K.3252, K.8591, Sm.209, Sm.866, K.13525 (`data/images/tablet_v/`). Full model output: `results/visual_comparison_K19276.txt`.

Key findings from the visual comparison:

- **Ruling confirmed** — a clear horizontal ruling is visible on the inscribed face, consistent with the ATF's `$ single ruling` between lines 4′ and 5′.
- **Only 3–4 lines legible** — much of the surface is worn. The face carrying the ink number "K 19276" is largely abraded; the inscribed face shows traces above and below the ruling.
- **Physical size ~4.5 × 5.5 cm** — large enough to hold ~9 lines at the ~0.45 cm line spacing typical of these Kuyunjik tablets.
- **Script style compatible** — same Neo-Assyrian ductus and line density as K.3252, consistent with Assurbanipal's library.
- **No individual signs readable from the photograph** — the surface condition means sign-level confirmation requires RTI (Reflectance Transformation Imaging) or physical collation at the British Museum.

### Suggested next steps

#### What we can already read

Obverse line 7′ of K.19276 gives us: `[...] mi#-na#-a# x x x a x [x x]`

`mi-na-a` is Akkadian *mīnâ* — "why?" The signs after it are present but unreadable from the photograph because the clay surface is abraded.

#### What the proposed placement predicts

If this is Tablet V line 116 — Humbaba's taunt — the full line should read:

> `[lim-tal-ku lil-lu {d}GIŠ-gim₂-maš nu-ʾ-u₂ a-me-lu] mi-na-a tal-li-ka a-di IGI-ia`
> *"You fool, Gilgamesh, you ignorant man — why have you come before me?"*

The traces after `mi-na-a` should therefore spell `tal-li-ka a-di IGI-ia` (or a close orthographic variant). The one sign the ATF transcriber *did* recover — the `a` in `mi-na-a x x x **a** x` — is consistent with the `a` of `a-di` ("before"), which is exactly where it would fall.

#### Why the photo is not enough

Cuneiform is pressed into clay; it is relief, not ink. When the surface weathers over 2,700 years the wedge impressions become shallower and vanish from normal photographs. The eBL image confirms the tablet exists and has lines, but individual sign shapes are lost.

#### Two routes to confirmation

**1. RTI imaging** — Reflectance Transformation Imaging takes ~50 photos under a light source moved to different positions around the tablet, then algorithmically combines them. Raking light at extreme angles casts tiny shadows into even very shallow wedge impressions, making them readable again. This is now standard practice for abraded British Museum tablets and is the fastest route — no travel required if the BM conservation lab runs it.

**2. Physical collation** — An Assyriologist examining the original tablet at the BM under a magnifying glass and raking lamp can sometimes read traces that do not photograph. George himself collated this fragment for his 2003 edition (his transliteration is in the eBL record). The question is whether anyone has returned to it with the Tablet V 115–116 hypothesis in mind.

#### The specific test

The check is narrow: can the traces after `mi-na-a` on line 7′ be read as `tal-li-[kam]`? The verbal form *tallikam* ("you have come") is highly specific — it appears in this exact phrasing in the Uruk witness (UrkNB1), currently the *only* known copy of these two lines. A match in the Kuyunjik tradition would be very difficult to explain otherwise.

#### Why it matters

UrkNB1 is from Uruk, southern Babylonia, Neo-Babylonian period — a different scribal tradition from Assurbanipal's Nineveh library. K.19276 would be the first Kuyunjik copy of this passage, allowing scholars to compare the two regional versions of Humbaba's taunt for the first time.

The physical tablet is held at the British Museum (BM reference `W_K-19276`, CDLI `P273235`).
