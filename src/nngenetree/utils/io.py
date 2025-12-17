"""I/O utility functions for NNGeneTree pipeline."""

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The same path after ensuring it exists.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_fasta_ids(fasta_path: Path) -> list[str]:
    """Read sequence IDs from a FASTA file.

    Args:
        fasta_path: Path to FASTA file.

    Returns:
        List of sequence IDs (without > prefix).
    """
    ids = []
    with open(fasta_path) as f:
        for line in f:
            if line.startswith(">"):
                seq_id = line[1:].split()[0].strip()
                ids.append(seq_id)
    return ids


def write_ids_file(ids: list[str], output_path: Path) -> Path:
    """Write sequence IDs to a file, one per line.

    Args:
        ids: List of sequence IDs.
        output_path: Path to output file.

    Returns:
        Path to the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for seq_id in ids:
            f.write(f"{seq_id}\n")
    return output_path


def count_sequences(fasta_path: Path) -> int:
    """Count sequences in a FASTA file.

    Args:
        fasta_path: Path to FASTA file.

    Returns:
        Number of sequences.
    """
    count = 0
    with open(fasta_path) as f:
        for line in f:
            if line.startswith(">"):
                count += 1
    return count


def parse_blast_m8(blast_path: Path) -> list[dict]:
    """Parse BLAST tabular output (format 6/m8).

    Args:
        blast_path: Path to BLAST m8 output file.

    Returns:
        List of hit dictionaries with standard BLAST fields.
    """
    hits = []
    with open(blast_path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) >= 12:
                hits.append(
                    {
                        "query": fields[0],
                        "subject": fields[1],
                        "pident": float(fields[2]),
                        "length": int(fields[3]),
                        "mismatch": int(fields[4]),
                        "gapopen": int(fields[5]),
                        "qstart": int(fields[6]),
                        "qend": int(fields[7]),
                        "sstart": int(fields[8]),
                        "send": int(fields[9]),
                        "evalue": float(fields[10]),
                        "bitscore": float(fields[11]),
                    }
                )
    return hits


def get_unique_subjects(blast_path: Path, max_hits: int = 50) -> list[str]:
    """Extract unique subject IDs from BLAST results.

    Args:
        blast_path: Path to BLAST m8 output file.
        max_hits: Maximum number of unique subjects to return.

    Returns:
        List of unique subject IDs.
    """
    seen = set()
    subjects = []

    with open(blast_path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) >= 2:
                subject = fields[1]
                if subject not in seen:
                    seen.add(subject)
                    subjects.append(subject)
                    if len(subjects) >= max_hits:
                        break

    return subjects
