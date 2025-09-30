#!/usr/bin/env python3
"""
Generate workflow diagram for NNGeneTree pipeline.

This script generates a visual representation of the NNGeneTree workflow
using Snakemake's built-in DAG visualization capabilities. It creates
both SVG and PNG versions of the workflow diagram.

Usage:
    python generate_workflow_diagram.py [output_prefix]

Arguments:
    output_prefix: Optional prefix for output files (default: 'workflow_diagram')
"""

import os
import sys
import subprocess
import tempfile


def generate_dag(output_prefix='workflow_diagram'):
    """
    Generate workflow DAG visualization.
    
    Parameters
    ----------
    output_prefix : str
        Prefix for output files
        
    Returns
    -------
    bool
        True if successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs('docs', exist_ok=True)
        
        # Generate DAG in dot format
        with tempfile.NamedTemporaryFile(suffix='.dot', mode='w+', delete=False) as tmp:
            dot_file = tmp.name
        
        print(f"Generating DAG representation to {dot_file}...")
        cmd = f"snakemake --dag | dot -Tpng > docs/{output_prefix}.png"
        subprocess.run(cmd, shell=True, check=True)
        
        # Generate SVG version for web
        cmd = f"snakemake --dag | dot -Tsvg > docs/{output_prefix}.svg"
        subprocess.run(cmd, shell=True, check=True)
        
        print(f"Workflow diagram generated successfully:")
        print(f"  - PNG: docs/{output_prefix}.png")
        print(f"  - SVG: docs/{output_prefix}.svg")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error generating workflow diagram: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False


def main():
    """Main function to generate the workflow diagram."""
    # Get output prefix from command line, if provided
    output_prefix = 'workflow_diagram'
    if len(sys.argv) > 1:
        output_prefix = sys.argv[1]
    
    # Generate the workflow diagram
    success = generate_dag(output_prefix)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 