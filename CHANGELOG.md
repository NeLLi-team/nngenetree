# Changelog

All notable changes to NNGeneTree are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-08-24

### Fixed
- `placement_results.json`, `placement_results.csv`, and `combined_placement_results.json` use NCBI Entrez taxonomy. Earlier versions guessed the taxonomy from accession prefixes.
- `tree_stats.tab` lists the input queries only. Earlier versions listed every tree leaf.
- The OG column in `taxonomy_assignments.txt` contains the sample name. Earlier versions left it empty.
- `combined_placement_results.json` labels samples by input order. Earlier versions sorted staged files by name, which mislabeled runs with more than 9 samples.
- The neighbor window in `extract_closest_neighbors.py` ignores hits below `self_hit_threshold` when it picks the reference distance, so an identical database sequence no longer reduces the list to one neighbor.
- `entrez_email` from `conf/local.config` is exported to tasks as `ENTREZ_EMAIL`.
- Tasks use the tools in the repository's `.pixi/envs/default/bin` directory and unset `MAFFT_BINARIES`. The shell environment of the caller does not affect tasks.
- `test/db/test_reference.dmnd` is tracked in git, so a fresh clone can run `nngenetree test`.

### Changed
- Samples with fewer than 2 unique DIAMOND subjects are skipped with a log warning. The run continues.
- NCBI taxonomy is fetched for every BLAST hit in the tree with batched Entrez requests, not only for the closest neighbors.
- iTOL files are published to `<sample>/itol/`: `itol_labels.txt`, `itol_branch_colors.txt`, `itol_query_circles.txt`, and `itol_colorstrip.txt`.
- New parameters: `min_hits` (default 5), `diamond_sensitivity` (default empty, DIAMOND fast mode), and `self_hit_threshold` (default 0.001).
- The launcher forwards extra arguments to Nextflow, for example `nngenetree my_data local --blast_hits 50 --blast_db /path/to/nr`.
- The pipeline checks that `<blast_db>.dmnd` exists before it starts.
- Script interfaces: `parse_closest_neighbors.py` takes `--subjects` and `--og`; `extract_phylogenetic_neighbors.py` requires `--taxonomy`; `extract_closest_neighbors.py` accepts `--self_hit_threshold`.

### Removed
- The `CHECK_BLAST_OUTPUT` step and its `check_blast_output.done` and `check_blast_output.log` outputs.
- `bin/assign_bestblastp.py` and `bin/check_blast_output.py`.
- The README entry for `<input_dir>_output_completion.log`; the pipeline never produced that file.

## [1.2.0] - 2025-11-29

### Changed
- The NR database path is set in `conf/local.config` or the `NR_DATABASE` environment variable. Hardcoded paths were removed, and the pipeline prints setup instructions when no database is configured. `conf/local.config.template` is the starting point.
- Python scripts read the Entrez email from the `ENTREZ_EMAIL` environment variable.
- SLURM queue and account are set in `conf/local.config` instead of the tracked config files.
- Output messages, scripts, and documentation no longer use emojis; banners use ASCII characters.
- README reorganized with tables for the configuration options; obsolete references fixed.

### Fixed
- `pixi.toml` uses `[workspace]` instead of the deprecated `[project]`.
- The pixi test task calls `nngenetree` instead of the removed `run_nextflow.sh`.

### Removed
- References to the non-existent `NEXTFLOW_README.md`.
- Hardcoded paths in configuration files.

## [1.1.0] - 2025-09-30

The pipeline moved from Snakemake to Nextflow.

### Added
- Nextflow DSL2 pipeline with processes in `modules/`, `-resume`, and HTML timeline, DAG, and trace reports.
- SLURM settings in `conf/slurm.config`.
- `nngenetree` launcher for all execution modes: `nngenetree test` (with output verification), `nngenetree <dir> local`, and `nngenetree <dir> slurm`.
- `pixi run test` task.
- `placement_results.csv` contains the full taxonomy lineage instead of the domain only.
- All outputs use the `{input_dir}_output` pattern.

### Changed
- Configuration moved from `workflow/config.txt` to `nextflow.config` with the profiles `test`, `local`, and `slurm`.
- Scripts moved from `workflow/scripts/` to `bin/`.
- Documentation explains the example and test values of `query_prefixes`.

### Removed
- Snakemake execution scripts: `run.sh`, `run_container.sh`, `run_slurm.sh`, and `run_nextflow_test.sh` (merged into the launcher).
- Snakemake-specific pixi tasks and obsolete log files.

### Fixed
- Scripts call `pixi run nextflow` so that Nextflow uses the Java from the pixi environment.
- Documentation paths point to `bin/`.
- One output directory pattern across all modes.

### Breaking changes
- The Snakemake workflow is no longer maintained. It remains in the `nngenetree-snk` branch.
- Command-line syntax changed from `snakemake --config` to `nextflow run main.nf --param`.
- Configuration files are Nextflow (Groovy) config instead of text.
- Output directories are named `*_output` instead of `*_nngenetree`.

### Migration from 1.0
1. The Snakemake version is preserved in the `nngenetree-snk` branch.
2. Replace `run.sh` with `nngenetree`.
3. Convert `workflow/config.txt` settings to `nextflow.config`.
4. Update output directory references from `*_nngenetree` to `*_output`.

## [1.0.0] - 2025-09-29

First stable release.

### Added
- Pixi replaces conda: `pixi.toml` lists dependencies and tasks, `pixi install` sets up the environment, and the lockfile pins versions.
- Test database with 131 sequences in `test_db/`; `pixi run test-fast` runs the pipeline in minutes with `workflow/config_test.txt`.
- `combine_and_deduplicate.py` removes duplicate sequence IDs and identical sequences before tree building and logs the counts.
- `extract_phylogenetic_neighbors.py` extracts neighbors for query prefixes and writes JSON and CSV placement results; results are combined across samples.
- `process_blast_for_extraction.py` deduplicates hits across queries; a checkpoint validates BLAST output before sequence extraction.
- `orthofinder_preprocess.py` runs OrthoFinder on multiple genomes, filters orthogroups by target proteins, and writes one FASTA file per orthogroup.
- README rewritten with a quick start, configuration override examples, workflow diagrams, and the list of pixi tasks.

### Changed
- Outputs use the `{input_dir}_nngenetree` pattern; override with `--config output_dir=custom`.
- Pixi tasks reduced from 21 to 12. Non-functional tasks (container, pytest, dag) and tasks with positional arguments were removed.
- SLURM resources are set per rule: threads, memory, time, and disk.

### Fixed
- Tree building no longer fails on duplicate sequences: self-hits are filtered during BLAST processing, and identical sequences are removed before alignment.
- Relative and absolute paths are handled consistently in the workflow.

### Removed
- The `example/` directory, replaced by `test/`.
- Untested container documentation (about 90 lines).
- The tasks `dag`, `build-container`, `run-container`, `pytest`, `analyze`, `visualize`, and `ortho-*`.

## [0.9.0] - 2025-09-28

First tagged release: Snakemake pipeline with DIAMOND BLASTP against nr, MAFFT alignment, TrimAl trimming, IQ-TREE tree construction, N-nearest-neighbor extraction, NCBI taxonomy, ETE3 tree images, a conda environment, and SLURM support.

---

[1.3.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.3.0
[1.2.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.2.0
[1.1.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.1.0
[1.0.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.0.0
