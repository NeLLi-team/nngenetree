#!/bin/bash

# NNGeneTree Pipeline Runner
# --------------------------
# Usage:
#   1. Run on SLURM cluster (default):
#      pixi run run-slurm-dir <input_directory>
#      OR
#      bash run.sh <input_directory>
#      Example: bash run.sh example
#
#   2. Run locally with all available cores:
#      pixi run run-dir <input_directory>
#      OR
#      bash run.sh <input_directory> true
#      Example: bash run.sh example true
#
# Prerequisites: Install dependencies with `pixi install`

# Set default input directory to example if not provided
queries_faa="${1:-example}"
local_run="${2:-false}"

# Create log directory if it doesn't exist
mkdir -p log

# Print start message
echo "Starting NNGeneTree pipeline v0.9.0 on directory: ${queries_faa}"
echo "Using config file: workflow/config.txt"
echo "Local execution: ${local_run}"

start_time=$(date +%s)
start_date=$(date '+%Y-%m-%d %H:%M:%S')
echo "Started at: ${start_date}"

# Check if pixi is available
if ! command -v pixi &> /dev/null; then
    echo "Error: pixi is not installed or not in PATH"
    echo "Please install pixi from https://pixi.sh/"
    exit 1
fi

# Common Snakemake parameters (removed --use-conda)
common_params="--rerun-incomplete \
    --rerun-triggers mtime \
    --config input_dir=${queries_faa}"

# Check if local execution is requested
if [ "${local_run}" = "true" ]; then
    # Run Snakemake locally with 16 cores using pixi
    echo "Running pipeline locally with 16 cores (using pixi)"
    pixi run snakemake \
        ${common_params} \
        --cores 16
else
    # Run Snakemake with SLURM using pixi
    echo "Running pipeline on SLURM cluster (using pixi)"
    pixi run snakemake \
        ${common_params} \
        --jobs 256 \
        --local-cores 8 \
        --cluster "sbatch \
          -A grp-org-sc-mgs \
          -q jgi_normal \
          -J nngenetree.{rule}.{wildcards.sample} \
          -c {threads} \
          --mem={resources.mem_mb} \
          -t {resources.time} \
          --output=log/nngenetree_{rule}_{wildcards.sample}_%j.out \
          --error=log/nngenetree_{rule}_{wildcards.sample}_%j.err"
fi

# Check if run completed successfully
if [ $? -eq 0 ]; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    hours=$((duration / 3600))
    minutes=$(( (duration % 3600) / 60 ))
    seconds=$((duration % 60))
    
    echo "✅ NNGeneTree pipeline completed successfully!"
    echo "⏱️ Total runtime: ${hours}h ${minutes}m ${seconds}s"
    echo "📊 Results can be found in ${queries_faa}_nngenetree/"
    echo "📋 Summary log: ${queries_faa}_nngenetree_completion.log"
else
    echo "❌ NNGeneTree pipeline failed. Please check the logs in the log/ directory."
fi
