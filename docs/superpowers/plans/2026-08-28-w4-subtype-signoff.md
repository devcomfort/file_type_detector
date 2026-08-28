# W4 Subtype and Model-Limit Sign-off

Date: 2026-08-28
Branch: `gt/coverage-expansion`

## Scope

This sign-off records the validation evidence for the W4 subtype fixtures and the seven labels accepted as locked-model limits. Detector output is recorded as an observation only; it is not Ground Truth evidence.

## Subtype fixtures

| Fixture | Independent validation | Locked Magika observation | Disposition |
|---|---|---|---|
| `sample.apk` | ZIP member inventory checked; `AndroidManifest.xml` marker has a self-consistent 16-byte chunk; embedded `classes.dex` is checked by the DEX checksum/signature/map validator | `jar` (0.96) | **Not promoted**: full Android binary-AXML parser validation still required |
| `sample.xpi` | ZIP member inventory checked; `manifest.json` is valid JSON with manifest version, name, and version | `xpi` (0.91) | Candidate remains excluded pending independent XPI package validation |
| `sample.ai` | PDF header/trailer and Illustrator creator marker checked structurally | `pdf` (0.89) | **Not promoted**: PDF compatibility is not proof of Illustrator semantics |
| `sample.textproto` | Fixture contains protobuf text-field syntax: scalar fields, nested message, boolean, and repeated list syntax | `yaml` (0.83) | Accepted as ambiguous model behavior; no subtype claim promoted |
| `sample.jinja` | Fixture contains Jinja delimiters, inheritance, block, filter, loop, and conditional syntax | `twig` (0.68) | Accepted as ambiguous model behavior; no subtype claim promoted |

The APK and AI records remain quarantined because the available checks do not establish the complete subtype semantics. XPI has a valid extension manifest marker but remains excluded until an independent package validator is added.

## Accepted locked-model limits

These labels were measured against the current locked Magika model and are excluded from the effective recognition denominator. They remain catalog entries where independently valid fixture bytes exist; their observed label is documented rather than used as Ground Truth.

| Target label | Fixture size | Observed locked label | Disposition |
|---|---:|---|---|
| `aidl` | 52 B | `txt` (0.49) | Accepted model limit; text syntax is not distinguishable to the locked model |
| `dm` | 29 B | `txt` (0.25) | Accepted model limit |
| `dwg` | 134 B | `txt` (0.31) | Accepted model limit; minimal text-like sample is insufficient for model recognition |
| `sgml` | 75 B | `txt` (0.30) | Accepted model limit |
| `sum` | 45 B | `txt` (0.52) | Accepted model limit |
| `ttf` | 80 B | `coff` (0.93) | Accepted borderline classification; both are binary formats with overlapping model evidence |
| `pdb` | 304 B | `proteindb` (1.00) | Accepted borderline classification; model collision is documented |

## Gate decision

- No W4 subtype fixture is promoted solely from a Magika label.
- `textproto` and `jinja` are signed off as ambiguous model behavior, not as successful target-label recognition.
- The seven limit labels are excluded from the effective locked-model denominator.
- Authoritative promotion remains gated on source integrity, independent format validity, MIME evidence, and content identifiability.
