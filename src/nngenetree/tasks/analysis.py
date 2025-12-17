"""Analysis tasks for NNGeneTree pipeline."""

import json
import logging
from pathlib import Path

import pandas as pd
from ete3 import Tree

from ..utils.io import ensure_dir, read_fasta_ids

logger = logging.getLogger(__name__)


def extract_closest_neighbors(
    tree_file: Path,
    query_fasta: Path,
    subjects_file: Path,
    output_dir: Path,
    num_neighbors: int = 10,
    query_prefixes: list[str] | None = None,
) -> Path:
    """Extract closest neighbors from phylogenetic tree.

    Args:
        tree_file: Path to tree file in Newick format.
        query_fasta: Path to query FASTA file.
        subjects_file: Path to subjects file.
        output_dir: Output directory for results.
        num_neighbors: Number of closest neighbors to extract.
        query_prefixes: Prefixes to identify query sequences.

    Returns:
        Path to neighbors CSV file.
    """
    ensure_dir(output_dir)
    output_file = output_dir / "closest_neighbors.csv"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Neighbors file exists, skipping: {output_file}")
        return output_file

    # Load tree
    tree = Tree(str(tree_file))

    # Get query IDs
    query_ids = set(read_fasta_ids(query_fasta))

    # If prefixes provided, also match by prefix
    if query_prefixes:
        for leaf in tree.get_leaves():
            for prefix in query_prefixes:
                if leaf.name.startswith(prefix):
                    query_ids.add(leaf.name)
                    break

    # Read subject IDs
    subject_ids = set()
    if subjects_file.exists():
        subject_ids = set(subjects_file.read_text().strip().split("\n"))

    # Find neighbors for each query
    results = []
    for query_id in query_ids:
        # Find query node in tree
        query_nodes = tree.search_nodes(name=query_id)
        if not query_nodes:
            # Try partial match
            for leaf in tree.get_leaves():
                if query_id in leaf.name or leaf.name in query_id:
                    query_nodes = [leaf]
                    break

        if not query_nodes:
            logger.warning(f"Query {query_id} not found in tree")
            continue

        query_node = query_nodes[0]

        # Get distances to all other leaves
        distances = []
        for leaf in tree.get_leaves():
            if leaf.name != query_node.name and leaf.name not in query_ids:
                dist = query_node.get_distance(leaf)
                distances.append((leaf.name, dist))

        # Sort by distance and take closest
        distances.sort(key=lambda x: x[1])
        for rank, (neighbor_id, dist) in enumerate(distances[:num_neighbors], 1):
            results.append(
                {
                    "query_id": query_id,
                    "neighbor_id": neighbor_id,
                    "distance": dist,
                    "rank": rank,
                    "accession": neighbor_id.split()[0],
                }
            )

    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)

    logger.info(f"Extracted {len(results)} neighbor relationships to {output_file}")
    return output_file


def decorate_tree(
    tree_file: Path,
    taxonomy_file: Path,
    query_fasta: Path,
    output_dir: Path,
) -> Path:
    """Decorate tree with taxonomy and query annotations.

    Args:
        tree_file: Path to tree file in Newick format.
        taxonomy_file: Path to taxonomy CSV file.
        query_fasta: Path to query FASTA file.
        output_dir: Output directory for results.

    Returns:
        Path to decorated tree file.
    """
    tree_dir = ensure_dir(output_dir / "tree")
    output_file = tree_dir / "decorated_tree.nwk"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Decorated tree exists, skipping: {output_file}")
        return output_file

    # Load tree
    tree = Tree(str(tree_file))

    # Load taxonomy
    tax_df = pd.read_csv(taxonomy_file)
    tax_dict = {}
    if "accession" in tax_df.columns and "taxonomy" in tax_df.columns:
        tax_dict = dict(zip(tax_df["accession"], tax_df["taxonomy"]))

    # Get query IDs
    query_ids = set(read_fasta_ids(query_fasta))

    # Annotate leaves
    for leaf in tree.get_leaves():
        accession = leaf.name.split()[0]

        # Add taxonomy to name if available
        if accession in tax_dict and tax_dict[accession]:
            # Extract domain/kingdom from taxonomy
            tax = tax_dict[accession]
            parts = tax.split(";")
            if len(parts) >= 2:
                short_tax = parts[-1].strip()[:20]
                leaf.name = f"{leaf.name}|{short_tax}"

        # Mark queries
        if accession in query_ids or leaf.name in query_ids:
            leaf.name = f"[QUERY]{leaf.name}"

    # Write decorated tree
    tree.write(outfile=str(output_file), format=1)

    logger.info(f"Decorated tree written to {output_file}")
    return output_file


def calculate_tree_stats(
    tree_file: Path,
    taxonomy_file: Path,
    combined_fasta: Path,
    output_dir: Path,
) -> Path:
    """Calculate tree statistics and summary.

    Args:
        tree_file: Path to tree file in Newick format.
        taxonomy_file: Path to taxonomy CSV file.
        combined_fasta: Path to combined sequences FASTA.
        output_dir: Output directory for results.

    Returns:
        Path to statistics JSON file.
    """
    ensure_dir(output_dir)
    output_file = output_dir / "tree_stats.json"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Tree stats exist, skipping: {output_file}")
        return output_file

    # Load tree
    tree = Tree(str(tree_file))

    # Basic tree stats
    leaves = tree.get_leaves()
    stats = {
        "num_leaves": len(leaves),
        "num_internal_nodes": len(tree.get_descendants()) - len(leaves),
        "tree_length": sum(n.dist for n in tree.traverse()),
        "max_depth": max(tree.get_distance(leaf) for leaf in leaves),
    }

    # Taxonomy distribution
    tax_df = pd.read_csv(taxonomy_file)
    if "taxonomy" in tax_df.columns:
        domain_counts: dict[str, int] = {}
        for tax in tax_df["taxonomy"].dropna():
            if tax:
                parts = tax.split(";")
                if parts:
                    domain = parts[0].strip()
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
        stats["taxonomy_distribution"] = domain_counts

    # Write stats
    output_file.write_text(json.dumps(stats, indent=2))

    logger.info(f"Tree stats written to {output_file}")
    return output_file


def extract_phylogenetic_placement(
    tree_file: Path,
    output_dir: Path,
    neighbors_file: Path,
    taxonomy_file: Path,
    query_prefixes: list[str] | None = None,
) -> Path:
    """Extract phylogenetic placement results for queries.

    Args:
        tree_file: Path to tree file in Newick format.
        output_dir: Output directory for results.
        neighbors_file: Path to neighbors CSV file.
        taxonomy_file: Path to taxonomy CSV file.
        query_prefixes: Prefixes to identify query sequences.

    Returns:
        Path to placement results JSON file.
    """
    ensure_dir(output_dir)
    output_file = output_dir / "placement_results.json"

    # Skip if output already exists
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info(f"Placement results exist, skipping: {output_file}")
        return output_file

    # Load data
    neighbors_df = pd.read_csv(neighbors_file)
    taxonomy_df = pd.read_csv(taxonomy_file)

    # Build taxonomy lookup
    tax_dict = {}
    if "accession" in taxonomy_df.columns and "taxonomy" in taxonomy_df.columns:
        tax_dict = dict(zip(taxonomy_df["accession"], taxonomy_df["taxonomy"]))

    # Extract placements per query
    placements = {}
    query_ids = neighbors_df["query_id"].unique() if "query_id" in neighbors_df else []

    for query_id in query_ids:
        query_neighbors = neighbors_df[neighbors_df["query_id"] == query_id]

        neighbor_info = []
        for _, row in query_neighbors.iterrows():
            neighbor_id = row.get("neighbor_id", row.get("accession", ""))
            accession = neighbor_id.split()[0]
            taxonomy = tax_dict.get(accession, "")

            neighbor_info.append(
                {
                    "neighbor_id": neighbor_id,
                    "accession": accession,
                    "distance": row.get("distance", 0),
                    "rank": row.get("rank", 0),
                    "taxonomy": taxonomy,
                }
            )

        # Determine consensus taxonomy
        consensus = _get_consensus_taxonomy(neighbor_info)

        placements[query_id] = {
            "query_id": query_id,
            "num_neighbors": len(neighbor_info),
            "neighbors": neighbor_info,
            "consensus_taxonomy": consensus,
        }

    # Write results
    output_file.write_text(json.dumps(placements, indent=2))

    logger.info(f"Placement results for {len(placements)} queries written to {output_file}")
    return output_file


def _get_consensus_taxonomy(neighbors: list[dict]) -> str:
    """Determine consensus taxonomy from neighbors."""
    if not neighbors:
        return ""

    # Get all taxonomies
    taxonomies = [n["taxonomy"] for n in neighbors if n.get("taxonomy")]
    if not taxonomies:
        return ""

    # Find common prefix across all taxonomies
    split_taxonomies = [t.split(";") for t in taxonomies]
    min_len = min(len(t) for t in split_taxonomies)

    consensus_parts = []
    for i in range(min_len):
        parts_at_level = [t[i].strip() for t in split_taxonomies]
        if len(set(parts_at_level)) == 1:
            consensus_parts.append(parts_at_level[0])
        else:
            break

    return "; ".join(consensus_parts) if consensus_parts else taxonomies[0]


def combine_placement_results(
    placement_files: list[Path],
    output_dir: Path,
) -> Path:
    """Combine placement results from multiple samples.

    Args:
        placement_files: List of paths to placement JSON files.
        output_dir: Output directory for combined results.

    Returns:
        Path to combined results JSON file.
    """
    ensure_dir(output_dir)
    output_file = output_dir / "combined_placement_results.json"

    combined = {}
    for pf in placement_files:
        if pf is None or not pf.exists():
            continue

        try:
            data = json.loads(pf.read_text())
            # Add sample ID from directory name
            sample_id = pf.parent.name
            for query_id, placement in data.items():
                combined_key = f"{sample_id}/{query_id}"
                placement["sample_id"] = sample_id
                combined[combined_key] = placement
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error reading {pf}: {e}")
            continue

    # Write combined results
    output_file.write_text(json.dumps(combined, indent=2))

    logger.info(f"Combined {len(combined)} placements to {output_file}")
    return output_file
