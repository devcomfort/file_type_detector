# Backend Conformance

Backend conformance compares `lexical`, `magic`, `magika`, and `hybrid` against
reviewed Ground Truth on Linux, macOS, and Windows. It does not publish one
universal accuracy percentage. Detector output depends on the operating system,
Python's MIME database, libmagic, and the Magika model.

## Source of Truth

| Artifact | Purpose |
| --- | --- |
| `tests/truth/backend_inventory_candidates.json` | Review state and evidence for every candidate fixture |
| `tests/truth/backend_inventory.json` | Verified records that collectors may evaluate |
| `tests/truth/backend_conformance_baseline.json` | Reviewed semantic observations for the supported CI matrix |

A fixture checksum identifies the bytes under review. It does not prove a MIME
type or extension. A record enters the authoritative inventory only after its
`ground_truth_review.status` is `verified` and its evidence, MIME alternatives,
extension aliases, and checksum validate.

## Evaluation Model

For each verified record and backend, the collector:

1. copies the fixture to a temporary probe path with the reviewed extension;
2. starts a fresh Python process so one backend run cannot contaminate another;
3. preserves the backend's raw output;
4. creates a semantic output by lowercasing, de-duplicating, and sorting MIME
   types and extensions; and
5. compares the semantic output with the reviewed alternatives.

`overall_match` requires both a MIME intersection and an extension intersection.
`no_result` and `error` remain separate states rather than being counted as
successful detections.

## Supported Matrix

The
[Backend conformance workflow](https://github.com/devcomfort-labs/filetype_detector/actions/workflows/backend-conformance.yml)
runs the complete inventory on these x64 environments:

| Runner label | GitHub runner | Native dependency |
| --- | --- | --- |
| `ubuntu-x64` | `ubuntu-22.04` | Ubuntu `libmagic1` package |
| `macos-x64` | `macos-15-intel` | Homebrew `libmagic` |
| `windows-x64` | `windows-2022` | `python-magic-bin==0.4.14` |

The report's execution matrix records the exact Python, filetype-detector,
python-magic, libmagic distribution, and Magika versions used by each run.
Treat a cross-platform difference as a runtime-matrix difference unless the
report isolates the operating system from those dependencies.

## Reports and Baseline

Each successful matrix uploads `backend-conformance-report` with:

- `backend-conformance.md` for review;
- `backend-conformance.json` for complete structured evidence;
- `backend-conformance.csv` for row-level analysis.

When no baseline exists, aggregation writes `candidate-baseline.json` without
passing or committing it automatically. A reviewer compares that candidate with
the full report before copying it to
`tests/truth/backend_conformance_baseline.json`.

Later runs fail on added, removed, or changed semantic observations. Raw-only
ordering or casing differences remain visible in the report but do not fail the
baseline gate.

## Read the Latest Evidence

1. Open the latest successful
   [Backend conformance workflow run](https://github.com/devcomfort-labs/filetype_detector/actions/workflows/backend-conformance.yml).
2. Download the `backend-conformance-report` artifact.
3. Read `backend-conformance.md` for the inventory review, runtime matrix,
   correctness, divergence, baseline status, and evidence rows.
4. Use the JSON or CSV file when you need every observation.

Do not copy a percentage from an older report into documentation. Link to the
run and retain its runtime matrix.

## Reproduce Locally

Validate that every candidate has a matching verified record:

```bash
python -m scripts.conformance.cli review \
  --candidates tests/truth/backend_inventory_candidates.json \
  --inventory tests/truth/backend_inventory.json \
  --root . \
  --require-complete
```

After installing libmagic, collect one local artifact:

```bash
LIBMAGIC_DISTRIBUTION="local:describe-installed-libmagic" \
python -m scripts.conformance.collector collect \
  --candidates tests/truth/backend_inventory_candidates.json \
  --inventory tests/truth/backend_inventory.json \
  --root . \
  --runner-label local \
  --output .artifacts/backend-conformance/local.json
```

Aggregate that artifact without the three-platform baseline:

```bash
python -m scripts.conformance.aggregate \
  --candidates tests/truth/backend_inventory_candidates.json \
  --inventory tests/truth/backend_inventory.json \
  --root . \
  --input .artifacts/backend-conformance/local.json \
  --output-dir .artifacts/backend-conformance/report \
  --expected-runner-label local
```

A local run proves the installed runtime's behavior. Only the GitHub Actions
matrix verifies the supported three-platform baseline.
