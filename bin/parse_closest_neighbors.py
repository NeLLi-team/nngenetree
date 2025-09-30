#!/usr/bin/env python3
"""
Parse closest neighbors from gene tree analysis results and add NCBI taxonomy information.

This script processes directories containing closest neighbors CSV files
and appends NCBI taxonomy information to the existing CSV files.

For each tree_neighbors.csv file, it adds a new column 'taxonomy' with the NCBI
taxonomy information for the subject IDs.
"""

import os
import sys
import argparse
import csv
from pathlib import Path
from typing import Iterator, Tuple, Dict, List, Optional, Set
from Bio import Entrez
from tqdm import tqdm
import time
import tempfile
import shutil
import re

# Set your email for NCBI Entrez
Entrez.email = 'fschulz@lbl.gov'

def fetch_taxonomy(accession: str) -> str:
    """
    Fetch taxonomy information for a given accession number.
    
    Parameters
    ----------
    accession : str
        NCBI protein accession number
        
    Returns
    -------
    str
        Taxonomy string or error message
    """
    try:
        # Remove version number if present
        accession = accession.split('.')[0]
        handle = Entrez.efetch(db='protein', id=accession, rettype='gb', retmode='xml')
        record = Entrez.read(handle)
        taxonomy = record[0]['GBSeq_taxonomy']
        handle.close()
        time.sleep(0.34)  # Rate limit to comply with NCBI's guidelines (3 requests per second)
        
        # Clean up taxonomy string for easier parsing
        # Replace spaces with underscores in the taxonomy string
        taxonomy = taxonomy.replace('; ', ';')
        taxonomy = taxonomy.replace(' ', '_')
        
        return taxonomy
    except Exception as e:
        return f"Unknown ({str(e)})"  # If taxonomy lookup fails, return Unknown with error message

def process_csv_file(file_path: Path) -> List[Dict[str, str]]:
    """
    Process a CSV file and return all rows with subject IDs.
    
    Parameters
    ----------
    file_path : Path
        Path to the CSV file
        
    Returns
    -------
    List[Dict[str, str]]
        List of rows from the CSV file
    """
    try:
        # Check if file is empty
        if os.path.getsize(file_path) == 0:
            print(f"File is empty: {file_path}", file=sys.stderr)
            return []
            
        # Handle CSV format with custom parser
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Check if file starts with '#' (error comment)
            if content.startswith('#'):
                print(f"Error indicator (#) found in file: {file_path}", file=sys.stderr)
                return []
                
            # Split content into lines and process manually
            lines = content.strip().split('\n')
            if not lines:
                print(f"No data rows found in file: {file_path}", file=sys.stderr)
                return []
                
            # Parse header line
            header = lines[0].split(',')
            if 'query' not in header[0] or 'subject' not in header[1]:
                print(f"Unexpected CSV format in file: {file_path}, header: {header}", file=sys.stderr)
                return []
                
            # Parse data rows
            rows = []
            for i in range(1, len(lines)):
                line = lines[i]
                # Split by comma, handling special case where taxonomy might contain commas
                if ',' in line:
                    # Try to find patterns of fields
                    match = re.match(r'([^,]+),([^,]+),([^,]+),([\d\.]+)(,.+)?', line)
                    if match:
                        query = match.group(1).strip()
                        subject = match.group(2).strip()
                        gene = match.group(3).strip()
                        distance = match.group(4).strip()
                        
                        row = {
                            'query': query,
                            'subject': subject,
                            'gene': gene,
                            'distance': distance
                        }
                        
                        # Check if taxonomy field exists
                        if match.group(5) and match.group(5).startswith(','):
                            # Extract taxonomy info - it's the last field which might contain commas
                            taxonomy_match = re.search(r',([^,]+;.*)$', line)
                            if taxonomy_match:
                                row['taxonomy'] = taxonomy_match.group(1).strip()
                            else:
                                row['taxonomy'] = ''
                        else:
                            row['taxonomy'] = ''
                        
                        rows.append(row)
                    else:
                        print(f"Could not parse line: {line}", file=sys.stderr)
            
            return rows
                
    except Exception as e:
        print(f"Error processing CSV file {file_path}: {e}", file=sys.stderr)
        print(f"Stack trace: {import_module('traceback').format_exc()}", file=sys.stderr)
        return []

def process_old_format_file(file_path: Path) -> List[Dict[str, str]]:
    """
    Process an old format text file and convert to the new CSV format.
    
    Parameters
    ----------
    file_path : Path
        Path to the text file
        
    Returns
    -------
    List[Dict[str, str]]
        List of rows with subject IDs in the new format
    """
    try:
        # Check if file is empty
        if os.path.getsize(file_path) == 0:
            print(f"File is empty: {file_path}", file=sys.stderr)
            return []
            
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Check for error message
            if 'Error' in content or 'no hits' in content.lower():
                print(f"Error or 'no hits' found in file: {file_path}", file=sys.stderr)
                return []
                
            # Get all non-empty lines
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if not lines:
                print(f"No valid content in file: {file_path}", file=sys.stderr)
                return []
                
            # Create a list of fake rows for each ID
            rows = []
            for subject_id in lines:
                rows.append({
                    'query': 'unknown',
                    'subject': subject_id,
                    'gene': Path(file_path).parent.name,
                    'distance': '0.0',
                    'taxonomy': ''
                })
            return rows
                
    except Exception as e:
        print(f"Error processing text file {file_path}: {e}", file=sys.stderr)
        return []

def find_and_process_files(base_dir: str = '.') -> Iterator[Tuple[Path, List[Dict[str, str]]]]:
    """
    Find all closest neighbors CSV files and process them.
    
    Parameters
    ----------
    base_dir : str
        Base directory to start the search from
        
    Yields
    ------
    Tuple[Path, List[Dict[str, str]]]
        Pairs of (file_path, rows) for each CSV file found
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Error: Directory '{base_dir}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not base_path.is_dir():
        print(f"Error: '{base_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Count processed files
    processed_count = 0
    
    # Process a single directory
    csv_path = base_path.joinpath('closest_neighbors.csv')
    if csv_path.exists():
        print(f"Found CSV file: {csv_path}", file=sys.stderr)
        rows = process_csv_file(csv_path)
        if rows:
            yield csv_path, rows
            processed_count += 1

    # If no processing occurred, report it
    if processed_count == 0:
        print(f"Warning: No closest_neighbors.csv files were found in {base_dir}", file=sys.stderr)
    else:
        print(f"Processed {processed_count} CSV files", file=sys.stderr)

def get_unique_accessions(all_rows: List[Dict[str, str]]) -> Set[str]:
    """
    Extract all unique subject IDs from the rows.
    
    Parameters
    ----------
    all_rows : List[Dict[str, str]]
        List of rows with subject IDs
        
    Returns
    -------
    Set[str]
        Set of unique subject IDs
    """
    accessions = set()
    for row in all_rows:
        if 'subject' in row and row['subject']:
            accessions.add(row['subject'])
    
    print(f"Found {len(accessions)} unique subject IDs", file=sys.stderr)
    return accessions

def append_taxonomy_to_csv(file_path: Path, taxonomy_dict: Dict[str, str]) -> None:
    """
    Append taxonomy information to the CSV file.
    
    Parameters
    ----------
    file_path : Path
        Path to the CSV file
    taxonomy_dict : Dict[str, str]
        Dictionary mapping subject IDs to taxonomy strings
    """
    try:
        # Create a temporary file for the new CSV
        with tempfile.NamedTemporaryFile(mode='w', dir=str(file_path.parent), delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            # Read the original CSV file
            with open(file_path, 'r') as f:
                # Read all lines
                lines = f.read().strip().split('\n')
                
                # Process header
                header = lines[0]
                if not header.endswith(',taxonomy'):
                    header += ',taxonomy'
                temp_file.write(header + '\n')
                
                # Process each data row
                for i in range(1, len(lines)):
                    line = lines[i]
                    parts = re.split(r',(?=[^;]*(?:,|$))', line)
                    
                    if len(parts) >= 2:
                        subject = parts[1].strip()
                        taxonomy = taxonomy_dict.get(subject, 'Unknown')
                        
                        # Check if there's already a taxonomy field at the end
                        if len(parts) > 4 and ';' in parts[-1]:
                            # Replace existing taxonomy
                            parts[-1] = taxonomy
                        else:
                            # Append taxonomy
                            parts.append(taxonomy)
                        
                        # Write the updated line with taxonomy
                        temp_file.write(','.join(parts) + '\n')
                    else:
                        # Write malformed lines as is
                        temp_file.write(line + '\n')
                        print(f"Warning: Malformed line: {line}", file=sys.stderr)
                
        # Replace the original file with the temporary file
        shutil.move(temp_path, file_path.with_name('closest_neighbors_with_taxonomy.csv'))
        print(f"Updated CSV file saved as {file_path.with_name('closest_neighbors_with_taxonomy.csv')}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error appending taxonomy to CSV file {file_path}: {e}", file=sys.stderr)
        # If there was an error, try to remove the temporary file
        try:
            if temp_path.exists():
                temp_path.unlink()
        except:
            pass

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-d', '--dir', default='.', help='Base directory to search for closest_neighbors.csv files')
    parser.add_argument('-o', '--output', help='Output file for taxonomy assignments in TSV format')
    parser.add_argument('-f', '--force', action='store_true', help='Force overwriting existing taxonomy information')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print verbose information')
    
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Find and process CSV files
    taxonomy_assignments = {}
    all_rows = []
    
    print(f"Searching for closest_neighbors.csv files in {args.dir}", file=sys.stderr)
    
    for file_path, rows in find_and_process_files(args.dir):
        print(f"Processing {file_path}", file=sys.stderr)
        all_rows.extend(rows)
    
    # Get unique accessions
    unique_accessions = get_unique_accessions(all_rows)
    
    # Fetch taxonomy for each accession
    print(f"Fetching taxonomy information for {len(unique_accessions)} accessions", file=sys.stderr)
    for accession in tqdm(unique_accessions, desc="Fetching taxonomy"):
        taxonomy = fetch_taxonomy(accession)
        taxonomy_assignments[accession] = taxonomy
    
    # Write taxonomy assignments to a file
    if args.output:
        with open(args.output, 'w') as f:
            f.write("OG\tAccession\tTaxonomy\n")
            for accession, taxonomy in taxonomy_assignments.items():
                # Extract OG name from file path
                og_name = Path(args.dir).name
                f.write(f"{og_name}\t{accession}\t{taxonomy}\n")
        print(f"Wrote taxonomy assignments to {args.output}", file=sys.stderr)
    
    # Update CSV files with taxonomy
    print("Appending taxonomy information to CSV files", file=sys.stderr)
    for file_path, rows in find_and_process_files(args.dir):
        append_taxonomy_to_csv(file_path, taxonomy_assignments)
    
    print("All processing completed successfully", file=sys.stderr)
    
if __name__ == "__main__":
    main()