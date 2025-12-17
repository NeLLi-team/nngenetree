"""Phylogenetic tree building tasks for NNGeneTree pipeline."""

import logging
import subprocess
from pathlib import Path

from ..utils.io import ensure_dir

logger = logging.getLogger(__name__)


def build_tree(
    trimmed_alignment: Path,
    output_dir: Path,
    builder: str = "fasttree",
    threads: int = 8,
) -> Path:
    """Build phylogenetic tree with FastTree or IQ-TREE.

    Args:
        trimmed_alignment: Path to trimmed alignment file.
        output_dir: Output directory for results.
        builder: Tree building method ('fasttree' or 'iqtree').
        threads: Number of threads to use.

    Returns:
        Path to tree file in Newick format.
    """
    tree_dir = ensure_dir(output_dir / "tree")
    tree_file = tree_dir / "final_tree.treefile"

    # Skip if output already exists
    if tree_file.exists() and tree_file.stat().st_size > 0:
        logger.info(f"Tree exists, skipping: {tree_file}")
        return tree_file

    if builder == "fasttree":
        _build_fasttree(trimmed_alignment, tree_file)
    elif builder == "iqtree":
        _build_iqtree(trimmed_alignment, tree_dir, threads)
    else:
        raise ValueError(f"Unknown tree builder: {builder}")

    return tree_file


def _build_fasttree(alignment: Path, output: Path) -> None:
    """Build tree with FastTree."""
    logger.info("Building tree with FastTree (LG model)")

    with open(alignment) as inf, open(output, "w") as outf:
        result = subprocess.run(
            ["fasttree", "-lg"],
            stdin=inf,
            stdout=outf,
            stderr=subprocess.PIPE,
            text=True,
        )

    if result.returncode != 0:
        logger.error(f"FastTree failed: {result.stderr}")
        raise RuntimeError(f"FastTree failed: {result.stderr}")

    logger.info(f"FastTree completed: {output}")


def _build_iqtree(alignment: Path, tree_dir: Path, threads: int) -> None:
    """Build tree with IQ-TREE."""
    logger.info(f"Building tree with IQ-TREE ({threads} threads)")

    prefix = tree_dir / "final_tree"

    cmd = [
        "iqtree",
        "-s",
        str(alignment),
        "-m",
        "LG+G4",
        "-T",
        str(threads),
        "--prefix",
        str(prefix),
        "-redo",  # Overwrite existing files
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        logger.error(f"IQ-TREE failed: {result.stderr}")
        raise RuntimeError(f"IQ-TREE failed: {result.stderr}")

    logger.info(f"IQ-TREE completed: {prefix}.treefile")
