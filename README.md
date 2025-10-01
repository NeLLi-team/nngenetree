# 🧬 NNGeneTree 🌳

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/NeLLi-team/nngenetree) [![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**NNGeneTree** is a phylogenetic analysis and taxonomic classification pipeline for protein sequences. It builds gene trees and finds the nearest neighbors of query sequences in the phylogenetic context, assigning taxonomy information for comprehensive evolutionary analysis.

**Built with Nextflow** - a dataflow-oriented workflow engine with built-in resume and reporting capabilities.

## 🔍 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Container Usage](#-container-usage)
- [Usage](#-usage)
- [Pipeline Workflow](#-pipeline-workflow)
- [Output Description](#-output-description)
- [Configuration](#-configuration)
- [Scripts Documentation](#-scripts-documentation)
- [License](#-license)
- [Contact](#-contact)

## 📋 Overview

NNGeneTree leverages the power of phylogenetic analysis to place query protein sequences in an evolutionary context and identify their closest neighbors in sequence space. This approach provides valuable insights into the functional and evolutionary relationships between proteins, complementing traditional similarity-based annotation methods.

## ✨ Features

- 🔄 Automated workflow from protein sequences to annotated phylogenetic trees
- 🧠 Smart selection of closest neighbors based on phylogenetic distance
- 🔍 NCBI taxonomy integration for comprehensive classification
- 📊 Statistical analysis of phylogenetic relationships
- 🎨 Visually appealing tree visualizations with taxonomic annotations
- 📝 Detailed logging and reports for each analysis step
- 🖥️ Supports both local execution and HPC cluster deployment (SLURM)
- 🧩 Modular design with Pixi package management

## 📦 Requirements

- [Pixi](https://pixi.sh/) (for environment and dependency management)
- [SLURM](https://slurm.schedmd.com/) (optional, for cluster execution)

The pipeline automatically manages all required tools through Pixi:
- Nextflow (workflow management)
- DIAMOND (fast protein similarity search)
- BLAST+ (sequence extraction)
- MAFFT (multiple sequence alignment)
- TrimAl (alignment trimming)
- IQ-TREE (phylogenetic tree construction)
- ETE Toolkit (tree manipulation)
- BioPython (sequence analysis and taxonomy retrieval)
- OpenJDK (for Nextflow)

## 💻 Installation

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

That's it! All dependencies are now installed and managed by Pixi.

### Execution from Anywhere (Optional)

To run `nngenetree` from any directory on your system, create a symbolic link to your PATH:

```bash
# From the nngenetree repository directory
mkdir -p ~/bin
ln -s $(pwd)/nngenetree ~/bin/nngenetree

# Add ~/bin to PATH (if not already in your PATH)
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Test it works from any directory
cd /tmp
nngenetree test
```

Once installed, you can run `nngenetree` from any location and it will automatically find the repository and handle paths correctly.

## 🚀 Usage

### Running the Pipeline

```bash
# Fast test with small test database (includes verification)
nngenetree test
# or: bash nngenetree test

# Run on your data locally
nngenetree my_input_dir local
# or: bash nngenetree my_input_dir local

# SLURM cluster execution (default)
nngenetree my_input_dir slurm
# or: bash nngenetree my_input_dir slurm
```

**Note:** Use `nngenetree` directly if you've installed it as a system command (see Installation section), otherwise use `bash nngenetree`.

### Nextflow Features

- **Automatic resume on failure** (`-resume`)
- **HTML execution reports** with resource usage
- **Built-in timeline and DAG visualizations**
- **Cloud-ready** (AWS, Azure, Google Cloud)

For complete Nextflow documentation, see [NEXTFLOW_README.md](NEXTFLOW_README.md).

## 🧬 OrthoFinder Preprocessing (Optional)

### Overview

NNGeneTree includes an **optional preprocessing script** for OrthoFinder integration. This is run **separately before** the main Nextflow pipeline and allows you to:
1. Identify orthogroups across multiple genomes using OrthoFinder
2. Filter orthogroups by target protein IDs
3. Automatically create FASTA files for each orthogroup
4. Use the orthogroup FASTA files as input to the NNGeneTree Nextflow pipeline

**Note:** OrthoFinder preprocessing is NOT part of the Nextflow pipeline. It's a standalone preparatory step.

### Prerequisites

Your genome files must follow this header format:
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
# Activate the pixi environment first
pixi shell

# Basic usage - process all orthogroups
python bin/orthofinder_preprocess.py \
  --genomes_faa_dir path/to/genomes \
  --output_dir path/to/output

# Filter orthogroups containing specific proteins
python bin/orthofinder_preprocess.py \
  --genomes_faa_dir path/to/genomes \
  --output_dir path/to/output \
  --target "target_substring"
```

### Complete Workflow Example

Process genomes through OrthoFinder and then run NNGeneTree:

```bash
# Step 1: Run OrthoFinder preprocessing
pixi shell
python bin/orthofinder_preprocess.py \
  --genomes_faa_dir my_genomes/ \
  --output_dir my_orthogroups/ \
  --target "species1|contig_10_" \
  --threads 16
exit

# Step 2: Run NNGeneTree Nextflow pipeline on the orthogroups
nngenetree my_orthogroups local
```

### OrthoFinder Script Options

The preprocessing script (`bin/orthofinder_preprocess.py`) supports:
- `--genomes_faa_dir`: Directory containing genome FASTA files
- `--output_dir`: Output directory for orthogroup FASTA files
- `--target`: Comma-separated list of substrings to filter orthogroups
- `--orthofinder_results`: Path to existing OrthoFinder results (skip re-running)
- `--threads`: Number of threads for OrthoFinder (default: 16)
- `--force`: Overwrite existing output directory

## 🔄 Pipeline Workflow

```
INPUT FASTA FILES (.faa)
      │
      ▼
┌─────────────────────┐
│ DIAMOND BLASTP      │ Fast protein similarity search (default: 20 hits per query)
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ PROCESS & VALIDATE  │ Extract unique subjects and validate output
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ EXTRACT SEQUENCES   │ Retrieve hit sequences using blastdbcmd
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ COMBINE SEQUENCES   │ Merge query + hit sequences
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ MAFFT ALIGNMENT     │ Multiple sequence alignment
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ TRIMAL TRIMMING     │ Remove poorly aligned regions (gap threshold: 0.1)
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ IQTREE              │ Build phylogenetic tree (LG+G4 model)
└─────┬───────────────┘
      │
      ├──────────────────────┐
      ▼                      ▼
┌─────────────────┐   ┌──────────────────────┐
│ EXTRACT         │   │ PHYLOGENETIC         │ Extract top 5 neighbors for
│ NEIGHBORS       │   │ PLACEMENT            │ specific query prefixes
│ (N=10 default)  │   └──────────────────────┘
└─────┬───────────┘
      │
      ▼
┌─────────────────────┐
│ ASSIGN TAXONOMY     │ Fetch NCBI taxonomy via Entrez API
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ DECORATE TREE       │ Generate PNG visualizations with taxonomy
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ TREE STATISTICS     │ Calculate phylogenetic statistics
└─────┬───────────────┘
      │
      ▼
┌─────────────────────┐
│ COMBINE RESULTS     │ Aggregate placement results to JSON
└─────────────────────┘
      │
      ▼
  FINAL OUTPUT
  (Trees, taxonomy, statistics, placement results)
```

## 📂 Output Description

Results are saved in a directory named `<input_dir>_output/`. For each input FASTA file, you'll find:

- `<sample>/`: Sample-specific results including:
  - `blast_results.m8`: DIAMOND BLAST tabular output
  - `unique_subjects.txt`: List of unique hit accessions
  - `check_blast_output.done`: Validation checkpoint
  - `extracted_hits.faa`: Sequences of BLAST hits
  - `combined_sequences.faa`: Combined query and hit sequences
  - `aln/`: Alignment files
    - `aligned_sequences.msa`: Raw MAFFT alignment
    - `trimmed_alignment.msa`: TrimAl-trimmed alignment
  - `tree/`: Phylogenetic trees
    - `final_tree.treefile`: Newick tree file
    - `final_tree.iqtree`: IQ-TREE log file
    - `decorated_tree.png`: Visualization with taxonomy
    - `tree_stats.tab`: Statistics about the tree
  - `closest_neighbors.csv`: Closest neighbors with phylogenetic distances
  - `closest_neighbors_with_taxonomy.csv`: Enhanced CSV with NCBI taxonomy
  - `taxonomy_assignments.txt`: Taxonomy information in tabular format
  - `placement_results.json`: Phylogenetic placement results with detailed neighbor info
  - `placement_results.csv`: Placement results in CSV format
  - `itol/`: Files for Interactive Tree of Life visualization
    - `itol_labels.txt`
    - `itol_colors.txt`
    - `itol_ranges.txt`
- `combined_placement_results.json`: Aggregated placement results across all samples

A comprehensive log file (`<input_dir>_output_completion.log`) contains a summary of the analysis, including:
- Pipeline version and runtime information
- BLAST hit counts for each sample
- Taxonomy distribution statistics (domains, phyla, classes, orders, families, genera)
- Tree generation status

## ⚙️ Configuration

### Nextflow Configuration

Edit `nextflow.config` or create a custom config file:

**Basic Parameters:**
- `input_dir`: Directory containing input .faa files (default: 'test')
- `output_dir`: Override default output directory (default: `{input_dir}_output`)
- `blast_db`: Path to BLAST/DIAMOND database (default: test database for testing)
- `blast_hits`: Number of BLAST hits to retrieve per query (default: 5)
- `closest_neighbors`: Number of closest neighbors to extract per query (default: 5)
- `query_filter`: Optional comma-separated list of query prefixes to filter
- `query_prefixes`: Prefixes for phylogenetic placement (default: 'Hype,Klos')
- `num_neighbors_placement`: Number of neighbors for placement (default: 5)
- `itol_tax_level`: Taxonomy level for iTOL visualization (default: class; options: domain, phylum, class, order, family, genus, species)

**Resource Configuration:**
```groovy
params {
  resources {
    run_diamond_blastp {
      threads = 4
      mem_mb = 8000
      time = '10m'
    }
    // Additional resource configurations in nextflow.config
  }
}
```

**Execution Profiles:**
- `standard`: Default profile (base configuration)
- `local`: Local execution with 16 cores
- `slurm`: SLURM cluster execution
- `test`: Test profile with small database

### Override Configuration

You can override any config parameter in `nextflow.config` or via command line:

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

See [NEXTFLOW_README.md](NEXTFLOW_README.md) for more configuration options.

## 🛠️ Available Pixi Tasks

View all available tasks with `pixi task list`. Key tasks include:

| Task | Description | Command |
|------|-------------|---------|
| `test` | Run test pipeline with verification | `pixi run test` |
| `clean` | Clean test output and logs | `pixi run clean` |
| `clean-all` | Clean all output directories | `pixi run clean-all` |
| `shell` | Start interactive shell | `pixi shell` |
| `lint` | Lint Python scripts | `pixi run lint` (dev env) |
| `format` | Format Python scripts | `pixi run format` (dev env) |

**Note:** For running on your own data, use: `nngenetree <input_dir> [local|slurm]` (or `bash nngenetree` if not installed as system command)

## 📝 Scripts Documentation

All scripts are located in the `bin/` directory and are automatically available in your PATH when using `pixi shell`.

### parse_closest_neighbors.py

Processes closest neighbors CSV files and adds NCBI taxonomy information:

```bash
python bin/parse_closest_neighbors.py -d <directory> -o <output_file>
```

- `-d, --base-dir`: Base directory containing CSV files
- `-o, --output`: Output summary file path (optional)

### extract_closest_neighbors.py

Extracts closest neighbors from a phylogenetic tree:

```bash
python bin/extract_closest_neighbors.py --tree <tree_file> --query <query_file> --subjects <subjects_file> --output <output_file> --num_neighbors <N>
```

### extract_phylogenetic_neighbors.py

Extracts phylogenetic neighbors with taxonomy for specific query prefixes:

```bash
python bin/extract_phylogenetic_neighbors.py --tree <tree_file> --query-prefixes <prefixes> --output-json <json_file> --output-csv <csv_file> --num-neighbors <N>
```

- `--tree`: Path to tree file
- `--query-prefixes`: Comma-separated list of query prefixes (e.g., "Hype,Klos")
- `--output-json`: Output JSON file with detailed neighbor information
- `--output-csv`: Output CSV file for pipeline compatibility
- `--num-neighbors`: Number of neighbors to extract per query (default: 5)
- `--self-hit-threshold`: Distance threshold for self-hits (default: 0.001)

### decorate_tree.py

Creates visualizations of the phylogenetic trees with taxonomy information:

```bash
python bin/decorate_tree.py <tree_file> <taxonomy_file> <query_file> <output_png> <itol_prefix>
```

### tree_stats.py

Calculates statistics about the phylogenetic relationships:

```bash
python bin/tree_stats.py <tree_file> <taxonomy_file> <query_file> <output_file>
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

For questions, issues, or contributions, please open an issue on the GitHub repository or contact the maintainers.

---

📊 **Developed at Joint Genome Institute (JGI)** 🧪
