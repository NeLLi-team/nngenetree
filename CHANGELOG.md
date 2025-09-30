# Changelog

All notable changes to NNGeneTree will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-09-30

### 🚀 Major Migration - Nextflow Implementation

This release completely migrates NNGeneTree from Snakemake to Nextflow, providing better scalability, resume capabilities, and execution reports.

### ✨ Added

#### Workflow Engine
- **Nextflow Pipeline**: Complete rewrite using Nextflow DSL2
  - Modular process architecture in `modules/` directory
  - Built-in resume capability with `-resume` flag
  - Automatic execution reports (HTML timeline, DAG, trace)
  - Better cloud integration (AWS, Azure, Google Cloud ready)
  - Improved SLURM integration via `conf/slurm.config`

#### Execution
- **Unified Run Script**: Single `run_nextflow.sh` for all execution modes
  - `bash run_nextflow.sh test` - Test mode with verification
  - `bash run_nextflow.sh <dir> local` - Local execution
  - `bash run_nextflow.sh <dir> slurm` - SLURM cluster
  - Built-in output verification for test mode
- **Pixi Test Task**: `pixi run test` for quick testing

#### Features
- **Full Taxonomy in CSV**: `placement_results.csv` now includes complete taxonomy strings
  - Changed from domain-only to full lineage (e.g., "Bacteria;Bacillati;Bacillota;...")
- **Standardized Output**: All outputs now use `{input_dir}_output` pattern
- **Better Documentation**: Updated README with Nextflow-specific instructions

### 🔧 Changed

#### Configuration
- **Nextflow Config**: Moved from `workflow/config.txt` to `nextflow.config`
  - Profile-based execution (test, local, slurm)
  - Cleaner parameter override syntax
  - Resource configuration in config blocks
- **Script Location**: All scripts moved from `workflow/scripts/` to `bin/`
- **Query Prefixes**: Added documentation explaining example vs actual test values

### 🗑️ Removed

#### Legacy Files
- Removed all Snakemake execution scripts:
  - `run.sh` (Snakemake)
  - `run_container.sh` (Snakemake container)
  - `run_slurm.sh` (Snakemake SLURM)
  - `run_nextflow_test.sh` (merged into main script)
- Removed Snakemake-specific pixi tasks
- Cleaned up obsolete log files

### 🐛 Fixed
- **Java Version**: Scripts now use `pixi run nextflow` to ensure Java 11+ from pixi environment
- **Path Consistency**: All documentation updated with correct `bin/` paths
- **Output Deduplication**: Single output directory pattern across all modes

### 📚 Documentation
- Updated README.md with Nextflow usage
- Updated NEXTFLOW_README.md with comprehensive guide
- Added query_prefixes configuration explanation
- Removed all Snakemake references from user-facing docs

### ⚠️ Breaking Changes
- Snakemake workflow no longer maintained (available in `nngenetree-snk` branch)
- Command-line syntax changed from `snakemake --config` to `nextflow run main.nf --param`
- Configuration file format changed from text to Groovy/Nextflow config
- Output directory naming changed from `*_nngenetree` to `*_output`

### 🔄 Migration Notes
For users migrating from v1.0 (Snakemake):
1. Old Snakemake version preserved in branch `nngenetree-snk`
2. Update scripts to use `run_nextflow.sh` instead of `run.sh`
3. Convert `workflow/config.txt` settings to `nextflow.config` format
4. Update output directory references from `*_nngenetree` to `*_output`

## [1.0.0] - 2025-09-29

### 🎉 Major Release - Production Ready

This is the first stable release of NNGeneTree with significant improvements to dependency management, workflow reliability, and user experience.

### ✨ Added

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

### 🔧 Changed

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

### 🐛 Fixed

- **Duplicate Sequences**: Fixed tree-building failures caused by duplicate sequences
  - Self-hits now properly filtered during BLAST processing
  - Identical sequences removed before alignment
  - Comprehensive logging of deduplication statistics

- **Path Handling**: Fixed relative vs absolute path issues in workflow
  - Consistent use of absolute paths throughout
  - Container-compatible path management
  - Proper working directory handling

### 📝 Documentation

- **Configuration Guide**: Added comprehensive config override examples
- **Task Reference**: Complete table of all functional Pixi tasks
- **Version Badge**: Added GitHub link to README badge
- **OrthoFinder Workflow**: Documented genome-scale analysis workflows

### 🗑️ Removed

- **Example Directory**: Replaced with `test/` for consistency
- **Container Documentation**: Removed ~90 lines of untested container docs
- **Non-functional Tasks**: Removed dag, build-container, run-container, pytest tasks
- **Positional Arg Tasks**: Removed analyze, visualize, ortho-* convenience commands

### 🔐 Infrastructure

- **Git Workflow**: Added completion guard and hooks for code quality
- **Impact Tracking**: All new files documented in `.claude/impact.json`
- **Logging**: Comprehensive logging infrastructure in `logs/` directory

### 📊 Statistics

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

[1.0.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v1.0.0
[0.9.0]: https://github.com/NeLLi-team/nngenetree/releases/tag/v0.9.0