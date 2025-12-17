"""Main pipeline flow for NNGeneTree using native Dask."""

import logging
from pathlib import Path

from ..config import PipelineConfig
from ..tasks.alignment import align_sequences, combine_sequences, trim_alignment
from ..tasks.analysis import (
    calculate_tree_stats,
    combine_placement_results,
    decorate_tree,
    extract_closest_neighbors,
    extract_phylogenetic_placement,
)
from ..tasks.blast import diamond_blastp, extract_hits, process_blast_results
from ..tasks.phylogeny import build_tree
from ..tasks.taxonomy import assign_taxonomy
from ..utils.cluster import get_cluster_info, get_dask_client
from ..utils.io import ensure_dir

logger = logging.getLogger(__name__)


def process_single_sample(
    fasta_file: Path,
    config: PipelineConfig,
    output_dir: Path,
) -> Path | None:
    """Process a single FASTA file through the NNGeneTree pipeline.

    This function runs sequentially for each sample.
    Parallelization happens at the sample level via Dask.

    Args:
        fasta_file: Path to input FASTA file.
        config: Pipeline configuration.
        output_dir: Output directory for this sample.

    Returns:
        Path to placement results JSON, or None if processing failed.
    """
    sample_id = fasta_file.stem
    sample_dir = ensure_dir(output_dir / sample_id)

    logger.info(f"Processing sample: {sample_id}")

    try:
        # Step 1: DIAMOND BLASTP
        blast_result = diamond_blastp(
            query_fasta=fasta_file,
            blast_db=config.blast_db,
            output_dir=sample_dir,
            threads=config.blast_resources.threads,
            max_hits=config.blast_hits,
        )

        # Step 2: Process BLAST results
        subjects = process_blast_results(
            blast_file=blast_result,
            output_dir=sample_dir,
            max_hits=50,
            min_hits=5,
        )

        # Check if we have enough hits
        if subjects is None:
            logger.warning(f"Insufficient BLAST hits for {sample_id}, skipping")
            return None

        # Step 3: Extract hit sequences
        hits = extract_hits(
            subjects_file=subjects,
            blast_db=config.blast_db,
            output_dir=sample_dir,
        )

        # Step 4: Combine sequences
        combined = combine_sequences(
            query_fasta=fasta_file,
            hits_fasta=hits,
            output_dir=sample_dir,
        )

        # Step 5: Align sequences
        aligned = align_sequences(
            combined_fasta=combined,
            output_dir=sample_dir,
            threads=config.align_resources.threads,
        )

        # Step 6: Trim alignment
        trimmed = trim_alignment(
            aligned_file=aligned,
            output_dir=sample_dir,
        )

        # Step 7: Build tree
        tree = build_tree(
            trimmed_alignment=trimmed,
            output_dir=sample_dir,
            builder=config.tree_builder,
            threads=config.tree_resources.threads,
        )

        # Step 8: Extract closest neighbors
        neighbors = extract_closest_neighbors(
            tree_file=tree,
            query_fasta=fasta_file,
            subjects_file=subjects,
            output_dir=sample_dir,
            num_neighbors=config.closest_neighbors,
            query_prefixes=config.get_query_prefix_list(),
        )

        # Step 9: Assign taxonomy (uses local lookup by default)
        taxonomy_csv, _ = assign_taxonomy(
            neighbors_csv=neighbors,
            output_dir=sample_dir,
            entrez_email=config.entrez_email,
            cache_dir=config.cache_dir,
            blast_db=config.blast_db,
        )

        # Step 10: Decorate tree
        decorate_tree(
            tree_file=tree,
            taxonomy_file=taxonomy_csv,
            query_fasta=fasta_file,
            output_dir=sample_dir,
        )

        # Step 11: Calculate tree stats
        calculate_tree_stats(
            tree_file=tree,
            taxonomy_file=taxonomy_csv,
            combined_fasta=combined,
            output_dir=sample_dir,
        )

        # Step 12: Extract phylogenetic placement
        placement = extract_phylogenetic_placement(
            tree_file=tree,
            output_dir=sample_dir,
            neighbors_file=neighbors,
            taxonomy_file=taxonomy_csv,
            query_prefixes=config.get_query_prefix_list(),
        )

        logger.info(f"Completed sample: {sample_id}")
        return placement

    except Exception as e:
        logger.error(f"Error processing {sample_id}: {e}")
        return None


def nngenetree_pipeline(config: PipelineConfig) -> Path:
    """Main NNGeneTree phylogenetic analysis pipeline.

    Uses Dask for parallel processing of samples.

    Args:
        config: Pipeline configuration.

    Returns:
        Path to combined placement results JSON.
    """
    # Setup output directory
    output_dir = config.get_output_dir()
    ensure_dir(output_dir)

    # Log configuration
    cluster_info = get_cluster_info(config)
    logger.info("NNGeneTree Pipeline Starting")
    logger.info(f"  Mode: {config.mode}")
    logger.info(f"  Input: {config.input_dir}")
    logger.info(f"  Output: {output_dir}")
    logger.info(f"  Cluster: {cluster_info}")

    # Find all input FASTA files
    input_files = sorted(config.input_dir.glob("*.faa"))
    logger.info(f"Found {len(input_files)} input FASTA files")

    if not input_files:
        raise ValueError(f"No .faa files found in {config.input_dir}")

    # Process samples in parallel using Dask
    with get_dask_client(config) as client:
        logger.info(f"Dask dashboard: {client.dashboard_link}")

        # Submit all samples for parallel processing
        futures = []
        for fasta_file in input_files:
            future = client.submit(
                process_single_sample,
                fasta_file,
                config,
                output_dir,
                pure=False,  # Don't cache results (we handle caching internally)
            )
            futures.append(future)

        # Gather results as they complete
        placement_files = []
        for future in futures:
            try:
                result = future.result()
                if result is not None:
                    placement_files.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

    logger.info(f"Completed {len(placement_files)}/{len(input_files)} samples")

    # Combine all results
    final_result = combine_placement_results(
        placement_files=placement_files,
        output_dir=output_dir,
    )

    logger.info(f"Pipeline complete! Results: {final_result}")
    return final_result


def run_pipeline(config: PipelineConfig) -> Path:
    """Run the NNGeneTree pipeline.

    This is the main entry point.

    Args:
        config: Pipeline configuration.

    Returns:
        Path to combined placement results JSON.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return nngenetree_pipeline(config)
