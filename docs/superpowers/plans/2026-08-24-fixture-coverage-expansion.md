# Fixture Coverage Expansion Plan

_Goal: extend Ground-Truth coverage toward every format that magic or magika can
detect, on top of the four-axis GT contract (source_integrity / format_validity /
MIME evidence / content_identifiability)._

---

## 📋 Current state (measured 2026-08-24, magika model output)

**Parity definition**: every non-internal magika label must have ≥1 independently
valid fixture that magika actually labels as that target
(`result.output.label`), measured with the locked model. Suffix-space inclusion
alone is not coverage — a shared suffix such as `.ts` can exist while no fixture
is classified as the intended target.

| Metric | Value |
| --- | --- |
| Authoritative inventory | 598 records / 591 unique suffixes / 226 MIME types |
| Magika model labels | 214 (2 internal test labels excluded → 212 real) |
| **Labels covered by actual model output** | **160 / 212** |
| **Model-output gap** | **52 labels** |
| ↳ no fixture at all | 21 (`autohotkey cat dicom dsstore emf gemfile gitattributes gitmodules hlp htaccess ignorefile macho mum outlook powershell pythonbytecode pytorch squashfs stltext wmf zlibstream`) |
| ↳ fixture exists but model mislabels | 31 |
| Magic-side universe | ~3,351 magic patterns in libmagic DB (needs DB parse to enumerate) |

### Why the 31 existing fixtures miss their labels

| Root cause | Count | Fix |
| --- | ---: | --- |
| A. Minimal stub too small for the model (`ace cab chm crx deb dex elf icns lha swf webm xar woff`, `flac`→bmp, `tga`→bmp, `rpm`/`snap`→stlbinary) | 17 | regenerate richer, spec-valid fixtures |
| B. Generic container subtype (`apk`/`xpi`→zip, `ai`→pdf, `textproto`→yaml, `jinja`→twig) | 5 | add subtype-distinguishing entries (JAR-style MANIFEST, OpusHead, etc.) |
| C. Text format model folds into txt (`aidl dm dwg sgml sum`) | 5 | accept as model limit; record as `ambiguous` quality tier |
| D. Header-only CFB (`msi one` → unknown) | 2 | real CFB streams required |
| E. Model borderline (`ttf`↔coff, `pdb`→proteindb) | 2 | acceptable; document as known ambiguity |

Fixture actions required: **21 new + 17 richer + 5 subtype entries + 2 CFB = 45**.
C and E (7 labels) are documented model limits, not fixture-fixable.
"Everything magic supports" requires parsing the magic database and prioritizing;
full parity with all 3,351 patterns is not a sensible goal — many are legacy,
ambiguous, or untestable without real-world samples.

## 🎯 Targets

| Target | Definition of done | Effort |
| --- | --- | --- |
| T1 — Magika parity | Two metrics: **catalog GT coverage** — all 212 real labels have ≥1 independently valid fixture (achievable 212/212); **locked-model recognition coverage** — fixtures the locked model actually labels as their target, currently 160/212, target 205/212 with C+E signed off as limits unless representative upstream Magika samples prove them | 45 fixture actions |
| T2 — Magic priority set | Top-N most-used libmagic MIME types covered (N≈300, ranked by usage frequency) | staged |
| T3 — Registry alignment | Every GT MIME either IANA-registered or carries vendor/spec evidence | audit pass |

## 🗂 The 52-label gap, by remediation class

### R1 — new fixtures for absent labels (21)

`autohotkey cat dicom dsstore emf gemfile gitattributes gitmodules hlp htaccess
ignorefile macho mum outlook powershell pythonbytecode pytorch squashfs stltext
wmf zlibstream`

Split: 18 text/simple-header formats (trivial generators) + `dicom` (pydicom,
already proven), `macho`/`pebin`-style Mach-O header, `pythonbytecode` from the
pinned CPython.

### R2 — richer fixtures for mislabeled stubs (16)

`ace cab chm crx deb dex elf icns lha swf webm xar` + `flac tga rpm snap`
(currently misdetected as bmp/stlbinary). Regenerate with spec-valid content of
sufficient materiality; keep Tier-2 pinned-SHA handling where writers are
nondeterministic.

### R3 — subtype-identifiable entries (5)

`apk xpi` need JAR/XPI distinguishing entries; `ai` needs real Illustrator-
compatible PDF; `textproto`/`jinja` accepted as ambiguous quality tier unless a
distinguishing convention exists.

### Accepted model limits (7, documented not fixed)

`aidl dm dwg sgml sum` (model folds into txt), `ttf`↔coff borderline,
`pdb`→proteindb. Recorded as `ambiguous` tier in reports; excluded from parity
denominator after review sign-off.



### Canonical action list (45)

- **21 new**: `autohotkey cat dicom dsstore emf gemfile gitattributes gitmodules
  hlp htaccess ignorefile macho mum outlook powershell pythonbytecode pytorch
  squashfs stltext wmf zlibstream`
  (`pebin` is already covered — magika labels our `.exe`/`.dll` fixtures as
  `pebin`; no separate record needed.)
- **17 richer regenerations**: `ace cab chm crx deb dex elf icns lha swf webm xar
  woff flac tga rpm snap`
- **5 subtype entries**: `apk xpi ai textproto jinja`
- **2 CFB rebuilds**: `msi one`

## ⚙️ Per-record pipeline (unchanged contract)

1. Generate or pin fixture bytes → SHA-256.
2. Candidate entry: probe_extension + ground_truth + provenance.
3. Four axes: source_integrity (`generated` recipe hash or `external` commit URL),
   format_validity (independent parser), content_identifiability (quality tier),
   MIME evidence (IANA/vendor link).
4. Human review promotes candidate → authoritative inventory.
5. Conformance matrix re-collects; new baseline reviewed and committed.

## 📅 Rollout

| Wave | Content | Actions | Gate before merge |
| --- | --- | --- | --- |
| W1 | Phase B–D infrastructure (4-axis loader, manifest, quality-slice report, model-output parity script) | 0 | existing 598 stay green under new schema |
| W2 | R1 new fixtures — text/simple-header subset | +15 | slow-scan error=0; parity script shows each new label hit; matrix green |
| W3 | R1 binary remainder (12) + R2 richer (17) + CFB rebuilds (2) | +31 | same gates; mislabel table shrinks accordingly |
| W4 | R3 subtype entries + accepted-limits sign-off | +5 / −7 from denominator | parity report at 100 % of effective labels |
| W5+ | Magic-priority set from DB parse (T2) | batches of ~50 | same pipeline |

Projected end state: **catalog GT coverage 212/212**; **locked-model recognition
coverage 205/212** (160 today + 45 fixture actions; the 7 C/E labels stay
documented limits unless representative upstream Magika samples prove them),
inventory ≈ 650 records.

## ✅ Acceptance criteria for "magika parity"

- Measured by `.audit/magika_parity.py` against the locked model: every label in
  `target_labels_space` minus internal labels minus signed-off model limits has ≥1
  fixture whose `result.output.label` equals that target.
- Every new record passes all three truth axes at `verified`.
- Conformance matrix reports no new cross-OS divergence attributable to the new
  fixtures; quality-tier slicing shows where backends are generic-container-limited.

