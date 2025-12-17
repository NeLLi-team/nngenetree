"""Alignment-related tasks for NNGeneTree pipeline."""

import logging
import subprocess
from pathlib import Path

from ..utils.io import ensure_dir

logger = logging.getLogger(__name__)


def combine_sequences(
    query_fasta: Path,
    hits_fasta: Path,
    output_dir: Path,
) -> Path:
    """Combine query and hit sequences into a single FASTA file.

    Deduplicates sequences by ID.

    Args:
        query_fasta: Path to query FASTA file.
        hits_fasta: Path to extracted hits FASTA file.
        output_dir: Output directory for results.

    Returns:
        Path to combined FASTA file.
    """
    ensure_dir(output_dir)
    output_file = output_dir / "combined_sequences.faa"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Combined sequences exist, skipping: {output_file}")
        return output_file

    seen_ids: set[str] = set()
    sequences: list[tuple[str, str]] = []

    # Read query sequences first (priority)
    for seq_id, seq in _read_fasta_entries(query_fasta):
        clean_id = seq_id.split()[0]
        if clean_id not in seen_ids:
            seen_ids.add(clean_id)
            sequences.append((seq_id, seq))

    # Add hit sequences (skip duplicates)
    for seq_id, seq in _read_fasta_entries(hits_fasta):
        clean_id = seq_id.split()[0]
        if clean_id not in seen_ids:
            seen_ids.add(clean_id)
            sequences.append((seq_id, seq))

    # Write combined file
    with open(output_file, "w") as f:
        for seq_id, seq in sequences:
            f.write(f">{seq_id}\n{seq}\n")

    logger.info(f"Combined {len(sequences)} sequences to {output_file}")
    return output_file


def _read_fasta_entries(fasta_path: Path) -> list[tuple[str, str]]:
    """Read FASTA file and return list of (header, sequence) tuples."""
    entries = []
    current_header = None
    current_seq: list[str] = []

    with open(fasta_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                if current_header is not None:
                    entries.append((current_header, "".join(current_seq)))
                current_header = line[1:]
                current_seq = []
            elif current_header is not None:
                current_seq.append(line)

        if current_header is not None:
            entries.append((current_header, "".join(current_seq)))

    return entries


def align_sequences(
    combined_fasta: Path,
    output_dir: Path,
    threads: int = 8,
) -> Path:
    """Run MAFFT multiple sequence alignment.

    Args:
        combined_fasta: Path to combined FASTA file.
        output_dir: Output directory for results.
        threads: Number of threads to use.

    Returns:
        Path to aligned sequences file.
    """
    aln_dir = ensure_dir(output_dir / "aln")
    output_file = aln_dir / "aligned_sequences.msa"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Alignment exists, skipping: {output_file}")
        return output_file

    logger.info(f"Running MAFFT alignment with {threads} threads")

    # Use MAFFT auto mode for best algorithm selection
    cmd = [
        "mafft",
        "--auto",
        "--thread",
        str(threads),
        str(combined_fasta),
    ]

    with open(output_file, "w") as outf:
        result = subprocess.run(cmd, stdout=outf, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.error(f"MAFFT failed: {result.stderr}")
        raise RuntimeError(f"MAFFT failed: {result.stderr}")

    logger.info(f"Alignment completed: {output_file}")
    return output_file


def trim_alignment(
    aligned_file: Path,
    output_dir: Path,
    gap_threshold: float = 0.1,
) -> Path:
    """Trim alignment with TrimAl.

    Args:
        aligned_file: Path to aligned sequences file.
        output_dir: Output directory for results.
        gap_threshold: Gap threshold for trimming (default 0.1 = 10%).

    Returns:
        Path to trimmed alignment file.
    """
    aln_dir = ensure_dir(output_dir / "aln")
    output_file = aln_dir / "trimmed_alignment.msa"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Trimmed alignment exists, skipping: {output_file}")
        return output_file

    logger.info(f"Trimming alignment with gap threshold {gap_threshold}")

    cmd = [
        "trimal",
        "-in",
        str(aligned_file),
        "-out",
        str(output_file),
        "-gt",
        str(gap_threshold),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        logger.error(f"TrimAl failed: {result.stderr}")
        raise RuntimeError(f"TrimAl failed: {result.stderr}")

    logger.info(f"Trimmed alignment: {output_file}")
    return output_file
