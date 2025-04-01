#!/bin/bash

# Build script for NNGeneTree Singularity container

# Make scripts executable
chmod +x run_container.sh update_paths.py

# First update paths in the Snakefile
echo "Updating paths in Snakefile for container compatibility..."
./workflow/scripts/update_paths.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to update paths in Snakefile"
    exit 1
fi

# Build the container
echo "Building NNGeneTree Singularity container..."
singularity build --fakeroot nngenetree.sif Singularity.def

if [ $? -eq 0 ]; then
    echo "✅ Container built successfully: nngenetree.sif"
else
    echo "❌ Container build failed."
    exit 1
fi

echo
echo "To use the container, run:"
echo "./run_container.sh -i /path/to/input/directory -b /path/to/blast/db"
echo
echo "For more options:"
echo "./run_container.sh -h" 