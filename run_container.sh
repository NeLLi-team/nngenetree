#!/bin/bash

# NNGeneTree Container Runner
# ---------------------------
# Usage:
#   ./run_container.sh [-p PROCESSES] [-i INPUT_DIR] [-o OUTPUT_DIR] [-b BLAST_DB] [-c CONFIG_FILE] [-l]
#
# Options:
#   -p PROCESSES    Number of processes to use (default: 8)
#   -i INPUT_DIR    Directory containing input .faa files (default: example)
#   -o OUTPUT_DIR   Directory to save output (default: INPUT_DIR_nngenetree)
#   -b BLAST_DB     Path to BLAST database (default: from config)
#   -c CONFIG_FILE  Path to custom config file (optional)
#   -l             Run locally instead of using SLURM (default: false)
#   -h             Show this help message

# Default values
PROCESSES=8
INPUT_DIR="example"
OUTPUT_DIR=""
BLAST_DB=""
CONFIG_FILE=""
LOCAL_RUN=false

# Parse command line arguments
while getopts "p:i:o:b:c:lh" opt; do
  case $opt in
    p) PROCESSES="$OPTARG" ;;
    i) INPUT_DIR="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    b) BLAST_DB="$OPTARG" ;;
    c) CONFIG_FILE="$OPTARG" ;;
    l) LOCAL_RUN=true ;;
    h)
      echo "Usage: ./run_container.sh [-p PROCESSES] [-i INPUT_DIR] [-o OUTPUT_DIR] [-b BLAST_DB] [-c CONFIG_FILE] [-l]"
      echo
      echo "Options:"
      echo "  -p PROCESSES    Number of processes to use (default: 8)"
      echo "  -i INPUT_DIR    Directory containing input .faa files (default: example)"
      echo "  -o OUTPUT_DIR   Directory to save output (default: INPUT_DIR_nngenetree)"
      echo "  -b BLAST_DB     Path to BLAST database (default: from config)"
      echo "  -c CONFIG_FILE  Path to custom config file (optional)"
      echo "  -l             Run locally instead of using SLURM (default: false)"
      echo "  -h             Show this help message"
      exit 0
      ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

# Set output directory if not specified
if [ -z "$OUTPUT_DIR" ]; then
  OUTPUT_DIR="${INPUT_DIR}_nngenetree"
fi

# Resolve absolute paths
INPUT_DIR_ABS=$(realpath "$INPUT_DIR")
if [ -z "$OUTPUT_DIR" ]; then
  OUTPUT_DIR_ABS="${INPUT_DIR_ABS}_nngenetree"
else
  OUTPUT_DIR_ABS=$(realpath "$OUTPUT_DIR")
fi

# Create command options
CMD_OPTIONS="--config input_dir=/data/input"

# Add BLAST DB path if provided
if [ ! -z "$BLAST_DB" ]; then
  BLAST_DB_ABS=$(realpath "$BLAST_DB")
  BLAST_DB_DIR=$(dirname "$BLAST_DB_ABS") 
  BLAST_DB_BASE=$(basename "$BLAST_DB_ABS")
  CMD_OPTIONS="$CMD_OPTIONS blast_db=/blast_db/$BLAST_DB_BASE"
  BLAST_BIND="--bind $BLAST_DB_DIR:/blast_db"
else
  BLAST_BIND=""
fi

# Print start message
echo "Starting NNGeneTree pipeline v0.9.0 with input directory: ${INPUT_DIR}"
echo "Output will be saved to: ${OUTPUT_DIR_ABS}"
echo "Processes: ${PROCESSES}"
echo "Local execution: ${LOCAL_RUN}"

# Prepare bind directories
mkdir -p "$OUTPUT_DIR_ABS"
mkdir -p "${OUTPUT_DIR_ABS}/.snakemake"

# Create log directory only if running in cluster mode
if [ "$LOCAL_RUN" = "false" ]; then
    mkdir -p log
fi

# Create or use config
if [ ! -z "$CONFIG_FILE" ]; then
  CONFIG_ABS=$(realpath "$CONFIG_FILE")
  CONFIG_BIND="--bind $CONFIG_ABS:/nngenetree/workflow/config.txt"
  echo "Using custom config: $CONFIG_ABS"
else
  CONFIG_BIND=""
  echo "Using default config in container"
fi

# Build command
SINGULARITY_CMD="singularity run --containall \
  --bind $INPUT_DIR_ABS:/data/input \
  --bind $OUTPUT_DIR_ABS:/data/output \
  --bind ${OUTPUT_DIR_ABS}/.snakemake:/nngenetree/.snakemake \
  $BLAST_BIND $CONFIG_BIND \
  --pwd /nngenetree \
  ./nngenetree.sif"

# Common Snakemake parameters
SNAKEMAKE_PARAMS="snakemake --snakefile workflow/Snakefile \
  --rerun-incomplete \
  --rerun-triggers mtime \
  $CMD_OPTIONS \
  --directory /data/output"

# Check if local execution is requested
if [ "$LOCAL_RUN" = "true" ]; then
  # Run Snakemake locally with specified cores
  echo "Running pipeline locally with $PROCESSES cores"
  $SINGULARITY_CMD $SNAKEMAKE_PARAMS --cores $PROCESSES
else
  # Run Snakemake with SLURM
  echo "Running pipeline on SLURM cluster"
  $SINGULARITY_CMD $SNAKEMAKE_PARAMS \
    --jobs 256 \
    --local-cores $PROCESSES \
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
  echo "✅ NNGeneTree pipeline completed successfully!"
  echo "📊 Results can be found in ${OUTPUT_DIR_ABS}"
  echo "📋 Summary log: ${OUTPUT_DIR_ABS}/*_completion.log"
else
  echo "❌ NNGeneTree pipeline failed. Please check the logs in the log/ directory."
fi 