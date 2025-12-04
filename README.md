# NNGeneTree

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/NeLLi-team/nngenetree)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**NNGeneTree** is a phylogenetic analysis and taxonomic classification pipeline for protein sequences. It builds gene trees and finds the nearest neighbors of query sequences in the phylogenetic context, assigning taxonomy information for comprehensive evolutionary analysis.

Built with **Nextflow** - a dataflow-oriented workflow engine with built-in resume and reporting capabilities.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [Usage](#usage)
- [OrthoFinder Preprocessing](#orthofinder-preprocessing-optional)
- [Pipeline Workflow](#pipeline-workflow)
- [Output Description](#output-description)
- [Configuration](#configuration)
- [Scripts Documentation](#scripts-documentation)
- [License](#license)
- [Contact](#contact)

---

## Overview

NNGeneTree leverages the power of phylogenetic analysis to place query protein sequences in an evolutionary context and identify their closest neighbors in sequence space. This approach provides valuable insights into the functional and evolutionary relationships between proteins, complementing traditional similarity-based annotation methods.

---

## Features

- **Automated workflow** from protein sequences to annotated phylogenetic trees
- **Smart neighbor selection** based on phylogenetic distance
- **NCBI taxonomy integration** for comprehensive classification
- **Statistical analysis** of phylogenetic relationships
- **Tree visualizations** with taxonomic annotations
- **Detailed logging and reports** for each analysis step
- **Local and HPC support** (SLURM cluster deployment)
- **Modular design** with Pixi package management

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

### Quick Start

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

## First-Time Setup

After installation, you must configure the database path for your system.

### Option 1: Configuration File (Recommended)

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

### Option 2: Environment Variables

```bash
# Add to your ~/.bashrc or ~/.zshrc
export NR_DATABASE=/path/to/your/nr/database
export ENTREZ_EMAIL=your.email@example.com
```

### SLURM Configuration (Optional)

If running on a SLURM cluster, add queue settings to `conf/local.config`:

```groovy
process {
    queue = 'your_queue_name'
    clusterOptions = '--qos=your_qos --account=your_account'
}
```

### Execution from Anywhere (Optional)

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

---

## Usage

### Running the Pipeline

```bash
# Test mode with small built-in database
nngenetree test

# Run on your data locally
nngenetree my_input_dir local

# Run on SLURM cluster (default)
nngenetree my_input_dir slurm
```

**Note:** Use `nngenetree` directly if installed to PATH, otherwise use `bash nngenetree`.

### Nextflow Features

- **Automatic resume on failure** (`-resume`)
- **HTML execution reports** with resource usage
- **Built-in timeline and DAG visualizations**
- **Cloud-ready** (AWS, Azure, Google Cloud)

---

## OrthoFinder Preprocessing (Optional)

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

### Running OrthoFinder Preprocessing

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

### Complete Workflow Example

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

### OrthoFinder Script Options

| Option | Description |
|--------|-------------|
| `--genomes_faa_dir` | Directory containing genome FASTA files |
| `--output_dir` | Output directory for orthogroup FASTA files |
| `--target` | Comma-separated substrings to filter orthogroups |
| `--orthofinder_results` | Path to existing OrthoFinder results (skip re-running) |
| `--threads` | Number of threads for OrthoFinder (default: 16) |
| `--force` | Overwrite existing output directory |

---

## Pipeline Workflow

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
| PROCESS & VALIDATE  |  Extract unique subjects and validate output
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

## Output Description

Results are saved in `<input_dir>_output/`. For each input FASTA file:

### Sample Directory Structure

```
<sample>/
├── blast_results.m8              # DIAMOND BLAST tabular output
├── unique_subjects.txt           # List of unique hit accessions
├── check_blast_output.done       # Validation checkpoint
├── extracted_hits.faa            # Sequences of BLAST hits
├── combined_sequences.faa        # Combined query and hit sequences
├── aln/
│   ├── aligned_sequences.msa     # Raw MAFFT alignment
│   └── trimmed_alignment.msa     # TrimAl-trimmed alignment
├── tree/
│   ├── final_tree.treefile       # Newick tree file
│   ├── final_tree.iqtree         # IQ-TREE log file
│   ├── decorated_tree.png        # Visualization with taxonomy
│   └── tree_stats.tab            # Tree statistics
├── closest_neighbors.csv         # Neighbors with phylogenetic distances
├── closest_neighbors_with_taxonomy.csv  # Enhanced CSV with NCBI taxonomy
├── taxonomy_assignments.txt      # Taxonomy information (tabular)
├── placement_results.json        # Detailed neighbor info
├── placement_results.csv         # Placement results (CSV format)
└── itol/                         # Interactive Tree of Life files
    ├── itol_labels.txt
    ├── itol_colors.txt
    └── itol_ranges.txt
```

### Aggregated Output

- `combined_placement_results.json`: All placement results across samples

### Completion Log

A log file (`<input_dir>_output_completion.log`) contains:

- Pipeline version and runtime information
- BLAST hit counts for each sample
- Taxonomy distribution statistics (domains, phyla, classes, orders, families, genera)
- Tree generation status

---

## Configuration

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `input_dir` | Directory containing input .faa files | `test` |
| `output_dir` | Override default output directory | `{input_dir}_output` |
| `blast_db` | Path to BLAST/DIAMOND database | (from local.config) |
| `blast_hits` | Number of BLAST hits per query | 5 |
| `closest_neighbors` | Number of closest neighbors to extract | 5 |
| `query_filter` | Comma-separated query prefixes to filter | - |
| `query_prefixes` | Prefixes for phylogenetic placement | `Hype,Klos` |
| `num_neighbors_placement` | Neighbors for placement | 5 |
| `itol_tax_level` | Taxonomy level for iTOL | `class` |

### Resource Configuration

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

### Execution Profiles

| Profile | Description |
|---------|-------------|
| `standard` | Default (base configuration) |
| `local` | Local execution with 16 cores |
| `slurm` | SLURM cluster execution |
| `test` | Test profile with small database |

### Override Configuration

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

## Pixi Tasks

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

## Scripts Documentation

All scripts are in `bin/` and available in PATH when using `pixi shell`.

### parse_closest_neighbors.py

Process closest neighbors CSV files and add NCBI taxonomy:

```bash
python bin/parse_closest_neighbors.py -d <directory> -o <output_file>
```

### extract_closest_neighbors.py

Extract closest neighbors from a phylogenetic tree:

```bash
python bin/extract_closest_neighbors.py \
  --tree <tree_file> \
  --query <query_file> \
  --subjects <subjects_file> \
  --output <output_file> \
  --num_neighbors <N>
```

### extract_phylogenetic_neighbors.py

Extract phylogenetic neighbors with taxonomy for specific query prefixes:

```bash
python bin/extract_phylogenetic_neighbors.py \
  --tree <tree_file> \
  --query-prefixes <prefixes> \
  --output-json <json_file> \
  --output-csv <csv_file> \
  --num-neighbors <N>
```

| Option | Description |
|--------|-------------|
| `--tree` | Path to tree file |
| `--query-prefixes` | Comma-separated query prefixes (e.g., "Hype,Klos") |
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
