#!/bin/bash

# SLURM submission script for NNGeneTree pipeline
# Usage: bash run_slurm.sh <input_directory>

INPUT_DIR="${1}"

if [ -z "$INPUT_DIR" ]; then
    echo "Error: Please provide an input directory"
    echo "Usage: bash run_slurm.sh <input_directory>"
    exit 1
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

echo "Running NNGeneTree pipeline on SLURM cluster"
echo "Input directory: $INPUT_DIR"

# Create log directory if it doesn't exist
mkdir -p log

# Run Snakemake with SLURM cluster submission
snakemake \
    --jobs 256 \
    --local-cores 8 \
    --config input_dir="$INPUT_DIR" \
    --cluster "sbatch \
      -A grp-org-sc-mgs \
      -q jgi_normal \
      -J nngenetree.{rule}.{wildcards.sample} \
      -c {threads} \
      --mem={resources.mem_mb} \
      -t {resources.time} \
      --output=log/nngenetree_{rule}_{wildcards.sample}_%j.out \
      --error=log/nngenetree_{rule}_{wildcards.sample}_%j.err"