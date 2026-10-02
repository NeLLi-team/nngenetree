# Handoff: pipeline - production-path-fixes
**Date:** 2026-10-01
**Branch:** main
**HEAD:** 2c4e0a9

## Context & Status

Chef asked to confirm that this checkout is current, make it bug-free, check the
databases, and run it on the 05megagenomo packaging query set. The checkout matched
`origin/main` at ccc9eb4 (v1.3.0). The August review had used only the toy test
database, so a Codex review targeted the production path (NCBI nr, multi-genome
query sets with pipes in IDs). Three verified bugs and the follow-up review findings
are fixed in 2c4e0a9 and pushed to `origin/main`. No release or tag was made; the
changes sit under `[Unreleased]` in `CHANGELOG.md`.

The 05megagenomo production run is Slurm job 26628762 (Dori, `-M perceus-00`),
driven by `05megagenomo/packaging_related/slurm/run_nngenetree_2026-10-01.sh`.

## Technical Implementation

### Work Completed
- Neighbor lists hold database hits only: query leaves of every genome are excluded, one leaf resolved per query (`bin/extract_closest_neighbors.py`).
- Hit extraction logs "Extracted N of M requested sequences"; samples with no extracted sequence are skipped with a warning (`modules/extract_hits.nf`, `main.nf` extract_gate).
- Startup check: a BLAST protein database (`.pin` or `.pal`) must sit next to `<blast_db>.dmnd` (`main.nf`).
- Entrez: 4 attempts per batch with 15/30/45 s pauses, `HTTPException` included; the task fails if all fail; header-only `closest_neighbors_with_taxonomy.csv` only for a valid header-only neighbor CSV (`bin/parse_closest_neighbors.py`).
- `ASSIGN_TAXONOMY`: `maxForks 1`, `time '30m'` (`modules/taxonomy.nf`).
- IQ-TREE `--seed ${params.seed}`, default 12345 (`modules/phylogeny.nf`, `nextflow.config`).
- DIAMOND `>=2.2.8,<3`; lock moved 2.1.13 to 2.2.8, lock format 6 to 7 (`pixi.toml`, `pixi.lock`).
- Docs: `README.md` parameter table and skip note, `CHANGELOG.md` `[Unreleased]`.

### Outcomes
- **What worked:** Slurm proof job 26628683 (`tasks/proof/run_2026-10-01.sbatch`): test mode exit 0, 12-sample run exit 0, `postcheck.py` 21/21, `postcheck_2026-10-01.py` 8/8, negative test 1 (BLAST db without the hits) skipped the sample and finished, negative test 2 (`.dmnd` only) stopped at startup. Fixture tests for each fix under the session scratchpad.
- **What didn't:** proof job 26628607 ran partly on intermediate code, and its old postcheck failed one log check because a `-preview` run on the login node rotated `.nextflow.log` during the job.

### File Map
| File | Change | Notes |
|------|--------|-------|
| `bin/extract_closest_neighbors.py` | Modified | exclude query leaves |
| `bin/parse_closest_neighbors.py` | Modified | retries, header-only output; ruff sorted imports and replaced typing aliases |
| `main.nf` | Modified | BLAST-db startup check, extraction gate |
| `modules/extract_hits.nf` | Modified | extraction counts |
| `modules/taxonomy.nf` | Modified | maxForks 1, time 30m |
| `modules/phylogeny.nf`, `nextflow.config` | Modified | IQ-TREE seed |
| `pixi.toml`, `pixi.lock` | Modified | DIAMOND 2.2.8 |
| `README.md`, `CHANGELOG.md` | Modified | docs |

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Skip, not fail, a sample whose extraction is empty | keeps the 1.3.0 decision to skip sparse samples instead of killing multi-sample runs; a missing BLAST db fails at startup instead |
| DIAMOND 2.2.8 rather than 2.1.24 | newest bioconda build; reads the 2.1.19-built nr.dmnd (format 3); 2.1.15-2.1.23 have crash, leak and hang regressions |
| Keep DIAMOND fast mode as default | recorded user decision from 2026-08-24; set `--sensitive` per run when needed |
| Leave rank labels, self-hit threshold and min-hits warning as they are | design-level changes; listed in `tasks/todo.md` for a decision |

## Knowledge Capture

### Lessons Learned
- Run no Nextflow command in the repository directory while a proof job uses it: `.nextflow.log` rotation breaks log-based checks.
- The Slurm job cannot see the login-node scratchpad; proof inputs and outputs live in `tasks/proof/`.

### Gotchas
- `blastdbcmd -entry_batch` exits 1 when any accession is missing, so `|| true` is needed; check the counts instead.
- Biopython 1.85 `Entrez._open` retries HTTP 429 without pausing.
- Nextflow `-resume` does not notice tool upgrades; use a new work directory after `pixi install` changes tools.

## Moving Forward

### Next Steps
1. Check 05megagenomo job 26628762: outputs under `05megagenomo/packaging_related/nngenetree_output_2026-10-01/`, logs under `05megagenomo/packaging_related/logs/`.
2. Decide on the design items in `tasks/todo.md` (positional taxonomy ranks for viruses in `decorate_tree.py` first).
3. Tag a release (1.3.1) only after Chef approves.

### Blockers
- None.
