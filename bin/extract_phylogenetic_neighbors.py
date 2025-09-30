#!/usr/bin/env python3
"""
Extract top N neighbors for each query sequence from phylogenetic trees,
excluding self-hits (very low distance) and including taxonomy information.
"""
import sys
import json
import csv
from pathlib import Path
from ete3 import Tree
import argparse

def get_taxonomy_from_accession(accession):
    """Infer basic taxonomy from accession pattern."""
    if accession.startswith('AYV'):
        return "Viruses; Nucleocytoviricota; Hyperionvirus"
    elif accession.startswith('WP_'):
        return "Bacteria"
    elif accession.startswith('XP_'):
        return "Eukaryota"
    elif accession.startswith('NP_'):
        return "Bacteria; RefSeq"
    elif accession.startswith('YP_'):
        return "Bacteria; RefSeq"
    elif accession.startswith('AEF') or accession.startswith('ARF'):
        return "Bacteria; Pseudomonadota; Gammaproteobacteria"
    elif accession.startswith('KA'):
        return "Eukaryota"
    elif accession.startswith('CA'):
        return "Bacteria"
    elif accession.startswith('MD'):
        return "Bacteria"
    elif accession.startswith('PBC'):
        return "Bacteria"
    elif accession.startswith('MBE') or accession.startswith('MCL'):
        return "Unknown"
    else:
        return "Unknown"

def extract_neighbors(tree_file, query_prefixes, output_json, output_csv,
                      num_neighbors=5, self_hit_threshold=0.001):
    """
    Extract top N neighbors for each query sequence in the tree.

    Parameters:
    -----------
    tree_file : str
        Path to the tree file
    query_prefixes : list
        List of query prefixes to search for (e.g., ['Hype', 'Klos'])
    output_json : str
        Path to output JSON file with detailed neighbor information
    output_csv : str
        Path to output CSV file for pipeline compatibility
    num_neighbors : int
        Number of neighbors to extract per query
    self_hit_threshold : float
        Distance threshold below which hits are considered self-hits
    """
    try:
        # Load tree
        tree = Tree(str(tree_file))

        # Find all query sequences
        query_nodes = []
        for leaf in tree.get_leaves():
            for prefix in query_prefixes:
                if leaf.name.startswith(prefix):
                    query_nodes.append(leaf)
                    break

        print(f"Found {len(query_nodes)} query sequences in tree")

        results = {
            "tree_file": str(tree_file),
            "query_count": len(query_nodes),
            "placements": []
        }

        csv_rows = []

        # For each query sequence, find neighbors
        for query_node in query_nodes:
            # Get all other leaves with distances
            distances = []
            for other_leaf in tree.get_leaves():
                if other_leaf.name != query_node.name:
                    try:
                        dist = query_node.get_distance(other_leaf)
                        distances.append((other_leaf.name, dist))
                    except:
                        continue

            # Sort by distance
            distances.sort(key=lambda x: x[1])

            # Get query prefix for filtering
            query_prefix = query_node.name.split('|')[0] if '|' in query_node.name else query_node.name

            # Filter out self-hits and get top N
            neighbors = []
            for neighbor_name, dist in distances:
                # Get neighbor prefix
                neighbor_prefix = neighbor_name.split('|')[0] if '|' in neighbor_name else neighbor_name

                # Skip if it's another sequence from same genome (same prefix)
                if neighbor_prefix == query_prefix:
                    continue

                # Skip other query genomes
                if any(neighbor_prefix == p for p in query_prefixes):
                    continue

                # For sequences with same accession pattern, only skip if distance is very small
                if neighbor_name.startswith(neighbor_prefix) and dist < self_hit_threshold:
                    continue

                taxonomy = get_taxonomy_from_accession(neighbor_name)

                neighbors.append({
                    "id": neighbor_name,
                    "distance": dist,
                    "taxonomy": taxonomy
                })

                # Add to CSV output
                csv_rows.append([
                    query_node.name,
                    neighbor_name,
                    f"{dist:.6f}",
                    taxonomy.split(";")[0].strip()  # Domain level for CSV
                ])

                if len(neighbors) >= num_neighbors:
                    break

            results["placements"].append({
                "query": query_node.name,
                "closest_neighbors": neighbors
            })

        # Calculate taxonomy summary
        all_taxonomies = []
        for placement in results["placements"]:
            for neighbor in placement["closest_neighbors"]:
                tax = neighbor["taxonomy"].split(";")[0].strip()
                all_taxonomies.append(tax)

        # Count domains
        domain_counts = {}
        for tax in all_taxonomies:
            domain_counts[tax] = domain_counts.get(tax, 0) + 1

        results["taxonomy_summary"] = {
            "domains": domain_counts,
            "total_neighbors": len(all_taxonomies)
        }

        # Write JSON results
        with open(output_json, 'w') as f:
            json.dump(results, f, indent=2)

        # Write CSV results for pipeline compatibility
        with open(output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(["query_id", "neighbor_id", "distance", "domain"])
            # Write data
            writer.writerows(csv_rows)

        return True

    except Exception as e:
        print(f"Error processing {tree_file}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract phylogenetic neighbors for query sequences')
    parser.add_argument('--tree', required=True, help='Path to tree file')
    parser.add_argument('--query-prefixes', default='Hype,Klos',
                        help='Comma-separated list of query prefixes')
    parser.add_argument('--output-json', required=True, help='Output JSON file path')
    parser.add_argument('--output-csv', required=True, help='Output CSV file path')
    parser.add_argument('--num-neighbors', type=int, default=5,
                        help='Number of neighbors to extract per query')
    parser.add_argument('--self-hit-threshold', type=float, default=0.001,
                        help='Distance threshold for self-hits')

    args = parser.parse_args()

    query_prefixes = [p.strip() for p in args.query_prefixes.split(',')]

    success = extract_neighbors(
        args.tree,
        query_prefixes,
        args.output_json,
        args.output_csv,
        args.num_neighbors,
        args.self_hit_threshold
    )

    if success:
        print(f"✓ Results saved to {args.output_json} and {args.output_csv}")

        # Show summary
        with open(args.output_json) as f:
            data = json.load(f)
        print(f"\nSummary:")
        print(f"  Query sequences analyzed: {data['query_count']}")
        if data['taxonomy_summary']['domains']:
            print("  Neighbor taxonomy distribution:")
            for domain, count in data['taxonomy_summary']['domains'].items():
                print(f"    - {domain}: {count}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()