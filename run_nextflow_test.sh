#!/bin/bash
##############################################
# NNGeneTree Nextflow Test Script
##############################################
# Run the pipeline on test data (test1.faa, test2.faa)
# Uses test database for fast execution
#

set -euo pipefail

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
nextflow run main.nf -profile test -resume

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
else
    echo "⚠️  Warning: $MISSING_FILES key file(s) missing"
    exit 1
fi