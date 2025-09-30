# 🧬 NNGeneTree 🌳

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/NeLLi-team/nngenetree) [![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**NNGeneTree** is a Snakemake pipeline for phylogenetic analysis and taxonomic classification of protein sequences. It builds gene trees and finds the nearest neighbors of query sequences in the phylogenetic context, assigning taxonomy information for comprehensive evolutionary analysis.

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
- Snakemake (workflow management)
- DIAMOND (fast protein similarity search)
- BLAST+ (sequence extraction)
- MAFFT (multiple sequence alignment)
- TrimAl (alignment trimming)
- IQ-TREE (phylogenetic tree construction)
- ETE Toolkit (tree manipulation)
- BioPython (sequence analysis and taxonomy retrieval)

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

## 🚀 Usage

### Running with Pixi (Recommended)

```bash
# Fast test with small test database (completes in minutes)
# Output: test_nngenetree/
pixi run test-fast

# Run on your own data locally (16 cores)
# Output: mydata_nngenetree/
snakemake --cores 16 --config input_dir=mydata

# Run with custom config file
snakemake --cores 16 --configfile my_config.txt

# Override specific config parameters
snakemake --cores 16 --config input_dir=mydata blast_hits=50 closest_neighbors=20

# Dry run (preview what will be executed)
pixi run dry-run

# Clean output files
pixi run clean
```

### Traditional Shell Script

```bash
# Local execution (16 cores)
bash run.sh <input_directory> true

# SLURM cluster execution
bash run.sh <input_directory>
```

## 🧬 OrthoFinder Integration

### Overview

NNGeneTree now includes integrated support for OrthoFinder preprocessing, allowing you to:
1. Identify orthogroups across multiple genomes
2. Filter orthogroups by target protein IDs
3. Automatically create FASTA files for each orthogroup
4. Process orthogroups through the NNGeneTree pipeline

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
python workflow/scripts/orthofinder_preprocess.py \
  --genomes_faa_dir path/to/genomes \
  --output_dir path/to/output

# Filter orthogroups containing specific proteins
python workflow/scripts/orthofinder_preprocess.py \
  --genomes_faa_dir path/to/genomes \
  --output_dir path/to/output \
  --target "target_substring"
```

### Complete Workflow Example

Process genomes through OrthoFinder and then run NNGeneTree:

```bash
# Step 1: Run OrthoFinder preprocessing
pixi run python workflow/scripts/orthofinder_preprocess.py \
  --genomes_faa_dir my_genomes/ \
  --output_dir my_orthogroups/ \
  --target "species1|contig_10_" \
  --threads 16

# Step 2: Run NNGeneTree on the orthogroups
pixi run run-local my_orthogroups/
```

### OrthoFinder Script Options

The preprocessing script (`workflow/scripts/orthofinder_preprocess.py`) supports:
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

Results are saved in a directory named `<input_dir>_nngenetree/`. For each input FASTA file, you'll find:

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

A comprehensive log file (`<input_dir>_nngenetree_completion.log`) contains a summary of the analysis, including:
- Pipeline version and runtime information
- BLAST hit counts for each sample
- Taxonomy distribution statistics (domains, phyla, classes, orders, families, genera)
- Tree generation status

## ⚙️ Configuration

### Config File Options

Edit `workflow/config.txt` or create your own config file:

**Basic Parameters:**
- `input_dir`: Directory containing input .faa files
- `output_dir`: Override default output directory (default: `{input_dir}_nngenetree`)
- `blast_db`: Path to BLAST/DIAMOND database (default: `/clusterfs/jgi/scratch/science/mgs/nelli/databases/nr/nr`)
- `blast_hits`: Number of BLAST hits to retrieve per query (default: 20)
- `closest_neighbors`: Number of closest neighbors to extract per query (default: 10)
- `query_filter`: Optional comma-separated list of query prefixes to filter
- `itol_tax_level`: Taxonomy level for iTOL visualization (default: class; options: domain, phylum, class, order, family, genus, species)

**Resource Configuration:**
```yaml
resources:
  run_diamond_blastp:
    threads: 8
    mem_mb: 32000
    time: "2:00:00"
  # Additional resource configurations...
```

### Override Configuration

You can override any config parameter on the command line:

```bash
# Use custom config file
snakemake --configfile my_custom_config.txt --cores 16

# Override specific parameters
snakemake --cores 16 --config input_dir=mydata blast_hits=50

# Override multiple parameters
snakemake --cores 16 --config \
  input_dir=mydata \
  blast_db=/path/to/custom/db \
  closest_neighbors=20 \
  output_dir=custom_output
```

## 🛠️ Available Pixi Tasks

View all available tasks with `pixi task list`. Key tasks include:

| Task | Description | Command |
|------|-------------|---------|
| `test-fast` | Fast test with small database | `pixi run test-fast` |
| `test-dry` | Dry run with test configuration | `pixi run test-dry` |
| `dry-run` | Preview what will be executed | `pixi run dry-run` |
| `clean` | Clean test output files | `pixi run clean` |
| `clean-all` | Clean all output directories | `pixi run clean-all` |
| `shell` | Start interactive shell | `pixi shell` |
| `lint` | Lint Python scripts | `pixi run lint` (dev env) |
| `format` | Format Python scripts | `pixi run format` (dev env) |

**Note:** For running on your own data, use snakemake directly (see Usage section above)

## 📝 Scripts Documentation

### parse_closest_neighbors.py

Processes closest neighbors CSV files and adds NCBI taxonomy information:

```bash
python workflow/scripts/parse_closest_neighbors.py -d <directory> -o <output_file>
```

- `-d, --base-dir`: Base directory containing CSV files
- `-o, --output`: Output summary file path (optional)

### extract_closest_neighbors.py

Extracts closest neighbors from a phylogenetic tree:

```bash
python workflow/scripts/extract_closest_neighbors.py --tree <tree_file> --query <query_file> --subjects <subjects_file> --output <output_file> --num_neighbors <N>
```

### extract_phylogenetic_neighbors.py

Extracts phylogenetic neighbors with taxonomy for specific query prefixes:

```bash
python workflow/scripts/extract_phylogenetic_neighbors.py --tree <tree_file> --query-prefixes <prefixes> --output-json <json_file> --output-csv <csv_file> --num-neighbors <N>
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
python workflow/scripts/decorate_tree.py <tree_file> <taxonomy_file> <query_file> <output_png> <itol_prefix>
```

### tree_stats.py

Calculates statistics about the phylogenetic relationships:

```bash
python workflow/scripts/tree_stats.py <tree_file> <taxonomy_file> <query_file> <output_file>
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

For questions, issues, or contributions, please open an issue on the GitHub repository or contact the maintainers.

---

📊 **Developed at Joint Genome Institute (JGI)** 🧪
