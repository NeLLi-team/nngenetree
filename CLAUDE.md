# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

NNGeneTree (v0.9.0) is a Snakemake-based bioinformatics pipeline for phylogenetic analysis and taxonomic classification of protein sequences. It processes FASTA files (.faa) containing one or more protein sequences, performs BLASTP searches against a reference database (nr), extracts top hits, performs multiple sequence alignment, builds phylogenetic trees, and identifies the N nearest neighbors per query based on branch lengths. The pipeline provides comprehensive summary statistics and taxonomy assignments.

## Key Commands

### Installation

**Install dependencies with Pixi:**
```bash
# Install pixi if not already installed
curl -fsSL https://pixi.sh/install.sh | bash

# Install project dependencies
pixi install
```

### Running the Pipeline

**Using Pixi tasks (recommended):**
```bash
# Fast test with small database (completes in minutes)
pixi run test-fast                     # run with test database (10 sequences)
pixi run test-dry                      # dry run with test configuration
pixi run clean-test                    # clean test outputs

# Run on example directory with full nr database
pixi run example-local                 # run locally with 16 cores
pixi run example-slurm                 # run on SLURM cluster

# Run on custom directory
pixi run run-local <input_directory>  # run locally with 16 cores
pixi run run-slurm <input_directory>  # run on SLURM cluster

# Dry run to see what would be executed
pixi run dry-run

# Generate pipeline DAG visualization
pixi run dag
```

**Traditional execution (requires pixi install first):**
```bash
# Local execution (16 cores)
bash run.sh <input_directory> true
# Example: bash run.sh example true

# SLURM cluster execution (default)
bash run.sh <input_directory>
# Example: bash run.sh example
```

**Container execution (optional, may not be fully functional):**
```bash
# Local with container
./run_container.sh -i example -l -p 8

# SLURM with container
./run_container.sh -i example -b /path/to/blast/db
```

### Development Commands

**Using Pixi tasks:**
```bash
# Start interactive shell with environment
pixi shell

# Clean output files
pixi run clean      # Clean example output
pixi run clean-all  # Clean all outputs

# Development tasks
pixi run lint       # Lint Python scripts with flake8
pixi run format     # Format Python scripts with black
pixi run test       # Run tests with pytest

# Development shell with extra tools
pixi run dev-shell
```

**Run specific Snakemake targets:**
```bash
# Within pixi environment (or after pixi shell)
snakemake --config input_dir="example" -n

# Run a specific rule
snakemake --config input_dir="example" --cores 4 <rule_name>
```

**Check pipeline status:**
```bash
# View completion log
cat example_nngenetree_completion.log

# Check SLURM job logs
ls -la log/nngenetree_*.out
```

## Architecture & Core Components

### Pipeline Flow
The pipeline follows this sequence:
1. **DIAMOND BLASTP** (`run_diamond_blastp`): Fast protein similarity search against reference database (default: 20 hits per query)
2. **Process BLAST Results** (`process_blast_results`): Extract unique subject IDs and filter hits
3. **Check BLAST Output** (`check_blast_output`): Validate BLAST results before proceeding
4. **Extract Sequences** (`extract_hits`): Retrieve hit sequences from BLAST database using blastdbcmd
5. **Combine Sequences** (`combine_sequences`): Merge query and hit sequences into single FASTA
6. **Alignment** (`align_sequences`): MAFFT multiple sequence alignment of combined sequences
7. **Trimming** (`trim_alignment`): TrimAl removes poorly aligned regions (gap threshold 0.1)
8. **Tree Building** (`build_tree`): IQ-TREE constructs phylogenetic tree (LG+G4 model)
9. **Neighbor Extraction** (`extract_closest_neighbors`): Find N closest sequences per query based on phylogenetic distance (default: 10 neighbors)
10. **Phylogenetic Placement** (`extract_phylogenetic_placement`): Extract top 5 neighbors with taxonomy for specific query prefixes (e.g., Hype, Klos)
11. **Taxonomy Assignment** (`assign_taxonomy`): Fetch NCBI taxonomy for neighbors using Entrez API
12. **Tree Decoration** (`decorate_tree`): Generate PNG visualizations with taxonomic annotations
13. **Tree Statistics** (`calculate_tree_stats`): Compute phylogenetic statistics
14. **Combine Results** (`combine_placement_results`): Aggregate placement results across all samples into single JSON

### Key Files & Directories

**Configuration:**
- `workflow/config.txt` - Main pipeline configuration (BLAST DB path, hit counts, resource allocations)
- `workflow/Snakefile` - Snakemake workflow definition with all rules and dependencies
- `pixi.toml` - Pixi package manager configuration with dependencies and tasks

**Key Scripts:**
- `workflow/scripts/process_blast_for_extraction.py` - Process BLAST results and extract unique subjects
- `workflow/scripts/check_blast_output.py` - Validate BLAST output before proceeding
- `workflow/scripts/extract_closest_neighbors.py` - Find N closest phylogenetic neighbors per query
- `workflow/scripts/extract_phylogenetic_neighbors.py` - Extract neighbors with taxonomy for specific query prefixes
- `workflow/scripts/parse_closest_neighbors.py` - Fetch NCBI taxonomy for neighbors via Entrez API
- `workflow/scripts/decorate_tree.py` - Create tree visualizations with taxonomic annotations
- `workflow/scripts/tree_stats.py` - Calculate phylogenetic distance statistics
- `workflow/scripts/orthofinder_preprocess.py` - OrthoFinder integration for genome-scale analysis

**Shell Scripts:**
- `run.sh` - Main pipeline runner (local or SLURM execution)
- `run_slurm.sh` - SLURM-specific execution script
- `run_container.sh` - Container-based execution (may not be fully functional)

**Example Data:**
- `example/` - Test directory containing test1.faa and test2.faa files

### Output Structure
```
<input_dir>_nngenetree/
├── <sample>/                                    # Per-sample results directory
│   ├── blast_results.m8                         # DIAMOND BLAST tabular output
│   ├── unique_subjects.txt                      # List of unique hit accessions
│   ├── check_blast_output.done                  # Validation checkpoint
│   ├── extracted_hits.faa                       # FASTA sequences of BLAST hits
│   ├── combined_sequences.faa                   # Query + hit sequences merged
│   ├── aln/                                     # Alignment directory
│   │   ├── aligned_sequences.msa                # Raw MAFFT alignment
│   │   └── trimmed_alignment.msa                # TrimAl-trimmed alignment
│   ├── tree/                                    # Phylogenetic tree directory
│   │   ├── final_tree.treefile                  # Newick format tree
│   │   ├── final_tree.iqtree                    # IQ-TREE log file
│   │   ├── decorated_tree.png                   # Tree visualization with taxonomy
│   │   └── tree_stats.tab                       # Phylogenetic statistics table
│   ├── closest_neighbors.csv                    # Closest neighbors with distances
│   ├── closest_neighbors_with_taxonomy.csv      # Enhanced with NCBI taxonomy
│   ├── taxonomy_assignments.txt                 # Taxonomy in tabular format
│   ├── placement_results.json                   # Phylogenetic placement results
│   ├── placement_results.csv                    # Placement results in CSV format
│   └── itol/                                    # iTOL annotation files
│       ├── itol_labels.txt
│       ├── itol_colors.txt
│       └── itol_ranges.txt
├── combined_placement_results.json              # Aggregated results across all samples
├── log/                                         # Log directory (created in parent dir)
│   ├── <sample>_check_blast_output.log
│   ├── <sample>_taxonomy_assignment.log
│   ├── <sample>_decorate_tree.log
│   ├── <sample>_tree_stats.log
│   ├── <sample>_phylogenetic_placement.log
│   ├── <sample>_extract_hits_errors.log
│   └── nngenetree_*_{sample}_{jobid}.{out,err} # SLURM logs
└── <input_dir>_nngenetree_completion.log        # Final summary report
```

## Configuration Options

Edit `workflow/config.txt` to modify pipeline parameters:

**Core Settings:**
- `input_dir`: Directory containing .faa files (can be overridden via --config)
- `blast_db`: Path to DIAMOND/BLAST database (default: /clusterfs/jgi/scratch/science/mgs/nelli/databases/nr/nr)
- `blast_hits`: Number of BLAST hits to retrieve per query (default: 20)
- `closest_neighbors`: Number of closest neighbors to extract per query (default: 10)
- `query_filter`: Comma-separated list of query prefixes to filter (optional, e.g., "Hype,Klos")
- `itol_tax_level`: Taxonomy level for iTOL visualization (default: class; options: domain, phylum, class, order, family, genus, species)

**Resource Configuration:**
Resource allocations are specified per rule in the config file under the `resources` section:
```yaml
resources:
  run_diamond_blastp:
    threads: 8
    mem_mb: 32000
    time: "2:00:00"
  align_sequences:
    threads: 8
    mem_mb: 16000
    time: "1:00:00"
    disk_mb: 10000
  build_tree:
    threads: 8
    mem_mb: 16000
    time: "1:00:00"
  extract_hits:
    threads: 1
    mem_mb: 8000
    time: "0:30:00"
```

## Testing Pipeline Functionality

**Fast test with small database (recommended for development):**
```bash
# Clean any previous test runs
pixi run clean-test

# Run with small test database (completes in minutes)
pixi run test-fast

# Check outputs
ls -lh test_output/test1/tree/decorated_tree.png
ls -lh test_output/test2/placement_results.json
```

The test database (`test_db/test_reference.dmnd`) contains only 10 sequences from the example files, making BLAST searches nearly instantaneous. This is ideal for:
- Testing pipeline modifications
- Validating new features
- CI/CD integration
- Quick sanity checks

**Full test with nr database:**
```bash
# Clean any previous runs
pixi run clean

# Run on example data (test1.faa and test2.faa) - takes 1-2 hours
pixi run example-local

# Check completion log
cat example_nngenetree_completion.log

# Verify outputs exist
ls -lh example_nngenetree/test1/tree/decorated_tree.png
ls -lh example_nngenetree/test2/placement_results.json
```

**Once local test succeeds, test on SLURM:**
```bash
# Clean previous runs
pixi run clean

# Submit to SLURM cluster
pixi run example-slurm

# Monitor job status
squeue -u $USER

# Check logs as jobs complete
tail -f log/nngenetree_*.out
```

## Important Implementation Notes

1. **Phylogenetic neighbor extraction**: The pipeline uses two approaches:
   - `extract_closest_neighbors.py`: Finds N closest neighbors based on phylogenetic distance for all queries
   - `extract_phylogenetic_neighbors.py`: Filters neighbors by query prefix (e.g., Hype, Klos) and provides detailed taxonomy

2. **Path handling**: The pipeline uses absolute paths internally. When containerized, paths are remapped via `update_paths.py`.

3. **SLURM integration**: Default SLURM execution uses JGI-specific settings:
   - Account: `grp-org-sc-mgs`
   - Queue: `jgi_normal`
   - Job naming: `nngenetree.{rule}.{sample}`

4. **Local rules**: These rules always run on the head node (not submitted to SLURM):
   - `process_blast_results`, `check_blast_output`, `trim_alignment`, `combine_sequences`
   - `decorate_tree`, `calculate_tree_stats`, `extract_closest_neighbors`, `assign_taxonomy`, `all`

5. **Query filtering**: Use the `query_filter` config option to process only specific query sequences (useful for testing/debugging).

6. **Taxonomy fetching**: The `parse_closest_neighbors.py` script fetches taxonomy from NCBI Entrez API with retry logic and caching to handle rate limits.

7. **Tree visualization**: The pipeline generates:
   - PNG images with ETE3 for quick viewing
   - iTOL annotation files for interactive exploration at https://itol.embl.de/

8. **Dependencies**: All dependencies are managed by Pixi and installed automatically. No manual conda environment management needed.

9. **Phylogenetic placement**: The `extract_phylogenetic_placement` rule is hardcoded to look for query prefixes "Hype,Klos" - modify `workflow/Snakefile:511` to change this.

## Working with the Container (Optional)

⚠️ **Note**: Container functionality may not be fully tested/functional. Use Pixi-based execution instead.

The pipeline includes Singularity container support for reproducibility:

**Build container:**
```bash
cp workflow/scripts/update_paths.py container/scripts/
sudo singularity build nngenetree.sif container/Singularity.def
```

**Path mappings in container:**
- Input directory → `/data/input`
- Output directory → `/data/output`
- BLAST database → `/blast_db/`

The `container/scripts/update_paths.py` script automatically adjusts paths during container build.