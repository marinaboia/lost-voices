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

**K.16980** scored 0.35 — below the default threshold — yet produced the clearest placement result of the three. Short fragments are systematically underscored by the semantic filter even when their few preserved signs are highly diagnostic. See placement study below.

## Pilot study — summary of contributions

We ran `place_fragment.py` on five fragments (the three unplaced candidates from the top results, plus the next two by score). Results:

| Fragment | Score | Prior status | Placement result | Contribution |
|---|---|---|---|---|
| **K.19276** | 0.60 | George's ZZ — suspected Gilgamesh, no hypothesis | Proposed: **Tablet V 115–116** (Humbaba's taunt) | New specific hypothesis with testable prediction; first proposed Kuyunjik witness to this passage |
| **K.21863** | 0.60 | "Gilg VII?" note, unanalysed | No fit in preserved portions of Tablets VI or VII | Ruled out all known feminine-address passages; likely in lost stretch of Tablet VII (ll. 2–35) |
| **K.16980** | 0.35 | "cf. Gilg I 222-223" note, unplaced | Confirmed: **Tablet I 220–221** (Enkidu's boast) | Validates and sharpens an existing informal note; adds `al-du` spelling variant; third Kuyunjik witness |
| **BM.54325** | 0.30 | Scored as possible Gilgamesh XI/XII | Not SB Gilgamesh at all | Sumerian GEN manuscript (prologue ll. 4–34); wrong language; provenance label also questionable |
| **K.23044** | 0.30 | Possible Tablet XI or Humbaba passage | Too little text to place | Single word *abūbi* + one illegible sign; best candidate is Tablet XI:14 but unconfirmable without collation |

K.19276 is the most actionable result: a specific, falsifiable placement hypothesis for a fragment George catalogued as unplaceable for over twenty years. Below score ~0.30 the fragments either belong to other compositions or preserve too little text to place. Detailed studies for each fragment follow below.

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

---

## K.21863 — placement study

**Script:** `place_fragment.py`  
**Tablets checked:** VI, VII  
**Full output:** `results/placement_K_21863.json`

### Fragment

```
1'. [... u]l?/ba]l?-lu
2'. [...-b]e-ki
3'. [...] x-ši?#-ki
4'. [...]-a#/e#/dan#-nu
5'. [...-i]k?-ki
6'. [...] x
```

### Diagnostic feature

Three of five lines end in `-ki` — the 2nd person feminine singular suffix in Akkadian. The fragment must come from a speech addressed to a woman or a grammatically feminine noun (e.g. *daltu* "door", *qištu* "forest"). The specific sequence across five lines is `-lu / -be-ki / -ši-ki / -nu / -ik-ki`.

### Result: no placement found in either tablet

**Tablet VI** — checked all three feminine-address passages: Gilgamesh's rejection of Ishtar (ll. 24–79), Anu's reply (ll. 89–91), and Enkidu's taunt (ll. 156–157). All are well-preserved at line-end. None produce the required sequence. The `-ki` endings in Tablet VI are isolated rather than clustered across consecutive lines.

**Tablet VII** — checked Enkidu's address to the cedar door (ll. 39–63), the curse of Šamhat (ll. 102–131), and the blessing of Šamhat (ll. 151–161). The most tempting alignment (line 4′ = VII 115 ending *-nu*, line 5′ = VII 116 ending *-ki*) fails because VII 116 ends in *-bu-ki*, not *-ik-ki*, and the surrounding lines also do not match.

### Where it might sit

The fragment could only fit in a wholly-lost stretch of Tablet VII — most plausibly **lines 2–35**, which precede the preserved door speech and are almost entirely unattested. The dense cluster of `-ki` endings is consistent with the character of Enkidu's door address, but there is nothing positive to confirm it, only the absence of contradiction.

### Assessment

Weaker result than K.19276. K.19276 produced a specific line match with a testable prediction; K.21863 points only toward a gap where confirmation is currently impossible. The fragment is almost certainly Gilgamesh (eBL genre tag, feminine-suffix pattern consistent with the epic's second half), but its precise location cannot be determined from surviving text alone.

---

## K.16980 — placement study

**Script:** `place_fragment.py`  
**Tablets checked:** I, VII, VIII  
**Full output:** `results/placement_K_16980.json`

### Fragment

```
1. [... i?-s]in-nu ši-ma-t[u₂? ...]
2. [...] x EDIN al-du [...]
   #note: ša ina ṣēri aldu = Enkidu? [AG]
```

Andrew George's own note in the eBL record already flagged line 2 as a possible Enkidu epithet. The eBL record carried a "cf. Gilg I 222-223" note but no formal placement.

### Result: Tablet I, lines 220–221

All three tablet analyses converged independently on the same passage: **Tablet I lines 220–221**, Enkidu's boast to Šamhat before setting out for Uruk.

The diagnostic element is line 2: `EDIN al-du` = *ina ṣēri aldu* = "born in the wild" — Enkidu's defining epithet, appearing here in his self-description as he prepares to challenge Gilgamesh. Line 1's *šīmātu* ("destinies") matches the immediately preceding line, where Enkidu declares he will go to Uruk and "change the destinies" of the city.

| Fragment line | Proposed = Tablet I line | Alignment |
|---|---|---|
| 1 | I 220 | *šīmātu* matches NinNA1a v 22 and NinNA3 v 2; both mark the MA as doubtful — a third witness with a clean reading would be useful |
| 2 | I 221 | `EDIN al-du` matches *[ša i-n]a ṣēri iʾʾaldu* in NinNA1a v 23 directly; `al-du` is a spelling variant of `iʾ-al-du`, the same alternation seen at Tablet I line 47 |

The scholar's note "cf. Gilg I 222-223" was essentially correct — the two-line offset is probably from an older edition.

### Textual contribution

K.16980 would be a third Kuyunjik witness to Tablet I lines 220–221. The spelling `al-du` (vs `iʾ-al-du` in both existing copies) is a minor variant worth noting in a future edition. The passage is not lost — it survives in NinNA1a and NinNA3 — so this fragment adds a witness rather than new text.

One unresolved discrepancy: the sign before *šīmātu* on line 1 is tentatively read as `[i?-s]in-nu` ("festival") in the eBL, but NinNA1a has `-um-ma` in that position. Physical collation would resolve whether this is a genuine variant, a misread, or a different line layout.

### What this reveals about the semantic filter

K.16980 scored **0.35** in the semantic filter — below the default 0.35 threshold and the lowest of the three unplaced fragments. Yet it produced the clearest placement result: all three checks converged without ambiguity.

The reason is that the semantic filter and placement analysis measure different things:

- The **semantic filter** asks whether the fragment *looks like Gilgamesh* from its broken text alone. K.16980 has only two damaged lines. Even `EDIN al-du` ("born in the steppe") is plain enough to appear in other literature; without more context the model hedged.
- The **placement analysis** asks whether the fragment *matches a specific passage* when compared line by line against the canonical text. Here the answer was unambiguous — *šīmātu* on one line immediately followed by *ina ṣēri aldu* on the next is highly specific.

**Implication:** short, broken fragments will systematically score lower in the semantic filter even if their few preserved signs are actually quite diagnostic when compared directly against the gaps. The 0.35 cutoff likely filters out some genuinely placeable fragments purely because they are small. A better approach for very short fragments (≤ 3 lines) might be to skip the semantic filter and run placement directly.

---

## BM.54325 — placement study

**Script:** `place_fragment.py`  
**Tablets checked:** XI, XII  
**Full output:** `results/placement_BM_54325.json`

### Fragment

18 lines of Sumerian (`%sux`) on the obverse and 4 on the reverse, ending with a ruling and blank surface. Every line carries an editorial note identifying it as *Gilgameš, Enkidu and the Netherworld* (GEN):

- Obverse: GEN lines 4–22 (cosmogonic prologue — separation of heaven and earth, Ereškigal given the netherworld, Enki's voyage)
- Reverse: GEN lines 31–34 (the *ḫuluppu* tree rescued from the Euphrates, carried to Uruk)

### Result: not Standard Babylonian Gilgamesh

The fragment is a Sumerian manuscript, not Akkadian. Tablet XI is entirely Akkadian with no bilingual sections; Tablet XII is an Akkadian translation of only the *second half* of GEN (from line 172 onward — the *pukku* and *mikkû* falling into the netherworld). The prologue preserved here (GEN 4–34) was never translated into the SB series.

The tablet ending mid-text (GEN 34, with the rest blank) suggests a **school extract**, not a section of a full multi-column manuscript.

The model also flagged a provenance question: "BM.54xxx" numbers typically belong to the 1882 Sippar/Babylon acquisitions (Rassam collection), not the Kuyunjik "K." or "Sm." series. The eBL provenance label should be verified against the museum register.

### Assessment

Wrong composition for our purposes. BM.54325 should be catalogued under the Sumerian Gilgamesh corpus (GEN), not the SB epic. The semantic filter scored it 0.30 because it contains genuine Gilgamesh vocabulary, but the language mismatch rules it out entirely.

---

## K.23044 — placement study

**Script:** `place_fragment.py`  
**Tablets checked:** II, V, XI  
**Full output:** `results/placement_K_23044.json`

### Fragment

```
1'. [...] a#-bu-bi x [...]
$ rest of side broken
```

A single damaged line. The only secure reading is **a-bu-bi** — the genitive of *abūbu*, "Deluge" — followed by one unidentified sign.

### Result: possible Tablet XI:14, unconfirmable

*abūbu* is one of the most common words in the epic (Tablets I, II, V, XI, plus Atrahasis and Erra), so one occurrence proves very little. However, the genitive form *abūbi* (rather than the nominative *abūbu*) narrows the field. Across all three tablets checked, the model found one candidate where the genitive, the following sign, and the absence of a Kuyunjik witness all align:

**Tablet XI, line 14:** `[ana šakān] a-bu-bi u[b-la libbašunu ilū rabûtu]`  
*"The great gods resolved in their hearts to send the Deluge."*

- NinNA2b already has `a-bu-b[i]` at this line; K.23044 is not that manuscript.
- NinNA1 has a break covering exactly *ana šakān abūbi ubla* — a join is physically conceivable.
- The unidentified trace after *bi* could be the beginning of *ub* (*ubla*).

A secondary candidate: **Tablet V, line 135** (`[šapār] a-bu-bi iš-[tuhhu lapātu]` — "to send the Deluge is to crack the whip"), where no Ninevite witness survives at all.

### Assessment

Too little text to reach a conclusion. One word plus one illegible sign cannot distinguish between multiple plausible tablets, let alone rule out other compositions. Collation of the trace after *bi* and comparison with NinNA1 column i would be the minimum needed to test the Tablet XI:14 hypothesis.
