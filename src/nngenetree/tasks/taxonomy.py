"""Taxonomy assignment tasks for NNGeneTree pipeline."""

import json
import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pandas as pd
from Bio import Entrez

from ..utils.io import ensure_dir

logger = logging.getLogger(__name__)

# Default paths for local taxonomy lookup
DEFAULT_TAXDUMP_DIR = Path("/clusterfs/jgi/scratch/science/mgs/nelli/databases/nr")
DEFAULT_BLAST_DB = Path("/clusterfs/jgi/scratch/science/mgs/nelli/databases/nr/nr")


class TaxonomyCache:
    """Persistent disk cache for NCBI taxonomy lookups."""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self._dirty = False

    def _load_cache(self) -> dict[str, str]:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save(self) -> None:
        """Save cache to disk."""
        if self._dirty:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(self.cache, indent=2))
            self._dirty = False

    def get(self, accession: str) -> str | None:
        """Get taxonomy for accession from cache."""
        return self.cache.get(accession)

    def set(self, accession: str, taxonomy: str) -> None:
        """Set taxonomy for accession in cache."""
        self.cache[accession] = taxonomy
        self._dirty = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save()


def _lookup_taxonomy_ncbi(
    accession: str,
    entrez_email: str,
    rate_limit_delay: float = 0.34,
) -> str:
    """Look up taxonomy for a protein accession via NCBI Entrez.

    Args:
        accession: Protein accession number.
        entrez_email: Email for NCBI Entrez API.
        rate_limit_delay: Delay between API calls (NCBI limit: 3/sec).

    Returns:
        Taxonomy string (semicolon-delimited lineage) or empty string.
    """
    Entrez.email = entrez_email

    try:
        # Rate limit
        time.sleep(rate_limit_delay)

        # Get protein record to find taxid
        handle = Entrez.efetch(db="protein", id=accession, rettype="gb", retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        if not records:
            return ""

        # Extract taxid from source features
        taxid = None
        for record in records:
            features = record.get("GBSeq_feature-table", [])
            for feature in features:
                if feature.get("GBFeature_key") == "source":
                    quals = feature.get("GBFeature_quals", [])
                    for qual in quals:
                        if qual.get("GBQualifier_name") == "db_xref":
                            value = qual.get("GBQualifier_value", "")
                            if value.startswith("taxon:"):
                                taxid = value.split(":")[1]
                                break

        if not taxid:
            return ""

        # Rate limit before second call
        time.sleep(rate_limit_delay)

        # Get taxonomy lineage
        handle = Entrez.efetch(db="taxonomy", id=taxid, retmode="xml")
        tax_records = Entrez.read(handle)
        handle.close()

        if not tax_records:
            return ""

        lineage = tax_records[0].get("Lineage", "")
        sci_name = tax_records[0].get("ScientificName", "")

        if lineage and sci_name:
            return f"{lineage}; {sci_name}"
        return lineage or sci_name or ""

    except Exception:
        return ""


def _check_local_tools() -> tuple[bool, bool]:
    """Check if blastdbcmd and taxonkit are available.

    Returns:
        Tuple of (blastdbcmd_available, taxonkit_available).
    """
    blastdbcmd = shutil.which("blastdbcmd") is not None
    taxonkit = shutil.which("taxonkit") is not None
    return blastdbcmd, taxonkit


def _batch_get_taxids_from_accessions(
    accessions: list[str],
    blast_db: Path,
) -> dict[str, str]:
    """Get taxids for accessions using blastdbcmd.

    Args:
        accessions: List of protein accessions.
        blast_db: Path to BLAST database.

    Returns:
        Dictionary mapping accession -> taxid.
    """
    if not accessions:
        return {}

    result = {}

    # Write accessions to temp file for batch lookup
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for acc in accessions:
            f.write(f"{acc}\n")
        acc_file = f.name

    try:
        # Use blastdbcmd to get taxids
        cmd = [
            "blastdbcmd",
            "-db",
            str(blast_db),
            "-entry_batch",
            acc_file,
            "-outfmt",
            "%a %T",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if proc.returncode == 0:
            for line in proc.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        acc = parts[0].split(".")[0]  # Remove version
                        taxid = parts[1]
                        result[acc] = taxid
    except Exception as e:
        logger.warning(f"blastdbcmd failed: {e}")
    finally:
        Path(acc_file).unlink(missing_ok=True)

    return result


def _batch_get_lineages_from_taxids(
    taxids: list[str],
    taxdump_dir: Path,
) -> dict[str, str]:
    """Get lineages for taxids using taxonkit.

    Args:
        taxids: List of taxonomy IDs.
        taxdump_dir: Directory containing taxdump files.

    Returns:
        Dictionary mapping taxid -> lineage string.
    """
    if not taxids:
        return {}

    result = {}
    unique_taxids = list(set(taxids))

    # Write taxids to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for tid in unique_taxids:
            f.write(f"{tid}\n")
        taxid_file = f.name

    try:
        # Use taxonkit lineage
        cmd = [
            "taxonkit",
            "lineage",
            "--data-dir",
            str(taxdump_dir),
            taxid_file,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if proc.returncode == 0:
            for line in proc.stdout.strip().split("\n"):
                if line and "\t" in line:
                    parts = line.split("\t", 1)
                    taxid = parts[0]
                    lineage = parts[1] if len(parts) > 1 else ""
                    result[taxid] = lineage
    except Exception as e:
        logger.warning(f"taxonkit failed: {e}")
    finally:
        Path(taxid_file).unlink(missing_ok=True)

    return result


def _lookup_taxonomy_local_batch(
    accessions: list[str],
    blast_db: Path | None = None,
    taxdump_dir: Path | None = None,
) -> dict[str, str]:
    """Look up taxonomy for accessions using local tools (blastdbcmd + taxonkit).

    This is much faster than NCBI API calls and has no rate limits.

    Args:
        accessions: List of protein accessions.
        blast_db: Path to BLAST database (default: NR database).
        taxdump_dir: Directory containing taxdump files.

    Returns:
        Dictionary mapping accession -> taxonomy lineage string.
    """
    blast_db = blast_db or DEFAULT_BLAST_DB
    taxdump_dir = taxdump_dir or DEFAULT_TAXDUMP_DIR

    # Step 1: Get taxids from accessions
    acc_to_taxid = _batch_get_taxids_from_accessions(accessions, blast_db)

    if not acc_to_taxid:
        logger.warning("No taxids found for accessions via blastdbcmd")
        return {}

    # Step 2: Get lineages from taxids
    unique_taxids = list(set(acc_to_taxid.values()))
    taxid_to_lineage = _batch_get_lineages_from_taxids(unique_taxids, taxdump_dir)

    # Step 3: Map accessions to lineages
    result = {}
    for acc in accessions:
        clean_acc = acc.split(".")[0]  # Remove version
        taxid = acc_to_taxid.get(clean_acc)
        if taxid:
            lineage = taxid_to_lineage.get(taxid, "")
            result[acc] = lineage
        else:
            result[acc] = ""

    return result


def assign_taxonomy(
    neighbors_csv: Path,
    output_dir: Path,
    entrez_email: str,
    cache_dir: Path,
    blast_db: Path | None = None,
    taxdump_dir: Path | None = None,
    use_local: bool = True,
) -> tuple[Path, Path]:
    """Add NCBI taxonomy to neighbor results.

    Uses local lookup (blastdbcmd + taxonkit) by default for speed.
    Falls back to NCBI Entrez API if local tools unavailable.

    Args:
        neighbors_csv: Path to CSV file with neighbor results.
        output_dir: Output directory for results.
        entrez_email: Email for NCBI Entrez API (fallback).
        cache_dir: Directory for taxonomy cache.
        blast_db: Path to BLAST database for local lookup.
        taxdump_dir: Directory containing taxdump files.
        use_local: Whether to try local lookup first (default True).

    Returns:
        Tuple of (taxonomy CSV path, JSON summary path).
    """
    ensure_dir(output_dir)
    ensure_dir(cache_dir)

    cache_file = cache_dir / "taxonomy_cache.json"
    output_csv = output_dir / "neighbors_with_taxonomy.csv"
    output_json = output_dir / "taxonomy_summary.json"

    # Skip if output already exists
    if output_csv.exists() and output_csv.stat().st_size > 0:
        logger.info(f"Taxonomy file exists, skipping: {output_csv}")
        return output_csv, output_json

    # Read neighbors
    df = pd.read_csv(neighbors_csv)

    if "accession" not in df.columns:
        # Try to find accession column
        acc_col = None
        for col in ["neighbor_id", "subject", "sseqid"]:
            if col in df.columns:
                acc_col = col
                break
        if acc_col:
            df["accession"] = df[acc_col]
        else:
            logger.warning("No accession column found in neighbors CSV")
            df["taxonomy"] = ""
            df.to_csv(output_csv, index=False)
            return output_csv, _write_taxonomy_summary(df, output_json)

    # Get unique accessions
    all_accessions = df["accession"].tolist()
    unique_accessions = list(set(all_accessions))

    # Check cache first
    with TaxonomyCache(cache_file) as cache:
        cached_results = {}
        uncached_accessions = []

        for acc in unique_accessions:
            cached_tax = cache.get(acc)
            if cached_tax is not None:
                cached_results[acc] = cached_tax
            else:
                uncached_accessions.append(acc)

        logger.info(
            f"Taxonomy lookup: {len(cached_results)} cached, "
            f"{len(uncached_accessions)} to look up"
        )

        # Try local lookup first (much faster, no rate limits)
        local_results = {}
        if use_local and uncached_accessions:
            has_blastdbcmd, has_taxonkit = _check_local_tools()

            if has_blastdbcmd and has_taxonkit:
                logger.info(
                    f"Using local taxonomy lookup for {len(uncached_accessions)} accessions"
                )
                local_results = _lookup_taxonomy_local_batch(
                    uncached_accessions,
                    blast_db=blast_db,
                    taxdump_dir=taxdump_dir,
                )

                # Cache the results
                for acc, tax in local_results.items():
                    cache.set(acc, tax)

                # Find accessions still missing
                uncached_accessions = [
                    acc
                    for acc in uncached_accessions
                    if acc not in local_results or not local_results[acc]
                ]

                logger.info(
                    f"Local lookup: {len(local_results)} found, "
                    f"{len(uncached_accessions)} remaining"
                )
            else:
                logger.warning(
                    f"Local tools not available (blastdbcmd={has_blastdbcmd}, "
                    f"taxonkit={has_taxonkit}), using NCBI API"
                )

        # Fall back to NCBI API for remaining accessions
        ncbi_results = {}
        if uncached_accessions:
            logger.info(
                f"Using NCBI API for {len(uncached_accessions)} remaining accessions"
            )
            for idx, acc in enumerate(uncached_accessions):
                tax = _lookup_taxonomy_ncbi(acc, entrez_email)
                ncbi_results[acc] = tax
                cache.set(acc, tax)

                if (idx + 1) % 10 == 0:
                    logger.info(f"NCBI API progress: {idx + 1}/{len(uncached_accessions)}")

        # Combine all results
        all_results = {**cached_results, **local_results, **ncbi_results}

        # Map to dataframe
        taxonomies = [all_results.get(acc, "") for acc in all_accessions]

    df["taxonomy"] = taxonomies
    df.to_csv(output_csv, index=False)

    # Log summary
    found = sum(1 for t in taxonomies if t)
    logger.info(
        f"Taxonomy complete: {len(taxonomies)} accessions, "
        f"{found} with taxonomy ({100*found/len(taxonomies):.1f}%)"
    )

    summary_path = _write_taxonomy_summary(df, output_json)

    return output_csv, summary_path


def _write_taxonomy_summary(df: pd.DataFrame, output_path: Path) -> Path:
    """Write taxonomy summary JSON."""
    summary = {
        "total_sequences": len(df),
        "with_taxonomy": len(df[df["taxonomy"].str.len() > 0]),
        "without_taxonomy": len(df[df["taxonomy"].str.len() == 0]),
    }

    # Count by domain/kingdom
    domain_counts: dict[str, int] = {}
    for tax in df["taxonomy"]:
        if not tax:
            continue
        parts = tax.split(";")
        if parts:
            domain = parts[0].strip()
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    summary["domain_counts"] = domain_counts

    output_path.write_text(json.dumps(summary, indent=2))
    return output_path
