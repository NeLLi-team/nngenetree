# Test database

This directory contains a small DIAMOND database for pipeline tests.

## Contents

- **test_reference.faa**: Reference proteins, including the sequences of test/test1.faa and test/test2.faa (131 sequences, 53,966 letters)
- **test_reference.dmnd**: DIAMOND database created from test_reference.faa; tracked in git so that a fresh clone can run the test

## Usage

### Quick test run

Run the pipeline with the test database:

```bash
# From the repository root; the run takes about two minutes
nngenetree test
```

### Creating the test database

If you need to recreate the test database:

```bash
# Combine example sequences
cat test/test1.faa test/test2.faa > test/db/test_reference.faa

# Create DIAMOND database
pixi run diamond makedb --in test/db/test_reference.faa --db test/db/test_reference
```

## Test database specifications

- **Sequences**: 131 proteins
- **Total length**: 53,966 amino acids
- **Build time**: ~0.1 seconds

## Purpose

The test database keeps a full pipeline run under two minutes, uses a fixed set of inputs, and works in automated tests.

## Comparison

| Database | Sequences | Size | BLAST Time (approx) |
|----------|-----------|------|---------------------|
| test_reference | 131 | 71 KB | < 1 second |
| nr (default) | 798M | 306 GB | 1-2 hours |

Use the test database during development, then run against the full nr database.