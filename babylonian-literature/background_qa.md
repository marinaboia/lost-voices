# Background Q&A — tablets, signs and languages

Answers to background questions that came up while designing the fragment
matcher. For the methods themselves see `related_work.md` and
`ngram_matcher.py`.

---

## Languages

### What is Sumerian?

The language of southern Mesopotamia (modern southern Iraq). Cuneiform writing
was invented for it, around 3200 BCE. Sumerian is unrelated to any known
language (a *language isolate*). It died out as a spoken language around
2000–1800 BCE, but scribes kept copying and studying it for almost two thousand
years more, much as Latin was used in medieval Europe: for religion,
scholarship and prestige.

### What is Akkadian?

A Semitic language, related to Hebrew, Arabic and Aramaic, spoken in
Mesopotamia from about 2500 BCE. Its speakers borrowed cuneiform from the
Sumerians to write it. Its two main dialects are:

- **Babylonian**, in the south
- **Assyrian**, in the north

**Standard Babylonian** is the literary form of Babylonian used in the first
millennium BCE for literature and scholarship, including in Assyria. Akkadian
was written until about the 1st century CE.

### Are the Gilgamesh tablets in Akkadian?

Yes. The version we match against, the **Standard Babylonian** epic in 12
tablets, is in Akkadian. Some background:

- The oldest Gilgamesh stories are separate **Sumerian** poems about
  "Bilgames", from around 2100 BCE.
- An **Old Babylonian** Akkadian epic followed, around 1800 BCE.
- The 12-tablet Standard Babylonian version came later. Tradition credits it to
  a scholar called Sîn-lēqi-unninni. Most of our copies come from Assurbanipal's
  library at Nineveh (7th century BCE).
- **Tablet XII** is a fairly close Akkadian translation of the second half of
  the Sumerian poem *Bilgames and the Netherworld*.

Even Akkadian text contains Sumerian: many words are written with Sumerian
**logograms** (see below).

The eBL fragments are not all Akkadian. Some are Sumerian, and some are
**bilingual** (Sumerian with an Akkadian line-by-line translation). Several
appear in our match results, e.g. BM.39107 "Bilingual incantation" and
BM.32392 "Sumerian incantation".

---

## Signs and how they are read

### What does it mean that a sign is "read" a certain way?

Most cuneiform signs can stand for several different things, and which one the
scribe meant depends on context. A modern editor decides, and the
**transliteration** (e.g. `{d}GIŠ-gim₂-maš`) records that decision in Latin
letters. It is an interpretation, not a picture of the clay.

Example: the star sign 𒀭, called **AN** in sign lists, can be transliterated:

| Transliteration | Meaning |
|---|---|
| `an` | the syllable "an" |
| `il₃` | the syllable "il" |
| `DINGIR` | the word "god" |
| `{d}` | a silent marker: "the next word is a god's name", as in `{d}GIŠ-gim₂-maš` (Gilgamesh) |
| `AN-e` | "sky", as in `gu₄ AN-e`, the Bull of Heaven |

### What are the `ABZ…` codes in the `signs` field?

Sign numbers from a standard sign list (Borger's *Assyrisch-babylonische
Zeichenliste*, "ABZ"). They name the physical sign rather than one reading of
it, so every AN is `ABZ13` however it was read. Matching on these means two
editors reading the same sign differently doesn't hide a match.

### What do the small subscript numbers mean (`gim` vs `gim₂`, `u` vs `u₂`)?

They tell apart **different signs that sound the same**. `u`, `u₂` and `u₃`
are three different signs, all read "u". So `gim` and `gim₂` are different
signs. It is *not* the same sign read two ways; that's what the AN table above
shows.

### What are logograms?

Cuneiform can write a word in two ways:

- **Spelled out in syllables**: `a-me-lu` for *amēlu*, "man".
- **One sign for the whole word**: `LU₂` means "man" on its own, like "&" for
  "and" or "$" for "dollar". These are **logograms**. Most were originally
  Sumerian words kept as shorthand.

By convention logograms are transliterated in CAPITALS (`LU₂`, `EDIN`, `UGU`,
`DINGIR`) and syllables in lowercase. A scribe could choose either, so two
copies of the same line can share no signs at all.

### What is the "dictionary form" of a word?

Akkadian words change form: "man" is *amēlu* as a subject, *amēla* as an
object, *amēli* after "of" (like English *go / went / gone*). The **dictionary
form**, or **lemma**, is the headword you'd look up: *amēlu*.

**Normalized** (or dictionary-form) Akkadian is a line rewritten as plain words,
ignoring how they were spelled. These two copies of Gilgamesh VII 94:

```
ṣa-a-a-du hab-bi-lu a-me-lu      (Babylon copy)
[...] ha-bi-la LU₂               (Ḫuzirina copy)
```

are both *ṣayyādu habbilu amēlu*: different signs, same words.

Our poem files include this for every line (the `reconstruction` field) and
George's English translation. The eBL fragment export has neither.

---

## Damage and how it is written

### How are broken signs written in a transliteration?

eBL uses the ATF conventions. From K.19276:

```
2'. [... {d}GIŠ-gi]m₂-maš x [x x]
4'. [...] MAŠ?# U₂# AŠ? [x x]
```

| Symbol | Meaning |
|---|---|
| `[ ]` | The clay is missing; anything inside is the editor's **restoration**, not visible. In `[... {d}GIŠ-gi]m₂-maš` only `m₂-maš` is on the clay. |
| `[...]` | Missing, length unknown. |
| `[x x]` | Missing, roughly that many signs' worth of space. |
| `x` (outside brackets) | A sign is there but can't be identified. |
| `#` | Damaged but identifiable. |
| `?` | Uncertain reading. |
| `!` | Scribal error, corrected by the editor: `dan!(E)` means "written E, read *dan*". |
| `1'.`, `2'.` | A primed line number: the count starts at the first surviving line, not the top of the original tablet. |

In the `signs` field, anything broken or unidentifiable becomes `X`.
Restorations aren't included, since they aren't on the clay.

### Why do fragments have two sides?

A tablet is written like a page: the front (**obverse**), then turned over, the
back (**reverse**). Big literary tablets also had 2–3 **columns** per side. A
~300-line Gilgamesh tablet might be laid out like this:

```
obverse:  col i (lines 1–50)   col ii (51–100)   col iii (101–150)
reverse:  col iv (151–200)     col v (201–250)   col vi (251–300)
```

A fragment broken out of the middle keeps clay from both faces, so it has text
on both sides, from parts of the poem far apart. Both sides should place in the
same tablet, about the right distance apart for its layout.

---

## Manuscripts, the composite text and fragments

### What is the difference between "the poem", a manuscript and a fragment?

- A **manuscript** (or **witness**) is one ancient copy of a tablet, usually
  itself broken. Each has a **siglum** (label), e.g. Nineveh copy 1a of
  Tablet XI.
- The **composite text** ("the poem") is the modern edition built by lining up
  all the manuscripts line by line (here, George's edition as revised in eBL).
  A composite line is complete if *any* copy preserves it; it's a **gap** if
  every copy is broken there.
- A **fragment** is a piece of clay in a museum. An *unplaced* fragment is one
  nobody has assigned to a text yet.

### What is a "join"?

Two or more fragments recognised as pieces of the *same* original tablet and
fitted together, physically or on paper. Museum notes write it as `K.8594 +
K.21502`. A fragment that "joins" a known Gilgamesh manuscript is already
identified, so a match to it is a sanity check rather than a discovery.

### Where do most Gilgamesh copies come from?

**Kuyunjik**, the mound at ancient Nineveh, where Assurbanipal's library
(7th century BCE) was excavated. Museum numbers starting with `K.` are from
there. This is why the semantic filter weights Kuyunjik provenance.

---

## Why two copies of a line may not match

### Spelling differences

The same words written with different signs. From the Gilgamesh manuscripts:

**Tablet VII 94**, *habbilu amēlu* ("a criminal, a man"):
```
Babylon copy:   ṣa-a-a-du  hab-bi-lu  a-me-lu
Ḫuzirina copy:  [...] ha-bi-l]a  LU₂
```
`hab-bi-lu` vs `ha-bi-la` use different signs; `a-me-lu` (syllables) vs
`LU₂` (logogram).

**Tablet I 269**, *tahabbub elīšu* ("you'll caress him"):
```
Babylon copy:   ta-ram-šu-ma GIM DAM  ta-hab-bu-bu  UGU-šu₂
Nineveh copy:   [...]               e-li-šu₂  tah-b[u-ub]
```
`UGU` (logogram) vs `e-li` (syllables) for "upon"; also a different word order.

Sometimes the scribes wrote **different words** (a textual variant), e.g.
Tablet V 76: `lu-ba-ra-tu-ma` in one copy, `lu-u₂ ma-ku-ma` in another.

### Different parts survive

**Tablet VIII 91**, *altabbiš-ma mašak labbim-ma arappud ṣēra* ("I dressed in
a lion's skin and roamed the wild"):
```
Babylon copy:   [x x x x x x x x x x x a-rap]-pu-ud EDIN    ← only the end
Nineveh copy:   al-tab-biš-ma KUŠ l[a-ab-bi-im-ma x x x x]   ← only the beginning
```

Nothing is shared, so no comparison method can connect them directly. Such a
line can only be placed through its neighbours or through what it means.

---

## Translation

### Would translating fragments into English work?

It isn't a silly idea: English has mature embedding models, and we already
have George's English translation of every poem line. But a translation is an
interpretation layered on an interpretation, so it has real limits:

- **Many fragments barely have content to translate.** A line like
  `[...] x x ka-a-ar ina BARA₂# ri-[x x]` is a few word pieces. Any fluent
  "translation" of it is mostly invention.
- **Models fill gaps confidently.** Asked to translate broken text, an LLM
  tends to restore what it expects. That would push fragments toward
  familiar-sounding Gilgamesh passages: exactly the false positives we want to
  avoid.
- **Logograms are ambiguous.** One sign can stand for several words, and
  without context the translator has to guess.
- **English loses detail.** Different Akkadian words can share one English
  translation, and a paraphrase can match on theme ("the gods", "the king")
  rather than on the actual words.
- **Not everything is Akkadian.** Sumerian and bilingual fragments need
  different handling.

Safer variants:

- **Word-by-word glossing.** Ask for each surviving word's dictionary form and
  meaning, with an explicit "unreadable" marker, not a fluent sentence.
- **Match in dictionary-form Akkadian, not English.** Normalize the fragment
  (`ha-bi-la LU₂` → *habbilu amēlu*) and compare words against the poem's
  `reconstruction`. This handles spelling and logograms without a paraphrase
  step.
- **Keep sign matching for exact cases**, and use translation mainly for the
  meaning-based "could this fill this gap?" check, where the gist is what
  matters.
