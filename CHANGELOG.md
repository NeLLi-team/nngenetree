# Changelog

All notable changes to NNGeneTree will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-08-24

### Fixed
- **Placement Taxonomy**: `placement_results.json`, `placement_results.csv` and `combined_placement_results.json` now use NCBI Entrez taxonomy; previously the taxonomy was guessed from accession prefixes
- **Tree Statistics**: `tree_stats.tab` lists the input queries only; previously it listed every tree leaf
- **Taxonomy Assignments**: The OG column in `taxonomy_assignments.txt` is the sample name; previously empty
- **Entrez Email**: `entrez_email` from `conf/local.config` is exported as `ENTREZ_EMAIL` to tasks
- **Environment Isolation**: Tasks resolve tools from the repository's `.pixi/envs/default/bin` and unset `MAFFT_BINARIES`; the shell environment of the caller does not affect tasks
- **Test Database**: `test/db/test_reference.dmnd` is tracked in git; a fresh clone can run `nngenetree test`

### Changed
- **Sparse Samples**: Samples with fewer than 2 unique DIAMOND subjects are skipped with a log warning; the run continues
- **Taxonomy Fetch**: NCBI taxonomy is fetched for every BLAST hit in the tree with batched Entrez efetch, not only for the closest neighbors
- **iTOL Files**: Published to `<sample>/itol/` as `itol_labels.txt`, `itol_branch_colors.txt`, `itol_query_circles.txt` and `itol_colorstrip.txt`
- **New Parameters**: `min_hits` (default 5), `diamond_sensitivity` (default empty: DIAMOND fast mode), `self_hit_threshold` (default 0.001)
- **Launcher**: Extra arguments are forwarded to Nextflow, for example `nngenetree my_data local --blast_hits 50 --blast_db /path/to/nr`
- **Script Interfaces**: `parse_closest_neighbors.py` takes `--subjects` and `--og`; `extract_phylogenetic_neighbors.py` requires `--taxonomy`; `extract_closest_neighbors.py` accepts `--self_hit_threshold`

### Removed
- `CHECK_BLAST_OUTPUT` step with `check_blast_output.done` and `check_blast_output.log`
- `bin/assign_bestblastp.py` and `bin/check_blast_output.py`
- `<input_dir>_output_completion.log`

## [1.2.0] - 2025-11-29

### Changed

#### Configuration
- **Configurable Database Path**: Removed hardcoded NR database paths
  - Database path now set via `conf/local.config` (recommended) or `NR_DATABASE` environment variable
  - Clear error message with setup instructions if database not configured
  - Added `conf/local.config.template` for easy setup
- **Configurable Entrez Email**: Python scripts now use `ENTREZ_EMAIL` environment variable
- **SLURM Settings**: Removed hardcoded queue/account settings; now configurable in `conf/local.config`

#### User Interface
- **Removed Emojis**: Cleaned up all output messages, scripts, and documentation
- **Simplified Banners**: Replaced Unicode box-drawing characters with ASCII

#### Documentation
- **Restructured README**: Cleaner, more intuitive organization
  - Removed emojis throughout
  - Added proper tables for configuration options
  - Fixed obsolete references
- **Updated CHANGELOG**: Consistent formatting without emojis

### Fixed
- **pixi.toml**: Changed deprecated `[project]` to `[workspace]`
- **Task Reference**: Fixed obsolete `run_nextflow.sh` reference to `nngenetree`

### Removed
- Obsolete references to non-existent `NEXTFLOW_README.md`
- Hardcoded paths from all configuration files

## [1.1.0] - 2025-09-30

### Major Migration - Nextflow Implementation

This release completely migrates NNGeneTree from Snakemake to Nextflow, providing better scalability, resume capabilities, and execution reports.

### Added

#### Workflow Engine
- **Nextflow Pipeline**: Complete rewrite using Nextflow DSL2
  - Modular process architecture in `modules/` directory
  - Built-in resume capability with `-resume` flag
  - Automatic execution reports (HTML timeline, DAG, trace)
  - Better cloud integration (AWS, Azure, Google Cloud ready)
  - Improved SLURM integration via `conf/slurm.config`

#### Execution
- **Unified Run Script**: Single `nngenetree` script for all execution modes
  - `nngenetree test` - Test mode with verification
  - `nngenetree <dir> local` - Local execution
  - `nngenetree <dir> slurm` - SLURM cluster
  - Built-in output verification for test mode
- **Pixi Test Task**: `pixi run test` for quick testing

#### Features
- **Full Taxonomy in CSV**: `placement_results.csv` now includes complete taxonomy strings
  - Changed from domain-only to full lineage (e.g., "Bacteria;Bacillati;Bacillota;...")
- **Standardized Output**: All outputs now use `{input_dir}_output` pattern
- **Better Documentation**: Updated README with Nextflow-specific instructions

### Changed

#### Configuration
- **Nextflow Config**: Moved from `workflow/config.txt` to `nextflow.config`
  - Profile-based execution (test, local, slurm)
  - Cleaner parameter override syntax
  - Resource configuration in config blocks
- **Script Location**: All scripts moved from `workflow/scripts/` to `bin/`
- **Query Prefixes**: Added documentation explaining example vs actual test values

### Removed

#### Legacy Files
- Removed all Snakemake execution scripts:
  - `run.sh` (Snakemake)
  - `run_container.sh` (Snakemake container)
  - `run_slurm.sh` (Snakemake SLURM)
  - `run_nextflow_test.sh` (merged into main script)
- Removed Snakemake-specific pixi tasks
- Cleaned up obsolete log files

### Fixed
- **Java Version**: Scripts now use `pixi run nextflow` to ensure Java 11+ from pixi environment
- **Path Consistency**: All documentation updated with correct `bin/` paths
- **Output Deduplication**: Single output directory pattern across all modes

### Documentation
- Updated README.md with Nextflow usage
- Added query_prefixes configuration explanation
- Removed all Snakemake references from user-facing docs

### Breaking Changes
- Snakemake workflow no longer maintained (available in `nngenetree-snk` branch)
- Command-line syntax changed from `snakemake --config` to `nextflow run main.nf --param`
- Configuration file format changed from text to Groovy/Nextflow config
- Output directory naming changed from `*_nngenetree` to `*_output`

### Migration Notes
For users migrating from v1.0 (Snakemake):
1. Old Snakemake version preserved in branch `nngenetree-snk`
2. Update scripts to use `nngenetree` instead of `run.sh`
3. Convert `workflow/config.txt` settings to `nextflow.config` format
4. Update output directory references from `*_nngenetree` to `*_output`

## [1.0.0] - 2025-09-29

### Major Release - Production Ready

This is the first stable release of NNGeneTree with significant improvements to dependency management, workflow reliability, and user experience.

### Added

#### Dependency Management
- **Pixi Package Manager**: Replaced conda with Pixi for faster, more reliable dependency management
  - Single `pixi.toml` file for all dependencies and tasks
  - Automatic environment setup with `pixi install`
  - Lockfile support for reproducible environments
  - Integrated task runner: `pixi run <task>`

#### Testing Infrastructure
- **Fast Test Suite**: Added small test database (131 sequences) for rapid validation
  - `test_db/` directory with pre-built BLAST database
  - `pixi run test-fast`: Complete pipeline test in minutes
  - Test configuration: `workflow/config_test.txt`

#### Pipeline Features
- **Sequence Deduplication**: New `combine_and_deduplicate.py` script prevents duplicate sequences in phylogenetic trees
  - Removes duplicate sequence IDs
  - Detects and removes identical sequences with different IDs
  - Detailed deduplication statistics in logs
- **Phylogenetic Placement**: Enhanced neighbor extraction with taxonomy
  - `extract_phylogenetic_neighbors.py`: Extract neighbors for specific query prefixes
  - Detailed placement results in JSON and CSV formats
  - Combined placement results across all samples
- **BLAST Processing**: Improved hit processing and validation
  - `process_blast_for_extraction.py`: Deduplicate hits across queries
  - Checkpoint validation before sequence extraction
  - Better error handling and logging

#### Documentation
- **Comprehensive README**: Complete rewrite with clear usage examples
  - Quick start guide
  - Configuration override examples
  - Detailed pipeline workflow diagrams
  - All functional Pixi tasks documented
- **Project Guidelines**: Added `CLAUDE.md` for AI assistant integration
- **Impact Tracking**: Complete `.claude/impact.json` for change documentation

#### OrthoFinder Integration
- **Genome-Scale Analysis**: New `orthofinder_preprocess.py` script
  - Process multiple genomes through OrthoFinder
  - Filter orthogroups by target proteins
  - Automatic FASTA file generation for each orthogroup
  - Direct integration with NNGeneTree pipeline

### Changed

#### Configuration
- **Standardized Output**: All outputs now use `{input_dir}_nngenetree` pattern
  - Consistent naming across all workflows
  - Removed confusing `test_output` override
  - Clear override mechanism via `--config output_dir=custom`

#### Pipeline Tasks
- **Streamlined Commands**: Reduced from 21 to 12 functional tasks
  - Removed non-functional tasks (container, pytest, dag)
  - Removed tasks with problematic positional arguments
  - All remaining tasks are tested and functional
  - Clear documentation for direct script usage

#### Workflow
- **Resource Configuration**: Improved resource allocation for SLURM
  - Per-rule thread, memory, and time specifications
  - Better default values for cluster execution
  - Disk space allocation for large alignments

### Fixed

- **Duplicate Sequences**: Fixed tree-building failures caused by duplicate sequences
  - Self-hits now properly filtered during BLAST processing
  - Identical sequences removed before alignment
  - Comprehensive logging of deduplication statistics

- **Path Handling**: Fixed relative vs absolute path issues in workflow
  - Consistent use of absolute paths throughout
  - Container-compatible path management
  - Proper working directory handling

### Documentation

- **Configuration Guide**: Added comprehensive config override examples
- **Task Reference**: Complete table of all functional Pixi tasks
- **Version Badge**: Added GitHub link to README badge
- **OrthoFinder Workflow**: Documented genome-scale analysis workflows

### Removed

- **Example Directory**: Replaced with `test/` for consistency
- **Container Documentation**: Removed ~90 lines of untested container docs
- **Non-functional Tasks**: Removed dag, build-container, run-container, pytest tasks
- **Positional Arg Tasks**: Removed analyze, visualize, ortho-* convenience commands

### Infrastructure

- **Git Workflow**: Added completion guard and hooks for code quality
- **Impact Tracking**: All new files documented in `.claude/impact.json`
- **Logging**: Comprehensive logging infrastructure in `logs/` directory

### Statistics

- **Files Added**: 50+ new files (test database, scripts, configs, documentation)
- **Lines Changed**: ~600 lines modified since v0.9.0
- **Documentation**: README grew from ~350 to ~450 lines of useful content
- **Tasks**: Reduced from 21 to 12 functional, tested tasks

## [0.9.0] - 2025-09-28

### Initial tagged release
- Basic Snakemake pipeline for phylogenetic analysis
- DIAMOND BLASTP search against nr database
- MAFFT alignment and TrimAl trimming
- IQ-TREE phylogenetic tree construction
- N-nearest neighbor extraction
- NCBI taxonomy integration
- ETE3 tree visualization
- Conda-based dependency management
- SLURM cluster support

---

[1.3.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.3.0
[1.2.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.2.0
[1.1.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.1.0
[1.0.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.0.0
[0.9.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v0.9.0
