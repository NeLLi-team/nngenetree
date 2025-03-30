# 🧬 NNGeneTree 🌳

[![Version](https://img.shields.io/badge/version-0.9.0-blue.svg)](https://github.com/username/nngenetree) [![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**NNGeneTree** is a Snakemake pipeline for phylogenetic analysis and taxonomic classification of protein sequences. It builds gene trees and finds the nearest neighbors of query sequences in the phylogenetic context, assigning taxonomy information for comprehensive evolutionary analysis.

## 🔍 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
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
- 🧩 Modular design with conda environment management

## 📦 Requirements

- [Conda/Miniconda](https://docs.conda.io/en/latest/miniconda.html) (for environment management)
- [Snakemake](https://snakemake.readthedocs.io/en/stable/) (v7.0+ recommended)
- [SLURM](https://slurm.schedmd.com/) (optional, for cluster execution)

The pipeline will automatically set up all required tools through conda environments:
- DIAMOND (for fast protein similarity search)
- BLAST+ (for sequence extraction)
- MAFFT (for multiple sequence alignment)
- TrimAl (for alignment trimming)
- IQ-TREE (for phylogenetic tree construction)
- ETE Toolkit (for tree manipulation)
- BioPython (for sequence analysis and taxonomy retrieval)

## 💻 Installation

No installation is required. Simply clone the repository and ensure you have Conda and Snakemake available:

```bash
git clone https://github.com/username/nngenetree.git
cd nngenetree
```

## 🚀 Usage

### Basic Usage

1. Place your protein sequences (in FASTA format with `.faa` extension) in a directory (e.g., `example/`).

2. Run the pipeline:

```bash
bash run.sh example
```

This will execute the pipeline on the SLURM cluster using the files in the `example/` directory.

### Local Execution

To run the pipeline locally without a SLURM cluster:

```bash
bash run.sh example true
```

### Custom Configuration

Modify the configuration in `workflow/config.txt` to set parameters such as:
- `input_dir`: Directory containing your FASTA files
- `blast_db`: Path to your BLAST database
- `blast_hits`: Number of BLAST hits to retrieve
- `closest_neighbors`: Number of closest neighbors to extract per query
- `query_filter`: Optional comma-separated list of query prefixes to filter by

## 🔄 Pipeline Workflow

```
INPUT FASTA FILES
      │
      ▼
┌─────────────┐
│ DIAMOND     │ Fast protein similarity search against reference database
│ BLASTP      │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ EXTRACT     │ Retrieve sequences of BLAST hits from the database
│ SEQUENCES   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ SEQUENCE    │ Align query sequences with hits using MAFFT
│ ALIGNMENT   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ TRIM        │ Remove poorly aligned regions with TrimAl
│ ALIGNMENT   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ BUILD       │ Construct phylogenetic tree using IQ-TREE
│ TREE        │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ EXTRACT     │ Identify the closest neighbors in the phylogenetic tree
│ NEIGHBORS   │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ ASSIGN      │ Retrieve taxonomy information from NCBI
│ TAXONOMY    │
└─────┬───────┘
      │
      ▼
┌─────────────┐
│ VISUALIZE   │ Generate decorated trees and statistics
│ TREES       │
└─────┬───────┘
      │
      ▼
  FINAL OUTPUT
```

## 📂 Output Description

Results are saved in a directory named `<input_dir>_nngenetree/`. For each input FASTA file, you'll find:

- `blast_results/`: DIAMOND BLAST search results (tabular format)
- `<sample>/`: Sample-specific results including:
  - `extracted_hits.faa`: Sequences of BLAST hits
  - `combined_sequences.faa`: Combined query and hit sequences
  - `unique_subjects.txt`: List of unique hit accessions
  - `aln/`: Alignment files
    - `aligned_sequences.msa`: Raw alignment
    - `trimmed_alignment.msa`: Trimmed alignment
  - `tree/`: Phylogenetic trees
    - `final_tree.treefile`: Newick tree file
    - `decorated_tree.png`: Visualization with taxonomy
    - `tree_stats.tab`: Statistics about the tree
  - `closest_neighbors.csv`: List of closest neighbors with distances
  - `closest_neighbors_with_taxonomy.csv`: Enhanced CSV with taxonomy information
  - `taxonomy_assignments.txt`: Taxonomy information in tabular format
  - `itol/`: Files for Interactive Tree of Life visualization

A comprehensive log file (`<input_dir>_nngenetree_completion.log`) contains a summary of the analysis, including:
- Pipeline version and runtime information
- BLAST hit counts for each sample
- Taxonomy distribution statistics
- Tree generation status

## ⚙️ Configuration

The pipeline is configured through `workflow/config.txt`. Key parameters include:

- `input_dir`: Directory containing input FASTA files (default: "example")
- `blast_db`: Path to BLAST database (required)
- `blast_hits`: Number of BLAST hits to retrieve (default: 50)
- `closest_neighbors`: Number of closest neighbors to extract per query (default: 10)
- `query_filter`: Optional comma-separated list of query prefixes to filter by

Resource configuration is also available for each step:
```yaml
resources:
  run_diamond_blastp:
    threads: 16
    mem_mb: 32000
    time: "4:00:00"
  # Additional resource configurations...
```

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
