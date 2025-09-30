# NNGeneTree - Nextflow Implementation

## Overview

This directory contains the Nextflow implementation of the NNGeneTree pipeline, providing an alternative workflow engine to Snakemake with built-in features for resume, reporting, and flexible execution.

## Quick Start

```bash
# Test run with small database (recommended first step)
bash run_nextflow.sh test

# Run on your own data locally
bash run_nextflow.sh mydata local

# Run on SLURM cluster
bash run_nextflow.sh mydata slurm
```

## Directory Structure

```
nextflow/
├── main.nf                          # Main workflow definition
├── nextflow.config                  # Pipeline configuration
├── modules/                         # Process modules
│   ├── diamond_blastp.nf           # DIAMOND BLAST search
│   ├── process_blast.nf            # BLAST result processing
│   ├── extract_hits.nf             # Sequence extraction
│   ├── combine_sequences.nf        # Sequence merging
│   ├── alignment.nf                # MAFFT + TrimAl
│   ├── phylogeny.nf                # IQ-TREE + neighbor extraction
│   ├── taxonomy.nf                 # Taxonomy assignment
│   ├── visualization.nf            # Tree decoration
│   └── placement.nf                # Phylogenetic placement
├── conf/                            # Configuration profiles
│   ├── base.config                 # Default settings
│   ├── test.config                 # Test dataset config
│   └── slurm.config                # HPC cluster config
└── bin/                             # Symlinks to Python scripts
```

## Installation

### Prerequisites

1. **Nextflow** (version 20.x or later)
   ```bash
   curl -s https://get.nextflow.io | bash
   mv nextflow ~/bin/  # or another directory in your PATH
   ```

2. **Pixi environment** (for dependencies)
   ```bash
   pixi install
   ```

Alternatively, Nextflow can use conda or containers for dependencies.

## Usage

### Test Run

The fastest way to verify the pipeline works:

```bash
bash run_nextflow.sh test
```

This runs on the test dataset (`test/*.faa`) using a small reference database. Completes in minutes.

**Expected output:**
- `test_output/test1/` - Results for test1.faa
- `test_output/test2/` - Results for test2.faa
- `test_output/combined_placement_results.json` - Combined results

### Running on Your Data

#### Local Execution
```bash
bash run_nextflow.sh my_input_dir local
```

Uses 16 cores by default. Adjust in `nextflow/conf/base.config`.

#### SLURM Cluster Execution
```bash
bash run_nextflow.sh my_input_dir slurm
```

Submits jobs to the SLURM scheduler. Configure queue settings in `nextflow/conf/slurm.config`.

### Advanced Usage

#### Direct Nextflow Command

For more control, run Nextflow directly:

```bash
cd nextflow

# Basic run
nextflow run main.nf --input_dir ../test -profile test

# With custom parameters
nextflow run main.nf \
    --input_dir ../my_data \
    --blast_db /path/to/database \
    --blast_hits 50 \
    --closest_neighbors 20 \
    -profile local \
    -resume
```

#### Resume Failed Runs

Nextflow automatically caches completed tasks. To resume after failure:

```bash
cd nextflow
nextflow run main.nf -profile test -resume
```

Only failed/incomplete tasks will re-run.

## Configuration

### Parameters

Key parameters can be set in `nextflow/nextflow.config` or via command line:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `input_dir` | Directory with .faa files | `test` |
| `output_dir` | Output directory | `{input_dir}_output` |
| `blast_db` | BLAST database path | `test/db/test_reference` |
| `blast_hits` | BLAST hits per query | `5` (test), `20` (prod) |
| `closest_neighbors` | Neighbors to extract | `5` (test), `10` (prod) |
| `query_filter` | Query prefix filter | `` |
| `itol_tax_level` | iTOL taxonomy level | `class` |
| `query_prefixes` | Placement query prefixes | `Hype,Klos` |

### Command-Line Overrides

```bash
nextflow run main.nf \
    --input_dir my_data \
    --blast_hits 100 \
    --closest_neighbors 30 \
    -profile local
```

### Profiles

Profiles define execution environments:

- **test**: Small test database, minimal resources
- **local**: Local execution, production database
- **slurm**: SLURM cluster execution
- **standard**: Default (same as local)

Activate with `-profile <name>`.

### Resource Configuration

Edit `nextflow/conf/base.config` to adjust CPU/memory per process:

```groovy
params {
    resources {
        run_diamond_blastp {
            threads = 16
            mem_mb = 64000
            time = '4h'
        }
        // ... other processes
    }
}
```

## Output Structure

Same as Snakemake pipeline:

```
{input_dir}_output/
├── test1/                           # Sample-specific results
│   ├── blast_results.m8
│   ├── unique_subjects.txt
│   ├── extracted_hits.faa
│   ├── combined_sequences.faa
│   ├── aln/
│   │   ├── aligned_sequences.msa
│   │   └── trimmed_alignment.msa
│   ├── tree/
│   │   ├── final_tree.treefile
│   │   ├── decorated_tree.png
│   │   └── tree_stats.tab
│   ├── closest_neighbors.csv
│   ├── closest_neighbors_with_taxonomy.csv
│   ├── taxonomy_assignments.txt
│   ├── placement_results.json
│   └── placement_results.csv
├── test2/                           # Additional samples...
│   └── ...
└── combined_placement_results.json  # Aggregated results
```

Additionally, Nextflow generates execution reports:

- `nextflow_report.html` - Execution summary with resource usage
- `nextflow_timeline.html` - Timeline visualization
- `nextflow_trace.txt` - Detailed task information
- `nextflow_dag.html` - Pipeline DAG visualization

## Execution Reports

Nextflow provides rich execution reporting:

### View Execution Report
```bash
# After pipeline completes
open test_output/nextflow_report.html
```

Contains:
- Task completion status
- Resource usage (CPU, memory, time)
- Failed tasks with error messages

### View Timeline
```bash
open test_output/nextflow_timeline.html
```

Visual timeline showing when each task ran and how long it took.

### View DAG
```bash
open test_output/nextflow_dag.html
```

Directed acyclic graph showing pipeline structure and dependencies.

## Troubleshooting

### Pipeline Fails with "Command not found"

Ensure Pixi environment is activated or conda directive is working:

```bash
# Check if tools are available
pixi shell
which diamond
which mafft
```

### "No such file or directory" for Python scripts

Verify symlinks in `nextflow/bin/`:

```bash
ls -la nextflow/bin/
# Should show symlinks to ../../workflow/scripts/*.py
```

### SLURM Jobs Not Submitting

Check SLURM configuration in `nextflow/conf/slurm.config`:
- Queue name (`queue`)
- Account/partition (`clusterOptions`)
- Resource limits

### Resume Not Working

Delete work directory to force re-run:

```bash
cd nextflow
rm -rf work .nextflow*
nextflow run main.nf -profile test
```

## Comparison: Nextflow vs Snakemake

Both implementations produce identical results. Choose based on your needs:

| Feature | Nextflow | Snakemake |
|---------|----------|-----------|
| **Resume capability** | Built-in (`-resume`) | Via checkpoints |
| **Execution reports** | HTML reports included | Requires plugins |
| **Cloud execution** | Native support | Requires setup |
| **Resource tracking** | Automatic | Manual |
| **Learning curve** | Moderate | Easier for Python users |
| **Parallelization** | Implicit, channel-based | Explicit, DAG-based |

## Migration from Snakemake

The Nextflow implementation is **fully compatible** with existing Snakemake outputs:

1. Both use the same Python scripts
2. Output directory structure is identical
3. Configuration parameters are equivalent

To switch:
```bash
# Snakemake
pixi run test-fast

# Nextflow
bash run_nextflow.sh test
```

Results are interchangeable.

## Contributing

When adding new features:

1. Add process to appropriate module in `nextflow/modules/`
2. Include process in `nextflow/main.nf`
3. Update configuration in `nextflow/conf/`
4. Test with `bash run_nextflow.sh test`
5. Document in this README

## License

Same as main NNGeneTree project (MIT License).

## Support

For issues specific to the Nextflow implementation:
1. Check execution reports (`nextflow_report.html`)
2. Review log files in `work/` directory
3. Open GitHub issue with "Nextflow" label

For general pipeline questions, see main `README.md`.