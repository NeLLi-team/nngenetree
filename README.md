# NNGeneTree

[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](https://github.com/NeLLi-team/nngenetree)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

NNGeneTree builds a gene tree for each set of query proteins, finds the nearest neighbors of every query in that tree, and assigns NCBI taxonomy to the neighbors.

The pipeline runs on Nextflow, which provides resume and execution reports.

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [First-time setup](#first-time-setup)
- [Usage](#usage)
- [OrthoFinder Preprocessing](#orthofinder-preprocessing-optional)
- [Pipeline workflow](#pipeline-workflow)
- [Output description](#output-description)
- [Configuration](#configuration)
- [Scripts documentation](#scripts-documentation)
- [License](#license)
- [Contact](#contact)

---

## Overview

NNGeneTree places query proteins in a tree together with their closest database hits and reports the nearest neighbors by tree distance. Tree distance complements similarity search, which ranks hits by alignment score alone.

---

## Features

- Automated workflow from protein sequences to annotated gene trees
- Neighbor selection by phylogenetic distance
- NCBI taxonomy for every hit in the tree
- Distance statistics for each query
- Tree images and iTOL annotation files
- Nextflow execution reports for each run
- Local and SLURM execution
- Environment managed by Pixi

---

## Requirements

- [Pixi](https://pixi.sh/) (for environment and dependency management)
- [SLURM](https://slurm.schedmd.com/) (optional, for cluster execution)

The pipeline automatically manages all required tools through Pixi:

| Tool | Purpose |
|------|---------|
| Nextflow | Workflow management |
| DIAMOND | Fast protein similarity search |
| BLAST+ | Sequence extraction |
| MAFFT | Multiple sequence alignment |
| TrimAl | Alignment trimming |
| IQ-TREE | Phylogenetic tree construction |
| ETE Toolkit | Tree manipulation |
| BioPython | Sequence analysis and taxonomy retrieval |
| OpenJDK | Required for Nextflow |

---

## Installation

### Quick start

```bash
# Clone the repository
git clone https://github.com/username/nngenetree.git
cd nngenetree

# Install Pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Install all dependencies
pixi install
```

All dependencies are now installed and managed by Pixi.

---

## First-time setup

After installation, you must configure the database path for your system.

### Option 1: Configuration file (recommended)

```bash
# Copy the template
cp conf/local.config.template conf/local.config

# Edit with your settings
nano conf/local.config
```

Edit `conf/local.config` and set:

- `blast_db`: Path to your DIAMOND-formatted NR database (without `.dmnd` extension)
- `entrez_email`: Your email for NCBI Entrez API

Example:

```groovy
params {
    blast_db = '/path/to/nr/database'
    entrez_email = 'your.email@example.com'
}
```

### Option 2: Environment variables

```bash
# Add to your ~/.bashrc or ~/.zshrc
export NR_DATABASE=/path/to/your/nr/database
export ENTREZ_EMAIL=your.email@example.com
```

### SLURM configuration (optional)

If running on a SLURM cluster, add queue settings to `conf/local.config`:

```groovy
process {
    queue = 'your_queue_name'
    clusterOptions = '--qos=your_qos --account=your_account'
}
```

### Execution from anywhere (optional)

To run `nngenetree` from any directory:

```bash
# From the nngenetree repository directory
mkdir -p ~/bin
ln -s $(pwd)/nngenetree ~/bin/nngenetree

# Add ~/bin to PATH (if not already)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Test from any directory
cd /tmp && nngenetree test
```

Each task uses the tools in the repository's `.pixi/envs/default/bin` directory and unsets `MAFFT_BINARIES`. Your shell environment doesn't affect the run.

---

## Usage

### Running the pipeline

```bash
# Test mode with small built-in database
nngenetree test

# Run on your data locally
nngenetree my_input_dir local

# Run on SLURM cluster (default)
nngenetree my_input_dir slurm

# Extra arguments are forwarded to Nextflow
nngenetree my_data local --blast_hits 50 --blast_db /path/to/nr
```

If `nngenetree` is not on your `PATH`, run `bash nngenetree` instead.

### Nextflow features

- Resume after a failure with `-resume`
- HTML execution report with resource usage
- Timeline and DAG files for each run

---

## OrthoFinder preprocessing (optional)

NNGeneTree includes an optional preprocessing script for OrthoFinder integration. This runs separately before the main pipeline and allows you to:

1. Identify orthogroups across multiple genomes using OrthoFinder
2. Filter orthogroups by target protein IDs
3. Create FASTA files for each orthogroup
4. Use orthogroup FASTA files as input to NNGeneTree

### Prerequisites

Genome files must follow this header format:

```
>{genome_id}|{contig_id}_{protein_id}
```

Example:

```
>Hype|contig_50_1
MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTA...
```

### Running OrthoFinder preprocessing

```bash
# Activate the pixi environment
pixi shell

# Basic usage - process all orthogroups
python bin/orthofinder_preprocess.py \
  --genomes_faa_dir path/to/genomes \
  --output_dir path/to/output

# Filter for specific proteins
python bin/orthofinder_preprocess.py \
  --genomes_faa_dir path/to/genomes \
  --output_dir path/to/output \
  --target "target_substring"
```

### Complete workflow example

```bash
# Step 1: Run OrthoFinder preprocessing
pixi shell
python bin/orthofinder_preprocess.py \
  --genomes_faa_dir my_genomes/ \
  --output_dir my_orthogroups/ \
  --target "species1|contig_10_" \
  --threads 16
exit

# Step 2: Run NNGeneTree on the orthogroups
nngenetree my_orthogroups local
```

### OrthoFinder script options

| Option | Description |
|--------|-------------|
| `--genomes_faa_dir` | Directory containing genome FASTA files |
| `--output_dir` | Output directory for orthogroup FASTA files |
| `--target` | Comma-separated substrings to filter orthogroups |
| `--orthofinder_results` | Path to existing OrthoFinder results (skip re-running) |
| `--threads` | Number of threads for OrthoFinder (default: 16) |
| `--force` | Overwrite existing output directory |

---

## Pipeline workflow

```
INPUT FASTA FILES (.faa)
         |
         v
+---------------------+
| DIAMOND BLASTP      |  Fast protein similarity search (default: 20 hits/query)
+---------------------+
         |
         v
+---------------------+
| PROCESS             |  Extract unique subjects; skip samples with < 2 hits
+---------------------+
         |
         v
+---------------------+
| EXTRACT SEQUENCES   |  Retrieve hit sequences using blastdbcmd
+---------------------+
         |
         v
+---------------------+
| COMBINE SEQUENCES   |  Merge query + hit sequences
+---------------------+
         |
         v
+---------------------+
| MAFFT ALIGNMENT     |  Multiple sequence alignment
+---------------------+
         |
         v
+---------------------+
| TRIMAL TRIMMING     |  Remove poorly aligned regions (gap threshold: 0.1)
+---------------------+
         |
         v
+---------------------+
| IQTREE              |  Build phylogenetic tree (LG+G4 model)
+---------------------+
         |
         +---------------------------+
         |                           |
         v                           v
+-----------------+     +------------------------+
| EXTRACT         |     | PHYLOGENETIC           |
| NEIGHBORS       |     | PLACEMENT              |
| (N=10 default)  |     +------------------------+
+-----------------+
         |
         v
+---------------------+
| ASSIGN TAXONOMY     |  Fetch NCBI taxonomy via Entrez API
+---------------------+
         |
         v
+---------------------+
| DECORATE TREE       |  Generate PNG visualizations with taxonomy
+---------------------+
         |
         v
+---------------------+
| TREE STATISTICS     |  Calculate phylogenetic statistics
+---------------------+
         |
         v
+---------------------+
| COMBINE RESULTS     |  Aggregate placement results to JSON
+---------------------+
         |
         v
     FINAL OUTPUT
```

---

## Output description

The pipeline writes results to `<input_dir>_output/`. For each input FASTA file:

### Sample directory structure

```
<sample>/
├── blast_results.m8              # DIAMOND BLAST tabular output
├── unique_subjects.txt           # List of unique hit accessions
├── extracted_hits.faa            # Sequences of BLAST hits
├── combined_sequences.faa        # Combined query and hit sequences
├── aln/
│   ├── aligned_sequences.msa     # Raw MAFFT alignment
│   └── trimmed_alignment.msa     # TrimAl-trimmed alignment
├── tree/
│   ├── final_tree.treefile       # Newick tree file
│   ├── final_tree.iqtree         # IQ-TREE log file
│   ├── decorated_tree.png        # Visualization with taxonomy
│   └── tree_stats.tab            # Tree statistics (one row per input query)
├── closest_neighbors.csv         # Neighbors with phylogenetic distances
├── closest_neighbors_with_taxonomy.csv  # Enhanced CSV with NCBI taxonomy
├── taxonomy_assignments.txt      # Taxonomy information (tabular); OG column is the sample name
├── placement_results.json        # Neighbor details with NCBI Entrez taxonomy
├── placement_results.csv         # Placement results (CSV format)
└── itol/                         # Interactive Tree of Life files
    ├── itol_labels.txt
    ├── itol_branch_colors.txt
    ├── itol_query_circles.txt
    └── itol_colorstrip.txt
```

The pipeline skips samples with fewer than 2 unique DIAMOND subjects, logs a warning, and continues with the remaining samples.

### Aggregated output

- `combined_placement_results.json`: All placement results across samples

---

## Configuration

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `input_dir` | Directory containing input .faa files | `test` |
| `output_dir` | Override default output directory | `{input_dir}_output` |
| `blast_db` | Path to BLAST/DIAMOND database | (from local.config) |
| `blast_hits` | Number of BLAST hits per query | 5 |
| `min_hits` | Warn when a query has fewer BLAST hits than this | 5 |
| `diamond_sensitivity` | Extra DIAMOND flag, for example `--sensitive` | (empty: fast mode) |
| `self_hit_threshold` | Distance below which a neighbor is treated as a self-hit | 0.001 |
| `entrez_email` | Email for NCBI Entrez; exported as `ENTREZ_EMAIL` to tasks | (from local.config) |
| `closest_neighbors` | Number of closest neighbors to extract | 5 |
| `query_filter` | Comma-separated query prefixes to filter | - |
| `query_prefixes` | Prefixes for phylogenetic placement | `Hype,Klos` |
| `num_neighbors_placement` | Neighbors for placement | 5 |
| `itol_tax_level` | Taxonomy level for iTOL | `class` |

### Resource configuration

```groovy
params {
  resources {
    run_diamond_blastp {
      threads = 4
      mem_mb = 8000
      time = '10m'
    }
    // Additional resources in nextflow.config
  }
}
```

### Execution profiles

| Profile | Description |
|---------|-------------|
| `standard` | Default (base configuration) |
| `local` | Local execution with 16 cores |
| `slurm` | SLURM cluster execution |
| `test` | Test profile with small database |

### Override configuration

```bash
# Use custom config file
nextflow run main.nf -c my_custom_config.txt

# Override specific parameters
nextflow run main.nf --input_dir mydata --blast_hits 50

# Override multiple parameters
nextflow run main.nf \
  --input_dir mydata \
  --blast_db /path/to/custom/db \
  --closest_neighbors 20 \
  --output_dir custom_output
```

---

## Pixi tasks

View all tasks with `pixi task list`:

| Task | Description |
|------|-------------|
| `test` | Run test pipeline with verification |
| `clean` | Clean test output and logs |
| `clean-all` | Clean all output directories |
| `shell` | Start interactive shell |
| `lint` | Lint Python scripts (dev env) |
| `format` | Format Python scripts (dev env) |

---

## Scripts documentation

All scripts are in `bin/` and available in PATH when using `pixi shell`.

### parse_closest_neighbors.py

Process closest neighbors CSV files and add NCBI taxonomy:

```bash
python bin/parse_closest_neighbors.py -d <directory> --subjects <unique_subjects.txt> --og <sample> -o <output_file>
```

### extract_closest_neighbors.py

Extract closest neighbors from a phylogenetic tree:

```bash
python bin/extract_closest_neighbors.py \
  --tree <tree_file> \
  --query <query_file> \
  --subjects <subjects_file> \
  --output <output_file> \
  --num_neighbors <N> \
  --self_hit_threshold <distance>
```

### extract_phylogenetic_neighbors.py

Extract phylogenetic neighbors with taxonomy for specific query prefixes:

```bash
python bin/extract_phylogenetic_neighbors.py \
  --tree <tree_file> \
  --query-prefixes <prefixes> \
  --taxonomy <taxonomy_assignments.txt> \
  --output-json <json_file> \
  --output-csv <csv_file> \
  --num-neighbors <N>
```

| Option | Description |
|--------|-------------|
| `--tree` | Path to tree file |
| `--query-prefixes` | Comma-separated query prefixes (e.g., "Hype,Klos") |
| `--taxonomy` | Path to `taxonomy_assignments.txt` (required) |
| `--output-json` | Output JSON file |
| `--output-csv` | Output CSV file |
| `--num-neighbors` | Neighbors per query (default: 5) |
| `--self-hit-threshold` | Distance threshold for self-hits (default: 0.001) |

### decorate_tree.py

Create tree visualizations with taxonomy:

```bash
python bin/decorate_tree.py <tree_file> <taxonomy_file> <query_file> <output_png> <itol_prefix>
```

### tree_stats.py

Calculate phylogenetic statistics:

```bash
python bin/tree_stats.py <tree_file> <taxonomy_file> <query_file> <output_file>
```

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Contact

For questions, issues, or contributions, please open an issue on the GitHub repository.

---

*Developed at Joint Genome Institute (JGI)*
