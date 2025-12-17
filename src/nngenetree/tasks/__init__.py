"""Prefect tasks for NNGeneTree pipeline."""

from .blast import diamond_blastp, process_blast_results, extract_hits
from .alignment import combine_sequences, align_sequences, trim_alignment
from .phylogeny import build_tree
from .taxonomy import assign_taxonomy
from .analysis import (
    extract_closest_neighbors,
    decorate_tree,
    calculate_tree_stats,
    extract_phylogenetic_placement,
    combine_placement_results,
)

__all__ = [
    "diamond_blastp",
    "process_blast_results",
    "extract_hits",
    "combine_sequences",
    "align_sequences",
    "trim_alignment",
    "build_tree",
    "assign_taxonomy",
    "extract_closest_neighbors",
    "decorate_tree",
    "calculate_tree_stats",
    "extract_phylogenetic_placement",
    "combine_placement_results",
]
