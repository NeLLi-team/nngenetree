#!/usr/bin/env python3

import os
import argparse
from Bio import SeqIO
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_orthogroup(group, seq_ids, seq_records_dict, extracted_dir, multi_faa_file):
    """
    Extract matching sequences for a single orthogroup into a .faa file.
    Returns a list of created file paths (only the .faa here).
    """
    files_created = []
    out_faa = os.path.join(extracted_dir, f"{group}.faa")
    out_records = []

    for sid in seq_ids:
        if sid in seq_records_dict:
            out_records.append(seq_records_dict[sid])
        else:
            print(f"Warning: sequence ID '{sid}' not found in {multi_faa_file}.")

    if out_records:
        # Write the extracted sequences to a FASTA file
        SeqIO.write(out_records, out_faa, "fasta")
        files_created.append(out_faa)
        print(f"[{group}] Created {out_faa}")

    return files_created

def main():
    parser = argparse.ArgumentParser(
        description="Extract proteins from orthogroups into individual .faa files."
    )
    parser.add_argument("ortho_file", help="Path to the orthogroup file.")
    parser.add_argument("multi_faa_file", help="Path to the multi-FASTA file.")
    parser.add_argument("-t", "--threads", type=int, default=8,
                        help="Number of threads for parallel processing (default=8).")
    parser.add_argument("-m", "--min-proteins", type=int, default=4,
                        help="Minimum number of proteins to process the orthogroup (default=4).")

    args = parser.parse_args()

    ortho_file = args.ortho_file
    multi_faa_file = args.multi_faa_file
    threads = args.threads
    min_proteins = args.min_proteins

    # Output directory to store extracted .faa files
    extracted_dir = "extracted_og_faa"
    os.makedirs(extracted_dir, exist_ok=True)

    # -------------------------
    # Parse the orthogroup file
    # -------------------------
    ortho_dict = {}
    with open(ortho_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            group_name, rest = line.split(":", 1)
            group_name = group_name.strip()
            seq_ids = rest.strip().split()
            ortho_dict[group_name] = seq_ids

    # ---------------------------------
    # Read all sequences into a dictionary
    # ---------------------------------
    seq_records_dict = {}
    for record in SeqIO.parse(multi_faa_file, "fasta"):
        seq_records_dict[record.id] = record

    # -------------------------------------------------
    # Process each orthogroup in parallel using threads
    # -------------------------------------------------
    final_files_created = []

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_group = {}
        for group, seq_ids in ortho_dict.items():
            # Skip orthogroups with fewer than min_proteins entries
            if len(seq_ids) < min_proteins:
                print(f"[{group}] Has only {len(seq_ids)} proteins (< {min_proteins}). Skipping.")
                continue

            future = executor.submit(
                process_orthogroup,
                group, seq_ids, seq_records_dict,
                extracted_dir,
                multi_faa_file
            )
            future_to_group[future] = group

        # Collect results
        for future in as_completed(future_to_group):
            group = future_to_group[future]
            try:
                created = future.result()
                final_files_created.extend(created)
            except Exception as e:
                print(f"[{group}] Error: {e}")

    # -----------------------------------
    # Summarize all files created
    # -----------------------------------
    print("\nAll jobs completed. Files created:")
    for fc in final_files_created:
        print(fc)

if __name__ == "__main__":
    main()
