# Configuration

## Per-Job Knobs

Per-job settings live in `jobs/<job-id>/intake.json` and are mirrored in the
`jobs.intake_json` SQLite column. `research start` writes them from CLI flags
and intake answers; plan YAML can override some behavior per task by setting
fields on `task_template[].payload`.

| Field | Default | Scope | Behavior |
|---|---:|---|---|
| `translate_non_english` | `false` | job or task payload | When true, extraction writes an English mirror for each non-English finding as `findings/NNNNNN.translation.md`. |
| `fragments` | `false` | job | Records that the operator requested section-fragment synthesis with `research start --fragments`. Runtime routing still uses `RESEARCH_FRAGMENT_SYNTH=1`, which the CLI sets for the spawned daemon. |
| `corpus_dossier` | `false` | job | When true, daemon local-corpus ingestion passes `per_page=True` to `local_corpus.index(...)` for files it indexes, writing one Source row per PDF page with `metadata.{parent_file, page_no, page_chunk}` stamped on the sidecar. Required by the dossier rollup (epic #359). Enabled with `research start --corpus-dossier`; the flag is rejected without `--corpus`. |
| `pdf_hybrid_pages` | `false` | job | When true, local-corpus PDF extraction merges the text layer with Tesseract OCR per page (`tools.pdf` hybrid mode). Use for FOIA / archival corpora that mix typed sections with scanned inserts. |
| `pdf_max_pages` | `1000` | job | Per-PDF page cap for local-corpus indexing. Clamped to `MAX_PAGES_HARD_CAP = 1000` regardless of intake value. |
| `pdf_max_chars` | `2_000_000` | job | Per-PDF character cap for local-corpus indexing. |

`translate_non_english` is intentionally opt-in. Use it for multilingual
archive runs where French, Spanish, or other non-English primary sources are
material to the answer. Do not enable it for English-only goals.

When enabled, each translated finding uses the `frontier_speed` tier and is
budget-tracked through `BudgetTracker`. If the estimated translation would push
the job past its cap, the original finding is still kept, no translation file is
written, and the loop emits an `INFO` event named `translation_skipped_budget`.

Task-level opt-in example:

```yaml
task_template:
  - kind: gallica_search
    payload:
      query: guerre d'Algerie 1956
      translate_non_english: true
```

Job-level CLI opt-in:

```bash
research start --skip-intake --goal "Algerian war archives" --translate-non-english
```

## Embedding Dimension Migration (issue #376)

The local-corpus embedding tier now emits **768-dimensional** vectors
(model `qwen3-embedding-4b-dwq` in `config/models.yaml`, model
`text-embedding-nomic-embed-text-v1.5` in `config/models.local.yaml`).
`tools/local_corpus.py` sets `EMBED_DIM = 768` to match.

Pre-upgrade jobs persisted 1024-d float32 blobs in `sources.embedding`.
Running `research search` against those rows after upgrading will not search
them cleanly: current code skips mismatched vectors, and older code paths may
fail while reading them. Choose one:

- **Drop the index**: `rm data/index.sqlite` and re-run `research start`
  for any job whose corpus you still need (re-embeds at $0 on local).
- **Per-job re-index**: delete the affected rows from `sources` and
  `job_sources` and re-run `research start` for that job.

New jobs created after the upgrade are unaffected.

## Fragment Synthesis Rollout

Whole-report synthesis remains the default. To opt a job into section-fragment
synthesis, run:

```bash
research start --skip-intake --goal "Widget Co governance" --fragments
```

The flag sets `RESEARCH_FRAGMENT_SYNTH=1` for the daemon and stores
`"fragments": true` in `jobs/<job-id>/intake.json`. Fragment state is persisted
under `fragments/<section>/NNNN.{md,json}` and mirrored in SQLite, so resume and
final-synthesis paths reassemble `report.md` from the latest fragments after a
restart. Logs include a `synthesis_mode` event with `mode="fragments"` or
`mode="legacy"` for operator visibility.

## Corpus Dossier Mode (epic #359)

Default corpus ingestion does whole-document chunking and runs one
synthesis pass at task 25, which produces a thematic summary of the
corpus. For investigations that need a **forensic dossier of every
file** in a corpus, opt into dossier mode:

```bash
research start --skip-intake --goal "Exhaustive dossier of UFO records" \
    --corpus corpus/ufo-records --corpus-dossier --local
```

`--corpus-dossier` requires `--corpus`; running with the flag set and
no corpus path exits with code 2. The flag writes
`"corpus_dossier": true` into `jobs/<job-id>/intake.json`. With the flag
on, local-corpus ingestion runs in per-page mode whenever the daemon
indexes operator-supplied files. The current inbox watcher already uses
this field; the corpus-walk startup path will use the same intake field
when it lands. In per-page mode, the indexer:

- Routes every PDF through `pdf.extract_pages_sync()` (one page per
  `Source` row, sub-chunked within the page when a single page exceeds
  the chunk-target token budget).
- Routes HTML / Markdown / TXT through the existing chunker but still
  stamps `metadata.parent_file` on every chunk so the rollup can group
  by file.
- Surfaces page-grain rows to semantic search and synthesis (each row
  becomes a citable Source).

The downstream dossier rollup (Stage 2 of the ladder, filed in M2 of
the epic) reads `metadata.parent_file` to build one
`findings/dossiers/<slug>.md` per file plus a `dossiers` structured
artifact. Stage 1 in this PR series is just the ingestion plumbing —
M1.2 wires the per-page coverage ledger, and M2 fills in the
extraction / rollup tasks.

## Candidate Roster Handoff Backtest

The 2026 federal candidate-roster regression runs without live network access:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_candidate_roster_backtest.py -q
```

It covers planner handoff failures before enqueue: grouped
`state_election_search` tasks without `state`, full state names repaired to
postal abbreviations, empty FEC candidate searches repaired to
`kind=candidates_enumerate` when structured filters exist, and rejected when
they do not.

When LM Studio and live source access are available, run a short local smoke
from the repo root:

```bash
UV_CACHE_DIR=.uv-cache uv run research start \
  --skip-intake \
  --local \
  --max-tasks 10 \
  --goal "As of May 15, 2026, create a complete sourced state-by-state list of every U.S. House and Senate candidate in all 50 states."
```

Then inspect the job events for connector-contract repairs/rejections and
cadence diagnostics:

```bash
jq 'select(.kind=="connector_contract_rejected" or .kind=="connector_contract_repaired" or .kind=="warning" or (.kind=="checkpoint" and (.payload.checkpoint_kind=="synthesis_done" or .payload.checkpoint_kind=="critique_done")))' \
  jobs/<job-id>/events.jsonl
```

The smoke is healthy when malformed connector tasks are absent or logged as
contract repairs/rejections before dispatch, local model routing is visible in
the daemon logs, and any synthesis/critique failure appears as a `warning`
event instead of a quiet pending-task stall.
