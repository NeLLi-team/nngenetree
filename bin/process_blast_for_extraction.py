#!/usr/bin/env python
"""
Process BLAST results to extract top N hits per query for sequence extraction.
Maintains all hits per query rather than deduplicating globally.
"""

import sys
import argparse
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser(description='Process BLAST results for sequence extraction')
    parser.add_argument('blast_file', help='BLAST output file (tabular format)')
    parser.add_argument('output_file', help='Output file with subject IDs to extract')
    parser.add_argument('--max-hits', type=int, default=50, help='Maximum hits per query (default: 50)')
    parser.add_argument('--min-hits', type=int, default=5, help='Minimum hits per query to proceed (default: 5)')

    args = parser.parse_args()

    # Read BLAST results and group by query
    query_hits = defaultdict(list)

    with open(args.blast_file, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                query = parts[0]
                subject = parts[1]

                # Skip self-hits
                if query == subject:
                    continue

                query_hits[query].append(subject)

    # Extract top N hits per query (preserving order within each query)
    # But deduplicate across all queries to avoid duplicate sequences in tree
    all_subjects_ordered = []  # Maintains order
    seen_subjects = set()       # Tracks what we've already added
    queries_with_few_hits = []

    for query, subjects in query_hits.items():
        # Take up to max_hits per query
        query_subject_count = 0
        for subject in subjects:
            if query_subject_count >= args.max_hits:
                break

            # Only add if we haven't seen this subject before
            if subject not in seen_subjects:
                all_subjects_ordered.append(subject)
                seen_subjects.add(subject)
                query_subject_count += 1

        if query_subject_count < args.min_hits:
            queries_with_few_hits.append(f"{query}: {query_subject_count} unique hits")

    # Write unique subjects only
    with open(args.output_file, 'w') as f:
        for subject in all_subjects_ordered:
            f.write(f"{subject}\n")

    # Report statistics
    print(f"Processed {len(query_hits)} queries")
    print(f"Total unique subjects to extract: {len(all_subjects_ordered)}")
    print(f"Deduplicated from: {sum(len(subjects) for subjects in query_hits.values())} total hits")

    if queries_with_few_hits:
        print(f"\nWarning: {len(queries_with_few_hits)} queries have fewer than {args.min_hits} hits:")
        for query_info in queries_with_few_hits[:5]:
            print(f"  {query_info}")
        if len(queries_with_few_hits) > 5:
            print(f"  ... and {len(queries_with_few_hits) - 5} more")

if __name__ == "__main__":
    main()