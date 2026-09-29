# lost-voices

AI-assisted research into ancient languages, lost texts, and deep etymology.

A collaboration between Marina Boia and Juro Gottweis.

---

## The Pick: Hunting Lost Lines of Gilgamesh

**Use an agent to find missing pieces of Babylonian literature, including lost lines of Gilgamesh.**

### Why this one

- **The data is open.** The Munich eBL team has published tens of thousands of transliterated tablets — many never published before — as an open dataset. Compiling it already turned up 1,250 joins (fragments that belong together). The platform code is open source, including a tool that aligns every fragment against the edited Corpus. ([JOHD](https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.148) · [GitHub](https://github.com/ElectronicBabylonianLiterature/ebl-api))
- **There's lots left to find.** Many fragments are still waiting to be joined. About 60% come from Assurbanipal's library at Nineveh — the largest collection of texts in antiquity. ([eBL](https://www.ebl.lmu.de/about))
- **Room to beat the current method.** Their matcher looks for overlapping n-grams (short identical runs of signs). A stronger agent could do fuzzy matching: spelling variants, broken signs, paraphrased parallel versions, and meaning-level similarity rather than exact wording. ([Level Up Coding](https://levelup.gitconnected.com/the-electronic-babylonian-library-ebl-gilgamesh-project-f883e0ff068f?gi=f98d4e6c6ef1))
- **Results are checkable.** A proposed join is a concrete claim: fragment X continues fragment Y. A curator can test it against the physical tablets in the British Museum. No endless debate — just yes or no.

### The pipeline

1. Download the eBL dataset plus the CDLI ATF dump.
2. Calibrate on known joins — hide the 1,250 known joins and see whether the agent rediscovers them. This gives a real precision number before claiming anything new.
3. Run across all unassigned fragments; propose joins and missing-line restorations with confidence scores.
4. Send top 20–50 candidates to the eBL team (Enrique Jiménez at LMU Munich) to check against the tablets.

**The headline if it works:** new lines of Gilgamesh, the Epic of Creation, or lost hymns — found by AI in museum drawers after 170 years.

### Two alternates

- **The first economic dataset in history.** CDLI's bulk dump contains thousands of Ur III administrative tablets (c. 2100 BCE). An agent could extract every commodity, worker, ration and transfer, then build a supply-chain model of the world's first bureaucratic state. There are already Sumerian machine-translation pipelines to build on. One caveat: CDLI's bulk export appears to have been frozen since August 2022, but it's still huge. ([CDLI tools](https://cdli-gh.github.io/guides/guide_tools_list.html) · [Glintstone data sources](https://github.com/wittkensis/glintstone/wiki/Data-Model-Data-Sources/1c08b5efbe6af3852061531ff113e324375612b3))
- **Linear A as a lottery ticket.** Put every candidate language (Luwian, Hurrian, Semitic, Etruscan-like) through an exhaustive, statistically scored comparison on the SigLA corpus. It will most likely end in "nothing fits well" — which is still publishable. But there is a small chance of the century's biggest decipherment.

### Sources

- [Transliterated Cuneiform Tablets of the eBL Platform (JOHD)](https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.148)
- [eBL API (GitHub)](https://github.com/ElectronicBabylonianLiterature/ebl-api)
- [About: eBL](https://www.ebl.lmu.de/about)
- [LMU Munich harnesses AI (Nature)](https://www.nature.com/articles/d42473-020-00366-8)
- [eBL Gilgamesh project (Level Up Coding)](https://levelup.gitconnected.com/the-electronic-babylonian-library-ebl-gilgamesh-project-f883e0ff068f?gi=f98d4e6c6ef1)
- [CDLI tools and data list](https://cdli-gh.github.io/guides/guide_tools_list.html)
- [Glintstone data sources wiki](https://github.com/wittkensis/glintstone/wiki/Data-Model-Data-Sources/1c08b5efbe6af3852061531ff113e324375612b3)

---

## Wider Idea Space

### Undeciphered scripts

- **Linear A** — Minoan script of Crete (c. 1800–1450 BCE), ~1,400 short inscriptions. Roughly pronounceable via Linear B, but the language is unknown. *Sources:* SigLA database, GORILA corpus, John Younger's Linear A texts site, DAMOS.
- **Cretan Hieroglyphic and the Phaistos Disc** — older Cretan scripts, probably the same language as Linear A. A Linear A breakthrough would cascade to them. *Sources:* CHIC corpus (Olivier & Godart).
- **Cypro-Minoan** — Cyprus's Bronze Age script, a descendant of Linear A, also used at Ugarit. *Sources:* Ferrara's corpus editions and Valério's sign lists.
- **Indus script** — Harappan civilisation, ~4,000 very short seals, language totally unknown. An agent could test the "is it even writing?" question rigorously. *Sources:* ICIT corpus (Wells), Mahadevan's concordance.
- **Rongorongo** — Easter Island glyphs on ~26 wooden objects; if genuine writing, one of only a handful of independent writing inventions. *Sources:* Barthel's corpus, Kohau project transcriptions.
- **Proto-Elamite** — Iran's earliest script (c. 3100 BCE), ~1,600 tablets, mostly accounts, only partially understood. *Sources:* CDLI, Jacob Dahl's Oxford work.
- **Linear Elamite** — partial decipherment claimed in 2022, remains contested; an agent could independently validate or refute it. *Sources:* Desset et al. published sign lists and inscriptions.
- **Khitan large and small scripts** — Liao dynasty (10th–12th c. China); long texts, bilingual pieces, only partly read — among the most crackable. *Sources:* Kane's *The Kitan Language and Script*, published epitaph corpora.
- **Byblos syllabary** — ~10 Bronze Age inscriptions from Lebanon, possibly early Semitic. *Sources:* Dunand editions.
- **Voynich manuscript** — is it a cipher, constructed language, real language, or hoax? *Sources:* EVA transcriptions, Beinecke scans.

### Recovering lost texts

- **Herculaneum scrolls** — whole Epicurean library carbonised by Vesuvius. Imaging now works; bottleneck is filling gaps in damaged Greek. Could yield lost Epicurus, Philodemus, or Latin literature. *Sources:* Vesuvius Challenge open data (scrollprize.org), Herculaneum papyri editions.
- **Palimpsests** — erased manuscripts overwritten later; hidden texts include Archimedes, lost Galen, Caucasian Albanian. *Sources:* Archimedes Palimpsest open data, Sinai Palimpsests Project.
- **Lost works from quotations** — many authors survive only as scattered quotes (Presocratics, lost Aristotle, Epicurus, historians). An agent could harvest every citation across the whole corpus. *Sources:* TLG, Diels–Kranz, Brill's New Jacoby, Photius's *Bibliotheca*.
- **Reconstructing Q** — the hypothetical sayings source behind Matthew and Luke; proper probabilistic reconstruction never done. *Sources:* International Q Project, SBLGNT, synoptic alignments.
- **Oxyrhynchus papyri** — hundreds of thousands of fragments from an Egyptian rubbish dump, only partly published; include lost Sappho, Menander, and gospels. *Sources:* papyri.info (DDbDP), Trismegistos, Oxyrhynchus Online images.

### Scale problems

- **The cuneiform backlog** — hundreds of thousands of Sumerian and Akkadian tablets remain untranslated, covering law, medicine, letters, and literature. The biggest untapped written archive on Earth. *Sources:* CDLI, ORACC, eBL, BDTNS, Archibab.
- **Fragment joining** — matching broken pieces across museums. eBL has already found joins in Gilgamesh this way. *Sources:* eBL Fragmentarium, Cairo Geniza (Friedberg Genizah Project), Dead Sea Scrolls (Leon Levy Digital Library, Scripta Qumranica Electronica).
- **Demotic and Coptic backlog** — huge numbers of late Egyptian documents remain unedited. *Sources:* Thesaurus Linguae Aegyptiae, Coptic Scriptorium, Trismegistos.
- **Oracle bones** — China's earliest writing (Shang dynasty), ~150,000 fragments, many unjoined, many characters unread. *Sources:* Yinqi Wenyuan database (Anyang), Chinese Text Project.

### Layers, insertions and authorship

- **New Testament interpolations** — Johannine Comma, ending of Mark, pericope adulterae; serve as ground truth for calibration. *Sources:* INTF New Testament Virtual Manuscript Room, SBLGNT.
- **The Ignatius recensions** — the long recension is a known 4th-century expansion; perfect benchmark for insertion detection. *Sources:* Lightfoot's edition (First1KGreek, TLG).
- **Pentateuch sources (J, E, P, D)** — can an agent independently recover or refute the documentary hypothesis? *Sources:* ETCBC BHSA (open annotated Hebrew Bible).
- **Homeric layers** — oral-formulaic strata, late additions (Iliad Book 10), same author as Odyssey? *Sources:* Chicago Homer, scholia, Perseus.
- **Mahabharata growth** — expanded over centuries from a core epic; critical edition records the variants. *Sources:* BORI Pune critical edition, GRETIL, DCS.
- **Talmud strata** — separating earlier rabbinic voices from the anonymous later editorial layer. *Sources:* Sefaria, Friedberg Talmud variants.
- **Early Quran manuscripts** — the Sana'a palimpsest preserves an erased lower text with variants from the standard text. *Sources:* Corpus Coranicum (Berlin), published Sana'a analyses.

### Science crossovers

- **Babylonian astronomical diaries** — centuries of nightly observations including eclipses; can measure the slowing of Earth's rotation and ancient solar activity. *Sources:* Sachs–Hunger *Astronomical Diaries*, ORACC.
- **Automated comparative method** — reconstruct proto-languages (Proto-Indo-European or deeper) with explicit, testable sound laws. *Sources:* LIV lexicon, Pokorny's IEW, Lexibank/CLDF datasets.
- **Stemmatics as phylogenetics** — building manuscript family trees to reconstruct the lost archetype. *Sources:* NTVMR collation data, Canterbury Tales project, Parzival project.
- **Dating by language drift** — date undated texts from linguistic features alone; could settle when Daniel or Deuteronomy was written. *Sources:* ETCBC, TLG, CDLI.
- **Ancient epidemics and climate in texts** — mining letters and chronicles for plagues, famines, and weather to join with ice cores and ancient DNA. *Sources:* ORACC letters, papyri.info, Chinese dynastic histories (ctext).
- **Sounding the past** — reconstruct ancient Greek music from surviving notation (Delphic hymns, Seikilos epitaph) combined with metrics. *Sources:* Pöhlmann & West's *Documents of Ancient Greek Music*.

### Moonshots

- **A "Rosetta finder"** — scan every museum catalogue for unrecognised bilingual inscriptions; the single thing that could crack Linear A overnight. *Sources:* museum open-access collections, CDLI, SigLA find-spot data.
- **A universal decipherment engine** — trained on every script ever deciphered (Linear B, Maya, Ugaritic, hieroglyphs), learns the *process*, then applied to all undeciphered ones. *Sources:* historical decipherment corpora, Bonn Maya Text Corpus (TWKM).
- **Living philology** — every restoration gets a calibrated probability, scored when new manuscripts or fragment joins turn up; makes philology a predictive science. *Sources:* Ithaca/Aeneas approach (DeepMind), PHI Greek Inscriptions, EDH, EDCS.

---

## Etymology Deep-Dive Tool

A word lookup tool that gives everything: meaning, attestations, etymology traced all the way back to proto-languages, and across all sister languages. Think Wiktionary but thorough, structured, and queryable.
