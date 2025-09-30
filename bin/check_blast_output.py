#!/usr/bin/env python3
import sys

def count_lines(blast_file):
    count = 0
    with open(blast_file) as f:
        for line in f:
            count += 1
    return count

if __name__ == "__main__":
    blast_file = sys.argv[1]
    num_lines = count_lines(blast_file)
    print(f"Number of lines in {blast_file}: {num_lines}")
    if num_lines < 2:
        print("Warning: Not enough lines in BLAST output")
        sys.exit(1)
    sys.exit(0)
