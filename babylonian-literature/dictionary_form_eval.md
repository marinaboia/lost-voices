# Dictionary-form conversion — model comparison

**Script:** `lemma_eval.py`
**Results:** `results/lemma_eval/` (`sample.json`, `raw_<setup>.jsonl`, `report.json`)
**Date:** 2026-10-05

## Why

Sign n-gram matching (`ngram_matcher.py`) misses a match when two copies of a
line use *different signs* for the same words: a logogram vs a syllabic
spelling (`LU₂` vs `a-me-lu`, "man"), or different syllables
(`ma-l]i-ki` vs `ma-lik`). One fix is to convert each word to its **dictionary
form** (lemma), e.g. *amēlu*, *māliku*, and match on words instead of signs.
See `background_qa.md` for terms and `related_work.md` for context.

The fragments in our eBL export have no dictionary forms, so a model would
have to produce them. This test asks which model does it well enough, and at
what cost.

## Method

### Answer key

In eBL's edition of SB Gilgamesh, the editors tagged every word of every
manuscript line with its dictionary entry (`uniqueLemma`), e.g. `TE-ka` →
*lētu*, `li-im-haṣ` → *mahāṣu*. The data also marks which signs are broken or
damaged. The editors' tags are the answer key.

### Sample — 45 chunks, 209 lines, 659 scored words

- **30 hard chunks** from 15 manuscript **pairs**: one poem line in two ancient
  copies, each with ≥5 readable signs, sharing no run of signs (picked at random
  from the 175 such pairs). Each copy's line goes in a separate chunk, with up
  to 2 lines before and after from the same manuscript, so a chunk resembles a
  small fragment.
- **15 random chunks**: a random manuscript line with ≥3 legible words, ±2 lines.

Seed 0; saved in `results/lemma_eval/sample.json`. Half the sample is
deliberately hard, so it is not representative of typical lines.

### What the model saw

- **Instructions** (`SYSTEM_PROMPT` in the script): how to read eBL ATF, then
  "give each numbered word's dictionary headword, or an empty string if it can't
  be identified from what is written". Plus: don't use restorations in
  brackets, and don't supply words from memory of known texts.
- **Each request:** the script period and the chunk's lines, every word
  numbered as eBL writes it, e.g.
  `Line 1: 1:[x 2:x … 8:mu-ṭap₃-pi-l]a 9:ul 10:i-šu`.
- **Not given:** that the text is Gilgamesh, a translation, or other copies.
- **Output:** a fixed JSON format (structured outputs), one (word number,
  headword) entry per word.

Setups: Claude Sonnet 5.5 and Claude Opus 5.5, each at effort `low` and
`medium` (adaptive thinking on, the default). One standard API call per chunk;
not the Batch API.

### Scoring

- **Legible word:** at least one sign outside brackets. Legible words with an
  editor tag (659) are scored.
- **Correct:** the model's headword equals the editors' tag after lowercasing,
  dropping homonym numbers (*ul I* → *ul*), treating ḫ = h, and ignoring
  vowel-length marks (ā = a). š, ṣ, ṭ stay distinct. A blank answer counts as
  wrong.
- **Word groups:** *logogram* = any sign in the word is a logogram;
  *damaged* = any sign broken or marked `#`; *clean* = neither. A damaged
  logogram counts in both of the first two.
- **Restored words filled in:** words wholly inside a bracketed stretch (the
  editor's restoration, e.g. `LUGAL-MEŠ` in `[x LUGAL-MEŠ x]`), excluding bare
  `x` and `[...]`. Counts how often the model gave a headword anyway, as if the
  word were on the clay.
- **Pairs:** for each of the 15 pairs, do the model's headwords for the two
  copies share at least one word, after removing function words (*ana, ina, u,
  ša, ul* …)? The ceiling is the same check on the editors' tags.
- **Cost:** token counts from each API response × list price.

## Results

| Setup | All words | Logograms | Damaged | Clean syllabic | Left blank | Restored words filled in | Pairs connected | Test cost |
|---|---|---|---|---|---|---|---|---|
| Sonnet 5.5, low | 73% | 65% | 64% | 79% | 2.9% | 15 / 28 | 3 / 15 | $0.38 |
| Sonnet 5.5, medium | 74% | 68% | 63% | 79% | 2.1% | 13 / 28 | 3 / 15 | $0.38 |
| **Opus 5.5, low** | **83%** | **86%** | **72%** | **88%** | 3.0% | **2 / 28** | 3 / 15 | $0.77 |
| Opus 5.5, medium | 82% | 84% | 67% | 88% | 5.6% | 2 / 28 | 3 / 15 | $0.97 |

Group sizes: all 659, logograms 91, damaged 193, clean 393. Approximate
uncertainty: ±3 points on "all", ±9 on "logograms". Total cost of the
comparison: about $2.50.

### Columns

- **Setup:** model and effort (how much the model reasons before answering).
- **All words / Logograms / Damaged / Clean syllabic:** share of legible words
  matching the editors' tag, overall and by group.
- **Left blank:** share of legible words the model left empty (counted as
  wrong in the accuracy columns).
- **Restored words filled in:** lower is better. A model that treats
  restorations as evidence would create false matches.
- **Pairs connected:** see below.
- **Test cost:** the 45 calls at standard prices; the Batch API halves it.

## Findings

1. **Opus 5.5 at low effort is the best setup.** Medium effort costs more and
   didn't help; the low-vs-medium differences are within noise.
2. **Logograms separate the models** (86% vs 65–68%), and they are the main
   reason for this step. Examples of Sonnet errors:
   - `MU-ar₂` → *mû* ("water"); correct is *zakāru* ("to speak"), the formula
     from K.19276.
   - `E₂.GAR₈` → *bētu* ("house"); correct is *igartu* ("wall").
3. **Sonnet treats editorial restorations as evidence about half the time**
   (15 of 28); Opus almost never (2 of 28). In eBL ATF a bracket can open
   several words earlier, and Opus tracks where it opens and closes.
4. **The accuracies are underestimates.** Many "errors" are different
   spellings of the same headword between dictionaries: *amēlu* vs eBL's
   *awīlu*, *Enlil* vs *Ellil*, *ultu* vs *ištu*, *wašābu* vs *ašābu*,
   *tâmtu* vs *tiāmtu*. For matching, the poem and the fragments must use the
   same spellings, either by converting the poem's manuscripts with the same
   model or by mapping output onto eBL's dictionary entries.

### The 15 pairs

Only **4 of 15** pairs share a content word even using the editors' tags;
the models connect **3** of those 4. These 4 are real spelling differences:

```
I 293   ummī ina pī ellil māliki rabî limqutam-ma
  copy A:  [...] ma-l]i-ki GAL-i li-in-qu-tam-ma
  copy B:  [...] p]i-i {d}+en-lil₂ ma-lik lim-qut-am-ma
  shared:  māliku, maqātu

VIII 46 haṣṣinu ahīya tuklat idīya
  copy A:  ha-aṣ-ṣi-in a-hi-i[a tuk-l]a-tu i-di-ia
  copy B:  ha-ṣi-nu a-ha-a-a tu-ku-lat [...]
  shared:  haṣṣinnu, ahu, tukultu
```

The other two: XI 59 (`AB-hi[r` vs `im-ta-h]ir`, both *mahāru*) and X 226
(*nimru*, *ṣēru*).

The other **11** are copies that preserve *different parts* of the line, so
there is nothing to match:

```
VI 179  gilgāmeš ina ēkallīšu ištakan hidûta
  copy A:  [x x x x x x x x x x iš-ta]-kan hi-du-tu     ← only the end
  copy B:  {d#}GIŠ#-gim₂#-maš# i#-[na x x x x x ...]      ← only the beginning

XI 114  ilū iptalhū abūbam-ma
  copy A:  [x x x x x] a#-bu-ba-am-ma
  copy B:  DINGIR-MEŠ ip-la-hu [x x x x x]
```

So most of the cases the sign matcher misses are not spelling problems. No
word-level method can connect them; only the neighbouring lines can place
them.

## Cost of a full fragment run

Measured: about **130 output tokens per line** in the current format, which
returns an entry for every `x`. Estimates for the Batch API (half price), Opus
5.5 at low effort:

| | All 23,223 fragments (326K lines) | Pre-filtered (~3K fragments) |
|---|---|---|
| Current format | ~$470 | ~$60 |
| Return only identifiable words, skip unreadable lines, whole fragment per call with cached instructions | ~$150–200 | ~$20–30 |

These extrapolate from 209 lines; a small batch of real fragments would confirm
them.

## Caveats

- **The answer key has editorial choices built in.** For damaged words, the
  editors' tag can rely on other copies, so a model that correctly says
  "unidentifiable" is marked wrong.
- **One run per setup.** Model output varies between runs; no repeats.
- **The models know Gilgamesh.** Opus filling in only 2 of 28 restorations
  suggests it reads the signs rather than reciting, but accuracy on unknown
  texts may be lower.
- **Not representative of typical lines:** half the sample was chosen to be
  hard.

## Next steps

1. Convert the poem's manuscripts with Opus (low effort; ~$5–10 via Batch),
   so both sides use the same headword spellings.
2. Add word matching to `ngram_matcher.py` next to sign matching, and rerun the
   leave-one-manuscript-out benchmark to see whether it adds correct hits.
3. Only then run a pre-filtered set of fragments.
