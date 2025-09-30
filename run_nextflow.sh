#!/bin/bash
##############################################
# NNGeneTree Nextflow Execution Script
##############################################
# Usage: bash run_nextflow.sh <input_directory> [local|slurm]
#
# Examples:
#   bash run_nextflow.sh test local            # Run test data locally
#   bash run_nextflow.sh my_data               # Run on SLURM (default)
#   bash run_nextflow.sh my_data slurm         # Run on SLURM explicitly
#

set -euo pipefail

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_directory> [local|slurm]"
    echo ""
    echo "Arguments:"
    echo "  input_directory  - Directory containing .faa files"
    echo "  execution_mode   - 'local' for local execution, 'slurm' for cluster (default: slurm)"
    echo ""
    echo "Examples:"
    echo "  $0 test local"
    echo "  $0 my_data slurm"
    exit 1
fi

INPUT_DIR="$1"
EXECUTION_MODE="${2:-slurm}"

# Validate input directory
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

# Count FASTA files
FASTA_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -name "*.faa" | wc -l)
if [ "$FASTA_COUNT" -eq 0 ]; then
    echo "Error: No .faa files found in '$INPUT_DIR'"
    exit 1
fi

echo "╔════════════════════════════════════════╗"
echo "║   🧬 NNGeneTree Nextflow Pipeline      ║"
echo "╠════════════════════════════════════════╣"
echo "║ Input Dir:    $INPUT_DIR"
echo "║ FASTA Files:  $FASTA_COUNT"
echo "║ Execution:    $EXECUTION_MODE"
echo "╚════════════════════════════════════════╝"

# Run Nextflow with appropriate profile
if [ "$EXECUTION_MODE" = "local" ]; then
    echo "Running pipeline locally..."
    nextflow run main.nf \
        --input_dir "$INPUT_DIR" \
        -profile local \
        -resume
elif [ "$EXECUTION_MODE" = "slurm" ]; then
    echo "Running pipeline on SLURM cluster..."
    nextflow run main.nf \
        --input_dir "$INPUT_DIR" \
        -profile slurm \
        -resume
else
    echo "Error: Invalid execution mode '$EXECUTION_MODE'. Use 'local' or 'slurm'"
    exit 1
fi

echo ""
echo "✅ Pipeline execution complete!"
echo "Results are in: ${INPUT_DIR}_nngenetree/"