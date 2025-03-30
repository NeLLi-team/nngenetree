#!/usr/bin/env python
import sys
import os
import argparse
from Bio import SeqIO
from ete3 import Tree
import csv # Import the csv module

def parse_fasta_headers(fasta_file):
    """
    Extract sequence IDs from a FASTA file.
    
    Parameters:
    -----------
    fasta_file : str
        Path to the FASTA file
    
    Returns:
    --------
    list
        List of sequence IDs
    """
    try:
        ids = []
        for record in SeqIO.parse(fasta_file, "fasta"):
            ids.append(record.id)
        return ids
    except Exception as e:
        sys.stderr.write(f"Error parsing FASTA file {fasta_file}: {str(e)}\n")
        return []

def read_subject_ids(subjects_file):
    """
    Read subject IDs from a file.
    
    Parameters:
    -----------
    subjects_file : str
        Path to the file containing subject IDs
    
    Returns:
    --------
    set
        Set of subject IDs
    """
    try:
        with open(subjects_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        sys.stderr.write(f"Error reading subjects file {subjects_file}: {str(e)}\n")
        return set()

def extract_closest_neighbors(tree_file, query_file, subjects_file, output_file, gene_name, num_neighbors=10, query_filter=None):
    """
    Extract the N closest neighbors to each query sequence from a phylogenetic tree.
    
    Parameters:
    -----------
    tree_file : str
        Path to the tree file in Newick format
    query_file : str
        Path to the query FASTA file
    subjects_file : str
        Path to the file containing all subject IDs
    output_file : str
        Path to the output file where closest neighbor IDs will be written
    gene_name : str
        Basename of the query file (used as gene identifier)
    num_neighbors : int
        Number of closest neighbors to extract per query
    query_filter : str
        Comma-separated list of query prefixes to filter by
    """
    try:
        # Check if tree file exists and is not empty
        if not os.path.exists(tree_file) or os.path.getsize(tree_file) == 0:
            sys.stderr.write(f"Warning: Tree file {tree_file} does not exist or is empty\n")
            with open(output_file, 'w') as f:
                f.write("# No valid tree found\n")
            return
            
        # Check if tree file contains "no hits" message
        with open(tree_file, 'r') as f:
            tree_content = f.read().strip()
            if "no hits" in tree_content.lower():
                sys.stderr.write(f"Warning: Tree file {tree_file} indicates no hits\n")
                with open(output_file, 'w') as f:
                    f.write("# Tree indicates no hits\n")
                return
        
        # Load the tree
        tree = Tree(tree_file)
        
        # Get query IDs
        query_ids = parse_fasta_headers(query_file)
        if not query_ids:
            sys.stderr.write(f"Error: No query IDs found in {query_file}\n")
            with open(output_file, 'w') as f:
                f.write("# No query IDs found\n")
            return
        
        # Get subject IDs
        subject_ids = read_subject_ids(subjects_file)
        if not subject_ids:
            sys.stderr.write(f"Error: No subject IDs found in {subjects_file}\n")
            with open(output_file, 'w') as f:
                f.write("# No subject IDs found\n")
            return
        
        # Parse query filter if provided
        query_prefixes = set()
        if query_filter:
            query_prefixes = set(prefix.strip() for prefix in query_filter.split(','))
            sys.stderr.write(f"Filtering queries by prefixes: {','.join(query_prefixes)}\n")
        
        # Find all leaf nodes in the tree
        all_leaves = {leaf.name for leaf in tree.get_leaves()}
        
        # Check if query IDs exist in the tree
        query_nodes = {}
        for query_id in query_ids:
            # Get the first field of the query ID (before the first "|")
            query_prefix = query_id.split('|')[0] if '|' in query_id else query_id
            
            # Skip if query filter is set and this query doesn't match any prefix
            if query_prefixes and not any(query_prefix.startswith(prefix) for prefix in query_prefixes):
                continue
                
            # Try different variations of the query ID that might be in the tree
            variations = [
                query_id,
                query_id.split()[0],
                query_id.split('|')[0] if '|' in query_id else query_id
            ]
            
            for var in variations:
                if var in all_leaves:
                    query_nodes[query_id] = var
                    break
            
            if query_id not in query_nodes:
                sys.stderr.write(f"Warning: Query ID {query_id} not found in tree\n")
        
        # Extract closest neighbors for each query
        closest_neighbors = set()
        output_rows = []  # Store output rows for CSV writing
        
        for query_id, tree_id in query_nodes.items():
            query_node = tree.search_nodes(name=tree_id)[0]
            
            # Get the first field of the query ID (before the first "|")
            query_prefix = query_id.split('|')[0] if '|' in query_id else query_id
            
            # Get distances to all other leaves
            distances = []
            for leaf in tree.get_leaves():
                if leaf.name != tree_id:
                    # Get the first field of the neighbor ID
                    neighbor_prefix = leaf.name.split('|')[0] if '|' in leaf.name else leaf.name
                    
                    # Skip if prefixes match
                    if neighbor_prefix == query_prefix:
                        continue
                        
                    distance = tree.get_distance(query_node, leaf)
                    distances.append((distance, leaf.name))
            
            # Sort by distance and take the N closest
            distances.sort()
            
            # Get the first distance as reference
            if distances:
                first_distance = distances[0][0]
                valid_distances = []
                
                # Only include distances that are not more than double the first distance
                for dist, name in distances:
                    if dist <= first_distance * 2:
                        valid_distances.append((dist, name))
                    else:
                        break
                
                # Limit to num_neighbors
                valid_distances = valid_distances[:num_neighbors]
                
                # Write results to both stderr and store for output file
                for i, (dist, name) in enumerate(valid_distances):
                    # Standard output to stderr for logging
                    log_line = f"{query_id}, Neighbor {i+1}: {name}, Distance: {dist:.6f}"
                    sys.stderr.write(log_line + "\n")
                    
                    # Prepare CSV row
                    output_rows.append([query_id, name, gene_name, f"{dist:.6f}"])
                    closest_neighbors.add(name)
        
        # Write results to output file as CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['query', 'subject', 'gene', 'distance'])
            # Write data rows
            writer.writerows(output_rows)
        
        sys.stderr.write(f"Extracted {len(closest_neighbors)} unique closest neighbors for {len(query_nodes)} queries. Wrote {len(output_rows)} rows to {output_file}\n")
    
    except Exception as e:
        sys.stderr.write(f"Error extracting closest neighbors: {str(e)}\n")
        # Write error to output file as comment if it happens before header write
        with open(output_file, 'w') as f:
            f.write(f"# Error: {str(e)}\n")

def main():
    parser = argparse.ArgumentParser(description='Extract closest neighbors from a phylogenetic tree')
    parser.add_argument('--tree', required=True, help='Path to the tree file in Newick format')
    parser.add_argument('--query', required=True, help='Path to the query FASTA file')
    parser.add_argument('--subjects', required=True, help='Path to the file containing all subject IDs')
    parser.add_argument('--output', required=True, help='Path to the output file')
    parser.add_argument('--num_neighbors', type=int, default=10, help='Number of closest neighbors to extract per query')
    parser.add_argument('--query_filter', help='Comma-separated list of query prefixes to filter by')
    
    args = parser.parse_args()
    
    # Extract gene name from query file path
    try:
        gene_name = os.path.splitext(os.path.basename(args.query))[0]
    except Exception as e:
        sys.stderr.write(f"Error extracting gene name from query file path '{args.query}': {str(e)}\n")
        gene_name = "unknown_gene" # Fallback gene name
        
    sys.stderr.write(f"Using gene name: {gene_name}\n")

    extract_closest_neighbors(
        args.tree,
        args.query,
        args.subjects,
        args.output,
        gene_name, # Pass gene name
        args.num_neighbors,
        args.query_filter
    )

if __name__ == "__main__":
    main()