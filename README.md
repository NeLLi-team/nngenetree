# NNGeneTree

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/NeLLi-team/nngenetree)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**NNGeneTree** is a phylogenetic analysis and taxonomic classification pipeline for protein sequences. It builds gene trees and finds the nearest neighbors of query sequences in the phylogenetic context, assigning taxonomy information for comprehensive evolutionary analysis.

## Features

- **Parallel execution** with Dask (local multi-core or SLURM cluster)
- **Local taxonomy lookup** using taxonkit + blastdbcmd (no NCBI API rate limits)
- **File-based caching** for incremental processing and resume capability
- **Smart neighbor selection** based on phylogenetic distance
- **Tree visualizations** with taxonomic annotations
- **Modular design** with Pixi package management

---

## Requirements

### Software

- [Pixi](https://pixi.sh/) - Package and environment management
- [SLURM](https://slurm.schedmd.com/) - Optional, for cluster execution

### Required NCBI Files

The pipeline requires the following NCBI database files for local taxonomy lookup:

| File | Description | Source |
|------|-------------|--------|
| **NR DIAMOND Database** | Protein database for BLAST searches | Pre-built or create with `diamond makedb` |
| **NR BLAST Database** | For sequence extraction with `blastdbcmd` | `ftp://ftp.ncbi.nih.gov/blast/db/nr.*` |
| **Taxonomy Dump Files** | For local taxonomy lineage lookup | `ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz` |

#### Taxonomy Dump Files Required

Extract from `taxdump.tar.gz`:
- `names.dmp` - Scientific names for each taxid
- `nodes.dmp` - Taxonomy tree structure
- `merged.dmp` - Merged/renamed taxids
- `delnodes.dmp` - Deleted taxids

These files should be in the same directory as your NR BLAST database, or in `~/.taxonkit/`.

---

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/NeLLi-team/nngenetree.git
cd nngenetree

# Install Pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Install the pipeline environment
pixi install -e prefect
```

### Setting Up NCBI Databases

```bash
# Example: Download and setup taxonomy files
cd /path/to/your/databases/nr/

# Download taxonomy dump (if not already present)
wget -c ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
tar -xzf taxdump.tar.gz

# Verify required files exist
ls -la names.dmp nodes.dmp merged.dmp delnodes.dmp

# Setup taxonkit (optional - uses files from blast_db directory by default)
mkdir -p ~/.taxonkit
cp names.dmp nodes.dmp merged.dmp delnodes.dmp ~/.taxonkit/
```

---

## Usage

### Basic Usage

```bash
# Activate the pipeline environment
pixi shell -e prefect

# Run pipeline locally (4 workers by default)
python -m nngenetree run \
  --input-dir my_proteins/ \
  --blast-db /path/to/nr/nr \
  --mode local

# Run on SLURM cluster
python -m nngenetree run \
  --input-dir my_proteins/ \
  --blast-db /path/to/nr/nr \
  --mode slurm \
  --slurm-account my_account \
  --max-jobs 50
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input-dir, -i` | Input directory with .faa files | Required |
| `--blast-db, -d` | Path to BLAST/DIAMOND database | Required |
| `--output-dir, -o` | Output directory | `{input}_output` |
| `--mode, -m` | Execution mode: `local` or `slurm` | `local` |
| `--threads, -t` | Threads per task (BLAST, alignment, tree) | 8 |
| `--local-workers, -w` | Number of Dask workers (local mode) | 4 |
| `--threads-per-worker` | Threads per Dask worker | 2 |
| `--blast-hits` | BLAST hits per query | 20 |
| `--closest-neighbors` | Neighbors to extract from tree | 10 |
| `--tree-builder` | Tree method: `fasttree` or `iqtree` | `fasttree` |
| `--query-prefixes` | Prefixes identifying query sequences | `GCMeta_,GTDB_,spire_mag_` |
| `--entrez-email` | Email for NCBI API (fallback only) | `fschulz@lbl.gov` |

### SLURM Options

| Option | Description | Default |
|--------|-------------|---------|
| `--slurm-queue` | SLURM partition/queue | `jgi_normal` |
| `--slurm-account` | SLURM account for billing | `grp-org-sc-mgs` |
| `--slurm-cores` | CPU cores per SLURM job | 32 |
| `--slurm-workers` | Dask workers per SLURM job | 8 |
| `--slurm-memory` | Memory per SLURM job (e.g., 128GB) | `128GB` |
| `--slurm-walltime` | Job walltime (HH:MM:SS) | `08:00:00` |
| `--max-jobs` | Maximum concurrent SLURM jobs | 65 |

### Environment Variables / .env File

Create a `.env` file in the project directory (automatically loaded):

```bash
# .env file example
NNGENETREE_BLAST_DB=/path/to/nr/nr
NNGENETREE_MODE=slurm
NNGENETREE_SLURM_QUEUE=your_queue
NNGENETREE_SLURM_ACCOUNT=your_account
NNGENETREE_SLURM_CORES_PER_JOB=32
NNGENETREE_SLURM_PROCESSES_PER_JOB=8
NNGENETREE_SLURM_MEMORY_PER_JOB=128GB
NNGENETREE_SLURM_WALLTIME=08:00:00
NNGENETREE_SLURM_MAX_JOBS=65
```

Or export as environment variables:

```bash
export NNGENETREE_BLAST_DB=/path/to/nr/nr
export NNGENETREE_MODE=slurm
# ... etc
```

---

## Pipeline Workflow

```
INPUT FASTA FILES (.faa)
         |
         v
+---------------------+
| DIAMOND BLASTP      |  Fast protein similarity search
+---------------------+
         |
         v
+---------------------+
| EXTRACT SEQUENCES   |  Retrieve hit sequences (blastdbcmd)
+---------------------+
         |
         v
+---------------------+
| COMBINE & DEDUPE    |  Merge query + hit sequences
+---------------------+
         |
         v
+---------------------+
| MAFFT ALIGNMENT     |  Multiple sequence alignment
+---------------------+
         |
         v
+---------------------+
| TRIMAL TRIMMING     |  Remove poorly aligned regions
+---------------------+
         |
         v
+---------------------+
| TREE BUILDING       |  FastTree (LG model) or IQ-TREE
+---------------------+
         |
         v
+---------------------+
| EXTRACT NEIGHBORS   |  Find N closest in tree
+---------------------+
         |
         v
+---------------------+
| ASSIGN TAXONOMY     |  Local lookup (blastdbcmd + taxonkit)
+---------------------+  Falls back to NCBI API if needed
         |
         v
+---------------------+
| DECORATE TREE       |  Add taxonomy annotations
+---------------------+
         |
         v
+---------------------+
| PLACEMENT RESULTS   |  JSON/CSV with consensus taxonomy
+---------------------+
```

---

## Taxonomy Lookup

### Local Lookup (Default - Recommended)

The pipeline uses **local taxonomy lookup** by default, which is:
- **Fast**: Processes thousands of accessions in seconds
- **No rate limits**: Multiple workers can query simultaneously
- **Offline**: Works without internet after initial database setup

**How it works:**
1. `blastdbcmd` extracts taxid from protein accession using the BLAST database
2. `taxonkit` looks up the full lineage from taxid using taxdump files

**Requirements:**
- BLAST database must have taxonomy information (standard NR does)
- Taxdump files (`names.dmp`, `nodes.dmp`) in blast_db directory or `~/.taxonkit/`

### NCBI API Fallback

If local tools are unavailable, the pipeline falls back to NCBI Entrez API:
- Rate-limited to 3 requests/second
- Requires `--entrez-email` option
- Results are cached to disk to avoid repeated lookups

---

## Output Structure

Results are saved in `<input_dir>_output/`:

```
output/
├── <sample_name>/
│   ├── blast_results.m8           # DIAMOND BLAST output
│   ├── subjects.txt               # Unique hit accessions
│   ├── extracted_hits.faa         # Hit sequences
│   ├── combined_sequences.faa     # Query + hits combined
│   ├── aln/
│   │   ├── aligned_sequences.msa  # MAFFT alignment
│   │   └── trimmed_alignment.msa  # TrimAl output
│   ├── tree/
│   │   ├── final_tree.treefile    # Newick tree
│   │   └── decorated_tree.nwk     # Tree with annotations
│   ├── closest_neighbors.csv      # Neighbors with distances
│   ├── neighbors_with_taxonomy.csv # With taxonomy lineages
│   ├── taxonomy_summary.json      # Taxonomy statistics
│   ├── tree_stats.json            # Tree statistics
│   └── placement_results.json     # Final placement results
└── combined_placement_results.json # All samples combined
```

---

## Configuration

### Database Paths

The most important configuration is the path to your NCBI databases:

```bash
# BLAST/DIAMOND database (required)
--blast-db /path/to/nr/nr

# The pipeline expects these files in the same directory:
# - nr.dmnd (DIAMOND database)
# - nr.* (BLAST database files for blastdbcmd)
# - names.dmp, nodes.dmp, merged.dmp, delnodes.dmp (taxdump)
```

### Example: JGI Cluster Setup

```bash
# JGI NR database location
BLAST_DB=/clusterfs/jgi/scratch/science/mgs/nelli/databases/nr/nr

# Run on SLURM with 8 workers
python -m nngenetree run \
  --input-dir by_interpro/ \
  --blast-db $BLAST_DB \
  --mode slurm \
  --slurm-account grp-org-sc-mgs \
  --max-jobs 64
```

---

## Batch Processing

For large datasets (hundreds of samples), process in batches:

```bash
# Example: Process 516 InterPro families in batches of 64
for batch in $(seq 0 7); do
  start=$((batch * 64))
  # Create batch input directory with subset of files
  # Run pipeline on each batch
done
```

The pipeline automatically:
- Skips completed samples (file-based caching)
- Scales workers based on available resources
- Handles failures gracefully (other samples continue)

---

## Pixi Tasks

```bash
# List available tasks
pixi task list

# Common tasks (in prefect environment)
pixi run -e prefect run-local     # Run locally
pixi run -e prefect run-slurm     # Run on SLURM
pixi run -e prefect info          # Show pipeline info
pixi run -e prefect test          # Run tests
pixi run -e prefect lint          # Lint code
pixi run -e prefect format        # Format code

# Cleanup
pixi run clean                    # Clean output directories
pixi run clean-all                # Clean everything
```

---

## Legacy Nextflow Workflow

The original Nextflow implementation is preserved in `legacy/nextflow/` for reference. The Dask implementation is now the primary and recommended workflow.

---

## Standalone Scripts

Utility scripts in `bin/` can be used independently:

| Script | Purpose |
|--------|---------|
| `extract_closest_neighbors.py` | Extract neighbors from tree |
| `parse_closest_neighbors.py` | Add taxonomy to neighbor CSV |
| `decorate_tree.py` | Create tree visualizations |
| `tree_stats.py` | Calculate tree statistics |
| `orthofinder_preprocess.py` | OrthoFinder integration |

---

## License

MIT License - see LICENSE file for details.

---

## Contact

For questions or issues, please open an issue on the GitHub repository.

*Developed at Joint Genome Institute (JGI)*
