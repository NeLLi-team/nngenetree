#!/bin/bash

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

# Activate conda environment for Snakemake
source /clusterfs/jgi/groups/science/homes/fschulz/miniconda3/etc/profile.d/conda.sh
conda activate snk

# Common Snakemake parameters
common_params="--use-conda \
    --rerun-incomplete \
    --rerun-triggers mtime \
    --config input_dir=\"${queries_faa}\""

# Check if local execution is requested
if [ "${local_run}" = "true" ]; then
    # Run Snakemake locally with all cores
    echo "Running pipeline locally with all available cores"
    snakemake \
        ${common_params} \
        --cores all
else
    # Run Snakemake with SLURM
    echo "Running pipeline on SLURM cluster"
    snakemake \
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
