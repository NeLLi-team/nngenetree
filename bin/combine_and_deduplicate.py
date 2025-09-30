#!/usr/bin/env python
"""
Combine query sequences with extracted BLAST hits while removing duplicates.
Handles two types of duplicates:
1. Exact sequence ID matches
2. Sequence content matches (same amino acid sequence with different IDs)
"""

import sys
import argparse
from collections import OrderedDict

def parse_fasta(fasta_file):
    """
    Parse FASTA file and return OrderedDict of {header: sequence}.
    Keeps only the first part of header (up to first whitespace).
    """
    sequences = OrderedDict()
    current_header = None
    current_seq = []

    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith('>'):
                # Save previous sequence if exists
                if current_header is not None:
                    sequences[current_header] = ''.join(current_seq)

                # Extract ID (first part before whitespace)
                current_header = line[1:].split()[0] if ' ' in line or '\t' in line else line[1:]
                current_seq = []
            else:
                current_seq.append(line)

        # Save last sequence
        if current_header is not None:
            sequences[current_header] = ''.join(current_seq)

    return sequences

def main():
    parser = argparse.ArgumentParser(
        description='Combine query and hit sequences while removing duplicates'
    )
    parser.add_argument('query_file', help='Query FASTA file')
    parser.add_argument('hits_file', help='Extracted hits FASTA file')
    parser.add_argument('output_file', help='Combined output FASTA file')
    parser.add_argument('--deduplicate-by-sequence', action='store_true',
                        help='Also remove sequences with identical content (not just IDs)')

    args = parser.parse_args()

    # Parse query sequences (these take priority)
    print(f"Reading query sequences from {args.query_file}...", file=sys.stderr)
    query_seqs = parse_fasta(args.query_file)
    print(f"  Found {len(query_seqs)} query sequences", file=sys.stderr)

    # Parse hit sequences
    print(f"Reading hit sequences from {args.hits_file}...", file=sys.stderr)
    hit_seqs = parse_fasta(args.hits_file)
    print(f"  Found {len(hit_seqs)} hit sequences", file=sys.stderr)

    # Track query IDs and optionally sequence content
    query_ids = set(query_seqs.keys())
    seen_sequences = set(query_seqs.values()) if args.deduplicate_by_sequence else set()

    # Filter hits: remove if ID matches query or sequence content matches query
    filtered_hits = OrderedDict()
    duplicate_ids = 0
    duplicate_seqs = 0

    for hit_id, hit_seq in hit_seqs.items():
        # Check for ID match
        if hit_id in query_ids:
            duplicate_ids += 1
            continue

        # Check for sequence content match (if enabled)
        if args.deduplicate_by_sequence and hit_seq in seen_sequences:
            duplicate_seqs += 1
            continue

        # Keep this hit
        filtered_hits[hit_id] = hit_seq
        if args.deduplicate_by_sequence:
            seen_sequences.add(hit_seq)

    # Write combined sequences: queries first, then filtered hits
    print(f"Writing combined sequences to {args.output_file}...", file=sys.stderr)
    with open(args.output_file, 'w') as f:
        # Write queries
        for header, seq in query_seqs.items():
            f.write(f">{header}\n{seq}\n")

        # Write filtered hits
        for header, seq in filtered_hits.items():
            f.write(f">{header}\n{seq}\n")

    # Report statistics
    total_output = len(query_seqs) + len(filtered_hits)
    print(f"\n=== Deduplication Summary ===", file=sys.stderr)
    print(f"Query sequences: {len(query_seqs)}", file=sys.stderr)
    print(f"Hit sequences (before filtering): {len(hit_seqs)}", file=sys.stderr)
    print(f"Removed due to ID match: {duplicate_ids}", file=sys.stderr)
    if args.deduplicate_by_sequence:
        print(f"Removed due to sequence match: {duplicate_seqs}", file=sys.stderr)
    print(f"Hit sequences (after filtering): {len(filtered_hits)}", file=sys.stderr)
    print(f"Total sequences in output: {total_output}", file=sys.stderr)

if __name__ == "__main__":
    main()