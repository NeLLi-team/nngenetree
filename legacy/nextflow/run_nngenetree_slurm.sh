#!/bin/bash
#SBATCH --job-name=nngenetree-head
#SBATCH --output=nngenetree_head_%j.log
#SBATCH --error=nngenetree_head_%j.err
#SBATCH --time=72:00:00
#SBATCH --partition=jgi_normal
#SBATCH --qos=jgi_normal
#SBATCH --account=grp-org-sc-mgs
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

# NNGeneTree Nextflow Head Process
# This script runs the Nextflow head process as a SLURM job
# to prevent it from being killed when running on a login node

set -euo pipefail

# Change to the nngenetree directory
cd /clusterfs/jgi/scratch/science/mgs/nelli/frederik/projects/25spacermatch/mirus_gamadvirus_analysis/results/nngenetree

echo "============================================"
echo "  NNGeneTree Pipeline - SLURM Head Job"
echo "============================================"
echo "  Start Time: $(date)"
echo "  Job ID: ${SLURM_JOB_ID:-local}"
echo "  Node: ${SLURM_NODELIST:-$(hostname)}"
echo "============================================"

# Run Nextflow (pixi provides the environment)
pixi run nextflow run main.nf \
    --input_dir by_interpro \
    -profile slurm \
    -resume

echo ""
echo "============================================"
echo "  Pipeline Complete: $(date)"
echo "============================================"
