#!/bin/bash

# Container setup script for NNGeneTree
# This script runs during container build to set up the environment

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Create necessary directories
mkdir -p /nngenetree
mkdir -p /data/input
mkdir -p /data/output
mkdir -p /blast_db

# Set up conda environment
. /opt/conda/etc/profile.d/conda.sh
conda activate nngenetree

# Update paths in Snakefile for container compatibility
echo "Updating paths for container compatibility..."
python /nngenetree/container/scripts/update_paths.py

# Test critical components
echo "Testing critical components..."
python -c "import snakemake; print(f'Snakemake version: {snakemake.__version__}')"
python -c "import Bio; print(f'BioPython version: {Bio.__version__}')"

echo "Container setup completed successfully!" 