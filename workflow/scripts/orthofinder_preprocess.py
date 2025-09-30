#!/usr/bin/env python
"""
OrthoFinder preprocessing for NNGeneTree pipeline

This script:
1. Runs OrthoFinder on a directory of genome FASTA files
2. Extracts orthogroups based on target substrings
3. Creates individual FASTA files for each orthogroup
"""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path
from Bio import SeqIO
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_genome_headers(genomes_dir):
    """
    Validate that genome headers follow the format: {genome_id}|{contig_id}_{protein_id}
    """
    genomes_dir = Path(genomes_dir)
    valid = True

    for faa_file in genomes_dir.glob("*.faa"):
        genome_id = faa_file.stem
        logger.info(f"Checking genome file: {faa_file}")

        for record in SeqIO.parse(faa_file, "fasta"):
            header_parts = record.id.split("|")

            if len(header_parts) != 2:
                logger.error(f"Invalid header format in {faa_file}: {record.id}")
                logger.error(f"Expected format: {genome_id}|contig_id_protein_num")
                valid = False
                continue

            if header_parts[0] != genome_id:
                logger.error(f"Genome ID mismatch in {faa_file}: {header_parts[0]} != {genome_id}")
                valid = False

            # Check for protein number suffix
            contig_protein = header_parts[1]
            if "_" not in contig_protein or not contig_protein.split("_")[-1].isdigit():
                logger.warning(f"Protein ID should end with _number: {record.id}")

    return valid


def run_orthofinder(genomes_dir, output_dir, threads=16):
    """
    Run OrthoFinder on the genome directory
    """
    logger.info(f"Running OrthoFinder on {genomes_dir}")

    # Handle output directory - OrthoFinder requires it doesn't exist
    output_dir = Path(output_dir)
    if output_dir.exists():
        logger.info(f"Removing existing OrthoFinder directory: {output_dir}")
        shutil.rmtree(output_dir)

    # Parent directory must exist
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    # Run OrthoFinder
    cmd = [
        "orthofinder",
        "-f", str(genomes_dir),
        "-o", str(output_dir),
        "-t", str(threads),
        "-M", "msa",  # Use MSA method for better accuracy
        "-S", "diamond"  # Use DIAMOND for faster searches
    ]

    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info("OrthoFinder completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"OrthoFinder failed: {e.stderr}")
        return False


def parse_orthogroups(orthogroups_file, genomes_dir):
    """
    Parse OrthoFinder Orthogroups.tsv file and extract sequences
    Returns dict: {OG_id: {genome_id: [protein_ids]}}
    """
    orthogroups = {}

    with open(orthogroups_file, 'r') as f:
        # Skip header
        header = f.readline().strip().split('\t')
        genome_names = header[1:]  # First column is Orthogroup

        for line in f:
            parts = line.strip().split('\t')
            og_id = parts[0]

            orthogroups[og_id] = defaultdict(list)

            for i, proteins_str in enumerate(parts[1:], 0):
                if proteins_str:  # Skip empty cells
                    genome_name = genome_names[i]
                    # OrthoFinder lists multiple proteins separated by comma and space
                    proteins = [p.strip() for p in proteins_str.split(',')]
                    orthogroups[og_id][genome_name] = proteins

    return orthogroups


def filter_orthogroups_by_target(orthogroups, targets):
    """
    Filter orthogroups to only include those containing proteins matching target substrings
    """
    if not targets:
        return orthogroups

    filtered = {}

    for og_id, genomes in orthogroups.items():
        include_og = False

        for genome, proteins in genomes.items():
            for protein_id in proteins:
                for target in targets:
                    if target in protein_id:
                        include_og = True
                        break
                if include_og:
                    break
            if include_og:
                break

        if include_og:
            filtered[og_id] = genomes
            logger.info(f"Including {og_id} - matches target criteria")

    logger.info(f"Filtered {len(filtered)} orthogroups from {len(orthogroups)} total")
    return filtered


def extract_orthogroup_sequences(orthogroups, genomes_dir, output_dir):
    """
    Extract sequences for each orthogroup and write to individual FASTA files
    """
    genomes_dir = Path(genomes_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load all genome sequences into memory
    genome_sequences = {}
    for faa_file in genomes_dir.glob("*.faa"):
        genome_id = faa_file.stem
        genome_sequences[genome_id] = {
            record.id: record for record in SeqIO.parse(faa_file, "fasta")
        }

    # Extract sequences for each orthogroup
    extracted_count = 0
    for og_id, genomes in orthogroups.items():
        og_sequences = []

        for genome_name, protein_ids in genomes.items():
            if genome_name in genome_sequences:
                for protein_id in protein_ids:
                    if protein_id in genome_sequences[genome_name]:
                        og_sequences.append(genome_sequences[genome_name][protein_id])
                    else:
                        logger.warning(f"Protein {protein_id} not found in {genome_name}")

        if og_sequences:
            output_file = output_dir / f"{og_id}.faa"
            SeqIO.write(og_sequences, output_file, "fasta")
            logger.info(f"Wrote {len(og_sequences)} sequences to {output_file}")
            extracted_count += 1

    logger.info(f"Extracted {extracted_count} orthogroup FASTA files")
    return extracted_count


def main():
    parser = argparse.ArgumentParser(
        description="OrthoFinder preprocessing for NNGeneTree pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Run on all orthogroups
  python orthofinder_preprocess.py --genomes_faa_dir example2/genomes --output_dir example2/orthogroups

  # Filter for specific targets
  python orthofinder_preprocess.py --genomes_faa_dir example2/genomes --output_dir example2/orthogroups --target "Hype_50_,Hper|contig_4_"

  # Skip OrthoFinder if already run
  python orthofinder_preprocess.py --genomes_faa_dir example2/genomes --output_dir example2/orthogroups --orthofinder_results OrthoFinder_results
        """
    )

    parser.add_argument(
        "--genomes_faa_dir",
        required=True,
        help="Directory containing genome FASTA files ({genome_id}.faa)"
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Output directory for orthogroup FASTA files"
    )

    parser.add_argument(
        "--target",
        help="Comma-separated list of substrings to filter orthogroups (e.g., 'Hype_50_,Hper|contig_4_')"
    )

    parser.add_argument(
        "--orthofinder_results",
        help="Path to existing OrthoFinder results directory (skip OrthoFinder run)"
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=16,
        help="Number of threads for OrthoFinder (default: 16)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output directory"
    )

    args = parser.parse_args()

    # Validate genome headers
    if not validate_genome_headers(args.genomes_faa_dir):
        logger.error("Genome header validation failed. Please fix headers before proceeding.")
        sys.exit(1)

    # Check if output directory exists
    output_dir = Path(args.output_dir)
    if output_dir.exists() and not args.force:
        logger.error(f"Output directory {output_dir} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Run or locate OrthoFinder results
    if args.orthofinder_results:
        orthofinder_dir = Path(args.orthofinder_results)
        if not orthofinder_dir.exists():
            logger.error(f"OrthoFinder results directory not found: {orthofinder_dir}")
            sys.exit(1)
    else:
        # Run OrthoFinder - put results in parent directory of output_dir
        output_parent = Path(args.output_dir).parent
        orthofinder_dir = output_parent / "OrthoFinder_results"
        if not run_orthofinder(args.genomes_faa_dir, orthofinder_dir, args.threads):
            logger.error("OrthoFinder failed")
            sys.exit(1)

    # Find Orthogroups.tsv file
    orthogroups_files = list(orthofinder_dir.rglob("Orthogroups.tsv"))
    if not orthogroups_files:
        logger.error(f"Could not find Orthogroups.tsv in {orthofinder_dir}")
        sys.exit(1)

    orthogroups_file = orthogroups_files[0]
    logger.info(f"Using orthogroups file: {orthogroups_file}")

    # Parse orthogroups
    orthogroups = parse_orthogroups(orthogroups_file, args.genomes_faa_dir)
    logger.info(f"Parsed {len(orthogroups)} orthogroups")

    # Filter by targets if specified
    if args.target:
        targets = [t.strip() for t in args.target.split(',')]
        logger.info(f"Filtering for targets: {targets}")
        orthogroups = filter_orthogroups_by_target(orthogroups, targets)

    # Extract sequences
    extracted = extract_orthogroup_sequences(orthogroups, args.genomes_faa_dir, args.output_dir)

    logger.info(f"✅ Successfully extracted {extracted} orthogroup files to {args.output_dir}")
    logger.info(f"These files can now be used as input for the NNGeneTree pipeline")


if __name__ == "__main__":
    main()