"""BLAST-related tasks for NNGeneTree pipeline."""

import logging
import subprocess
from pathlib import Path

from ..utils.io import ensure_dir, get_unique_subjects, write_ids_file

logger = logging.getLogger(__name__)


def diamond_blastp(
    query_fasta: Path,
    blast_db: Path,
    output_dir: Path,
    threads: int = 8,
    max_hits: int = 20,
) -> Path:
    """Run DIAMOND BLASTP against a protein database.

    Args:
        query_fasta: Path to query FASTA file.
        blast_db: Path to DIAMOND database (without .dmnd extension).
        output_dir: Output directory for results.
        threads: Number of threads to use.
        max_hits: Maximum number of hits per query.

    Returns:
        Path to BLAST results file (m8 format).
    """
    ensure_dir(output_dir)
    output_file = output_dir / "blast_results.m8"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"BLAST results exist, skipping: {output_file}")
        return output_file

    # Determine database path
    db_path = blast_db
    if not str(blast_db).endswith(".dmnd"):
        dmnd_path = Path(f"{blast_db}.dmnd")
        if dmnd_path.exists():
            db_path = dmnd_path

    logger.info(f"Running DIAMOND BLASTP: {query_fasta.name} against {db_path.name}")

    cmd = [
        "diamond",
        "blastp",
        "-d",
        str(db_path),
        "-q",
        str(query_fasta),
        "-o",
        str(output_file),
        "-p",
        str(threads),
        "-k",
        str(max_hits),
        "--outfmt",
        "6",
        "qseqid",
        "sseqid",
        "pident",
        "length",
        "mismatch",
        "gapopen",
        "qstart",
        "qend",
        "sstart",
        "send",
        "evalue",
        "bitscore",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        logger.error(f"DIAMOND BLASTP failed: {result.stderr}")
        raise RuntimeError(f"DIAMOND BLASTP failed: {result.stderr}")

    logger.info(f"BLAST completed: {output_file}")
    return output_file


def process_blast_results(
    blast_file: Path,
    output_dir: Path,
    max_hits: int = 50,
    min_hits: int = 5,
) -> Path | None:
    """Extract unique subject IDs from BLAST results.

    Args:
        blast_file: Path to BLAST m8 output file.
        output_dir: Output directory for results.
        max_hits: Maximum number of unique subjects to extract.
        min_hits: Minimum number of hits required to proceed.

    Returns:
        Path to subjects file, or None if insufficient hits.
    """
    ensure_dir(output_dir)
    subjects_file = output_dir / "subjects.txt"

    # Skip if output already exists
    if subjects_file.exists() and subjects_file.stat().st_size > 0:
        logger.info(f"Subjects file exists, skipping: {subjects_file}")
        return subjects_file

    subjects = get_unique_subjects(blast_file, max_hits=max_hits)

    if len(subjects) < min_hits:
        logger.warning(
            f"Only {len(subjects)} unique hits found (minimum: {min_hits}). "
            "Skipping this sample."
        )
        return None

    write_ids_file(subjects, subjects_file)

    logger.info(f"Extracted {len(subjects)} unique subjects to {subjects_file}")
    return subjects_file


def extract_hits(
    subjects_file: Path,
    blast_db: Path,
    output_dir: Path,
) -> Path:
    """Extract hit sequences from BLAST database.

    Args:
        subjects_file: Path to file containing subject IDs.
        blast_db: Path to BLAST database.
        output_dir: Output directory for results.

    Returns:
        Path to extracted sequences FASTA file.
    """
    ensure_dir(output_dir)
    output_file = output_dir / "extracted_hits.faa"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Extracted hits exist, skipping: {output_file}")
        return output_file

    logger.info(f"Extracting sequences from {blast_db.name}")

    cmd = [
        "blastdbcmd",
        "-db",
        str(blast_db),
        "-entry_batch",
        str(subjects_file),
        "-out",
        str(output_file),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        logger.error(f"blastdbcmd failed: {result.stderr}")
        raise RuntimeError(f"blastdbcmd failed: {result.stderr}")

    logger.info(f"Extracted sequences to {output_file}")
    return output_file
