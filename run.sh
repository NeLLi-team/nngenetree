#!/bin/bash

queries_faa="$1"
snakemake \
    --use-conda \
    --rerun-incomplete \
    --jobs 256 \
    --local-cores 8 \
    --config input_dir="${queries_faa}" \
    --cluster "sbatch \
      -A grp-org-sc-mgs \
      -q jgi_normal \
      -J {rule}.{wildcards.sample} \
      -c {threads} \
      --mem={resources.mem_mb} \
      -t {resources.time} \
      --output=nngenetree_analysis_%j.out \
      --error=nngenetree_analysis_%j.err"
