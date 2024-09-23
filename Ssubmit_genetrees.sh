#!/bin/bash
#SBATCH -A grp-org-sc-mgs
#SBATCH	-q jgi_normal
#SBATCH -J genetrees
#SBATCH -c 64
#SBATCH --mem=256GB
#SBATCH -t 24:00:00
#SBATCH --output=nngenetree_analysis_%A_%a.out
#SBATCH --error=nngenetree_analysis_%A_%a.err

eval "$(conda shell.bash hook)"
conda activate /clusterfs/jgi/groups/science/homes/fschulz/miniconda3/envs/snk

queries=$1

snakemake --use-conda -j 64 --config input_dir=$queries
