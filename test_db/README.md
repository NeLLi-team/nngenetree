# Test Database

This directory contains a small DIAMOND database for rapid pipeline testing.

## Contents

- **test_reference.faa**: Combined sequences from example/test1.faa and example/test2.faa (10 sequences, 4866 letters)
- **test_reference.dmnd**: DIAMOND database created from test_reference.faa

## Usage

### Quick Test Run

Run the pipeline with the test database for rapid validation:

```bash
# Local test run (completes in minutes instead of hours)
pixi run snakemake --configfile workflow/config_test.txt --cores 4

# Or with custom output directory
pixi run snakemake --configfile workflow/config_test.txt --config output_dir=test_output --cores 4
```

### Creating the Test Database

If you need to recreate the test database:

```bash
# Combine example sequences
cat example/test1.faa example/test2.faa > test_db/test_reference.faa

# Create DIAMOND database
pixi run diamond makedb --in test_db/test_reference.faa --db test_db/test_reference
```

## Test Database Specifications

- **Sequences**: 10 proteins
- **Total length**: 4,866 amino acids
- **Database hash**: c97c5bb9f156fee3bf85d763e81d2033
- **Build time**: ~0.1 seconds

## Benefits

1. **Speed**: BLAST search completes in seconds vs hours with nr database
2. **Predictability**: Small, fixed database for reproducible testing
3. **Development**: Ideal for testing pipeline modifications
4. **CI/CD**: Can be used for automated testing

## Comparison

| Database | Sequences | Size | BLAST Time (approx) |
|----------|-----------|------|---------------------|
| test_reference | 10 | 5 KB | < 1 second |
| nr (default) | 798M | 306 GB | 1-2 hours |

Use this test database for development and validation before running against the full nr database.