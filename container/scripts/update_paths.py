#!/usr/bin/env python3

import sys
import os
import re

def update_snakefile_paths(snakefile_path):
    """Update paths in Snakefile to be compatible with container paths."""
    with open(snakefile_path, 'r') as f:
        content = f.read()
    
    # Update paths to use /data/input and /data/output
    modified_content = content.replace(
        'INPUT_DIR = config.get("input_dir", "example")',
        'INPUT_DIR = config.get("input_dir", "/data/input")'
    )
    
    # Update the output directory to be relative to the input directory
    modified_content = modified_content.replace(
        'OUTPUT_BASE_DIR = INPUT_DIR + "_nngenetree"',
        'OUTPUT_BASE_DIR = "/data/output"'
    )
    
    # Write the modified content back to the file
    with open(snakefile_path, 'w') as f:
        f.write(modified_content)
        
    print(f"Updated paths in {snakefile_path}")
    print("- Changed input directory to /data/input")
    print("- Changed output directory to /data/output")

if __name__ == '__main__':
    snakefile_path = 'workflow/Snakefile'
    if not os.path.exists(snakefile_path):
        print(f"Error: {snakefile_path} not found!")
        sys.exit(1)
    update_snakefile_paths(snakefile_path)
    print("✅ Path updates completed successfully") 