# Related work — fragment identification and placement

Literature and code survey done before building a sign-level matcher, to see
what already exists. Checked October 2026.

## The idea we started from

From discussion with Juro: instead of asking a model "does this fragment look
like Gilgamesh?" (`semantic_filter.py`), match short phrases from each fragment
against the poem to find candidate positions, then ask a model whether the
fragment fits at that specific position (fragment ATF + image + surrounding
lines of the poem).

Multi-line fragments are the interesting case. If line 2 of a fragment matches
poem line *n*, line 1 should sit at *n − 1*. If *n − 1* is broken in every known
manuscript, the fragment may supply new text for it.

This is motivated by K.16980 (see `findings.md`). It scored at the semantic
filter's cutoff but gave the clearest placement, because its two lines were
very specific when compared directly against the text.

## What already exists

### eBL n-gram matcher

- Code: <https://github.com/ElectronicBabylonianLiterature/ngram-matcher>
- Paper: Simonjetz et al., *Reconstruction of Cuneiform Literary Texts as Text
  Matching*, LREC-COLING 2024 — <https://aclanthology.org/2024.lrec-main.1197>

Built by the eBL team (LMU Munich), the source of our data. It works on the
`signs` field (sign-list names such as `ABZ13`, not readings), so differences in
how editors *read* a sign don't prevent a match.

How it works (verified in the code):

- Each document (fragment, chapter, or single manuscript) is flattened into one
  sign sequence; line breaks become a `#` token (`document_model.py`).
  Sequences containing a broken sign (`X`) are dropped.
- It extracts the set of sign n-grams, n = 1–3 by default.
- Documents are compared by set overlap: an overlap coefficient, optionally
  length-weighted (Σ len²) or TF-IDF weighted (`metrics.py`, `base_corpus.py`).
- The output is **one score per text** (e.g. `/L/1/4/SB/XI 0.27`).
  `include_overlaps=True` adds the set of shared n-grams, **without positions**.
  The tool says *which* text, not *where* in it.
- Intended use is semi-automatic: it narrows tens of thousands of candidates to
  a few hundred for an expert to review. It can also use OCR output.

Reported results: since 2018 the team has matched over 1,500 tablet pieces,
including about 20 Gilgamesh fragments that add to more than 100 lines of the
epic. In November 2022 it found a piece of the latest known Gilgamesh
manuscript (130 BCE).

- <https://paleojudaica.blogspot.com/2024/08/ai-is-finding-more-gilgamesh-epic.html>
- <https://phys.org/news/2023-02-ai-texts-thousands-years-readable.html>

### eBL sign search (website / API)

- `ebl-api/ebl/corpus/infrastructure/manuscript_sign_matcher.py`,
  `corpus_sign_matcher.py`, `fragmentarium/infrastructure/fragment_sign_matcher.py`

Given a sign sequence, returns the exact manuscript lines that contain it. So
eBL *can* locate lines, but as an interactive search. An expert chooses which
sequence to look up, then checks by eye whether the fragment's other lines fit
around the hit.

### Restoring missing signs with language models

- Fetaya, Lifshitz, Aaron, Gordin, *Restoration of fragmentary Babylonian texts
  using recurrent neural networks*, PNAS 117(37), 2020. An RNN predicting
  missing tokens.
- Lazar, Saret, Yehudai, Horowitz, Wasserman, Stanovsky, *Filling the Gaps in
  Ancient Akkadian Texts: A Masked Language Modelling Approach*, EMNLP 2021 —
  <https://aclanthology.org/2021.emnlp-main.384.pdf>
  - **Model:** BERT-style masked language model. Best results come from
    multilingual BERT (M-BERT) fine-tuned on Akkadian.
  - **Data:** Oracc transliterations, about 1M tokens. Missing signs are `x`.
  - **Result:** 89.5% hit@5 on predicting masked tokens. Multilingual
    pretraining mattered more than the Akkadian data: zero-shot M-BERT beat a
    monolingual Akkadian model by about 10%. In a user study, experts found at
    least one of the top-3 predictions useful in most cases.
  - **Availability:** code and trained models at
    <https://github.com/SLAB-NLP/Akk>.
  - Described as the first Akkadian language model.

These predict *likely* signs in gaps from language patterns. They don't find a
physical witness that shows what was actually written.

### Akkadian translation models

None of these is built for matching passages, but all are trained on Akkadian
transliteration, which no general-purpose model is.

**AKK-60m** — <https://huggingface.co/Thalesian/AKK-60m> (Drake 2025)
- **Architecture:** fine-tuned T5-small, an encoder-decoder (6 + 6 layers,
  d_model 512, ~60M parameters). Apache-2.0.
- **Tasks:** an instruction model ("Translate Akkadian simple transliteration
  to English: …"). It translates Akkadian ↔ English from either cuneiform
  Unicode or transliteration, transliterates cuneiform, and fills missing signs.
- **Data:** Akkademia (Gutherz et al., PNAS Nexus 2023) plus CDLI Akkadian:
  about 390K transliterated lines for pretraining and 127K translated lines.
- **Damage handling:** trained with missing signs marked `*`, and with random
  wrong signs to simulate misreadings.
- **Reported scores:** BLEU 70.9 transliteration → English; 93.9 cuneiform →
  transliteration.
- **Limitations:** 64-token context, so short lines only. The training data is
  mostly royal inscriptions, letters and administrative texts, not Standard
  Babylonian literature.

**praeclarum/cuneiform** — <https://huggingface.co/praeclarum/cuneiform>
- **Architecture:** fine-tuned T5-base, an encoder-decoder (12 + 12 layers,
  d_model 768, ~220M parameters). MIT.
- **Tasks:** Akkadian and Sumerian → English, with prompts like
  "translate Akkadian to English: …". Input is CDLI-style ATF.
- **Limitations:** its vocabulary lacks ā, ḫ, ī, š, ṣ, ū, so these are
  flattened (š → "sh"), losing distinctions between Akkadian sounds. No
  reported metrics.

**TabletCraft / cuneiscribe** — <https://arxiv.org/html/2608.02609> (C3NLP @ ACL 2026)
- **Architecture:** fine-tuned ByT5-base (581M parameters), an encoder-decoder
  that reads raw bytes, so diacritics and logograms need no special vocabulary.
- **Data:** 116K bidirectional sentence pairs, mainly Akkademia (50K).
- **Results:** Akkadian → English BLEU 49.1 / chrF++ 63.1 on Neo-Assyrian
  validation data; English → Akkadian BLEU 48.5.
- **Extras:** a transliteration → cuneiform Unicode converter (14,240
  mappings, 95.3% coverage).
- **Availability:** `pip install cuneiscribe`, CC BY 4.0.

### Could these models give us embeddings?

All three translation models are encoder-decoders. Their **encoder output**
(one vector per input token, averaged into one vector per line) could serve as
a line embedding. There is precedent: LASER (Artetxe & Schwenk, TACL 2019)
builds multilingual sentence embeddings from a translation model's encoder,
and Sentence-T5 (Ni et al., 2021) showed that averaged T5 encoder outputs
already work reasonably for similarity, and much better after contrastive
fine-tuning.
Lazar et al.'s model is encoder-only (BERT), so it could be averaged the same
way.

Why it might help: a translation encoder has to map `a-me-lu` and `LU₂` to
the same meaning ("man") to translate them correctly. So spelling variants and
logograms could land close together, the case sign n-grams miss.

Reasons for caution:
- **Not trained for similarity.** Without fine-tuning on matching pairs,
  averaged encoder vectors often pick up length and genre rather than content.
- **Domain mismatch.** The training data is mostly royal inscriptions, letters
  and administrative texts, not Standard Babylonian literature.
- **Format mismatch.** eBL ATF (`[...]`, `#`, `{d}`, subscripts) differs from
  each model's input format, so fragments need converting first. AKK-60m
  expects `*` for missing signs; praeclarum drops diacritics.
- **Short context.** AKK-60m's 64-token limit means one line at a time.

This can be tested cheaply with the existing benchmark: embed every manuscript
line with each encoder, rerun leave-one-manuscript-out, and check especially
the 175 manuscript-line pairs that share no sign n-grams (see
`background_qa.md` for examples). If it helps there, the next step is
fine-tuning one encoder on matching pairs, which our manuscripts supply for
free: different copies of the same poem line.

### Reading tablets from photos

- <https://github.com/ElectronicBabylonianLiterature/cuneiform-ocr>
- *Automated sign detection across the Electronic Babylonian Library*,
  arXiv 2606.22608.

Sign detection from tablet photos; the n-gram matcher can already use its
output.

## Where our approach differs

| Step | eBL today | Ours |
|---|---|---|
| Which text might this be? | automated (n-gram matcher) | same idea |
| Where in the text? | expert runs sign searches by hand | automated for every fragment |
| Do the fragment's other lines fit around that spot? | expert, by eye | automated: consecutive fragment lines must land on consecutive poem lines (± small offset) |
| Same text, different spelling? | expert knowledge | LLM verification step |

Honest assessment:

- Automating line placement is a **modest extension** of what eBL has, not a
  new idea. Their data and search already support it.
- The more distinctive part is the **LLM check for spelling variants**. Any sign
  matching misses a match when the scribe used *different signs* for the same
  text, e.g. `MU-ar₂` vs `MU-ra` (K.19276), `al-du` vs `iʾ-al-du` (K.16980), or
  a logogram vs a syllabic spelling (`EDIN` vs `ṣe-e-ri`).
- **Selection effect:** eBL has almost certainly already run its matcher over
  the same fragments. The ones still unplaced are disproportionately those
  sign matching couldn't resolve: very short fragments, unusual spellings,
  formulaic lines. K.19276 is an example: catalogued by George, revised five
  times by eBL, still unplaced.

## Implications for our matcher

- **Keep line positions.** Index n-grams per manuscript line, not per document,
  so a hit points to a specific line of the poem.
- **Score multi-line consistency.** Reward fragment lines that land on
  consecutive poem lines, and downweight formulaic n-grams (e.g. "speaks to
  Gilgamesh") with IDF.
- **Poem sign names are available from eBL.** Our tablet JSONs hold only
  transliterations, but the API serves per-manuscript sign lines:
  `https://www.ebl.lmu.de/api/texts/L/1/4/chapters/Standard%20Babylonian/<TABLET>/signs`
  (the source `ngram-matcher` uses). These still need mapping back to poem line
  numbers through each line's manuscript entries.
- **Benchmark two ways:**
  1. Leave one manuscript out of the index, cut it into 1–3 line pseudo-fragments,
     and check whether the right line comes back in the top k.
  2. Check whether we can rank fragments that eBL's matcher ranks poorly.
- **Include other SB literature** (e.g. Atrahasis) as decoys. K.20164 turned out
  to be Atrahasis.
- Possible contact: the eBL team, who could physically check any placement we
  propose.
