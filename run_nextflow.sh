#!/bin/bash
##############################################
# NNGeneTree Nextflow Execution Script
##############################################
# Usage:
#   bash run_nextflow.sh test                      # Run test mode with verification
#   bash run_nextflow.sh <input_directory> local   # Run locally
#   bash run_nextflow.sh <input_directory> slurm   # Run on SLURM (default)
#
# Examples:
#   bash run_nextflow.sh test                  # Test with small database
#   bash run_nextflow.sh my_data local         # Run my_data locally
#   bash run_nextflow.sh my_data slurm         # Run my_data on SLURM
#

set -euo pipefail

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 test | <input_directory> [local|slurm]"
    echo ""
    echo "Arguments:"
    echo "  test             - Run test mode with built-in verification"
    echo "  input_directory  - Directory containing .faa files"
    echo "  execution_mode   - 'local' for local execution, 'slurm' for cluster (default: slurm)"
    echo ""
    echo "Examples:"
    echo "  $0 test"
    echo "  $0 my_data local"
    echo "  $0 my_data slurm"
    exit 1
fi

# Check if test mode
if [ "$1" = "test" ]; then
    # Test mode
    echo "╔════════════════════════════════════════╗"
    echo "║   🧪 NNGeneTree Test Run (Nextflow)   ║"
    echo "╠════════════════════════════════════════╣"
    echo "║ Test Files: test/test1.faa             ║"
    echo "║             test/test2.faa             ║"
    echo "║ Database:   test/db/test_reference     ║"
    echo "║ Output:     test_output/               ║"
    echo "╚════════════════════════════════════════╝"

    # Clean previous test output (optional)
    if [ -d "test_output" ]; then
        echo "Cleaning previous test output..."
        rm -rf test_output
    fi

    # Run test pipeline
    echo "Running test pipeline..."
    pixi run nextflow run main.nf -profile test -resume

    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║     ✅ Test Pipeline Complete          ║"
    echo "╠════════════════════════════════════════╣"
    echo "║ Check outputs in: test_output/         ║"
    echo "╚════════════════════════════════════════╝"

    # Verify key outputs exist
    echo ""
    echo "Verifying test outputs..."

    KEY_FILES=(
        "test_output/test1/blast_results.m8"
        "test_output/test1/tree/final_tree.treefile"
        "test_output/test1/placement_results.json"
        "test_output/test2/blast_results.m8"
        "test_output/test2/tree/final_tree.treefile"
        "test_output/test2/placement_results.json"
        "test_output/combined_placement_results.json"
    )

    MISSING_FILES=0
    for file in "${KEY_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "  ✅ $file"
        else
            echo "  ❌ $file (MISSING)"
            ((MISSING_FILES++))
        fi
    done

    echo ""
    if [ $MISSING_FILES -eq 0 ]; then
        echo "✅ All key output files generated successfully!"
        exit 0
    else
        echo "⚠️  Warning: $MISSING_FILES key file(s) missing"
        exit 1
    fi
else
    # Production mode
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
        pixi run nextflow run main.nf \
            --input_dir "$INPUT_DIR" \
            -profile local \
            -resume
    elif [ "$EXECUTION_MODE" = "slurm" ]; then
        echo "Running pipeline on SLURM cluster..."
        pixi run nextflow run main.nf \
            --input_dir "$INPUT_DIR" \
            -profile slurm \
            -resume
    else
        echo "Error: Invalid execution mode '$EXECUTION_MODE'. Use 'local' or 'slurm'"
        exit 1
    fi

    echo ""
    echo "✅ Pipeline execution complete!"
    echo "Results are in: ${INPUT_DIR}_output/"
fi