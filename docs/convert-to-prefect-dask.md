# NNGeneTree: Nextflow to Prefect-Dask Conversion Plan

## Overview

Convert the 14-step NNGeneTree phylogenetic pipeline from Nextflow DSL2 to Prefect 3.x with Dask task runners, supporting both local execution and SLURM cluster deployment.

## Current Architecture Summary

### Nextflow Pipeline (14 steps)
```
INPUT (.faa files)
  → DIAMOND_BLASTP (8 CPU, 64GB, 24h)
  → PROCESS_BLAST_RESULTS
  → CHECK_BLAST_OUTPUT
  → EXTRACT_HITS (1 CPU, 16GB, 4h)
  → COMBINE_SEQUENCES
  → ALIGN_SEQUENCES (8 CPU, 32GB, 24h)
  → TRIM_ALIGNMENT
  → BUILD_TREE (8 CPU, 32GB, 24h)
  → EXTRACT_CLOSEST_NEIGHBORS
  → ASSIGN_TAXONOMY (rate-limited NCBI API)
  → DECORATE_TREE
  → CALCULATE_TREE_STATS
  → EXTRACT_PHYLOGENETIC_PLACEMENT
  → COMBINE_PLACEMENT_RESULTS
OUTPUT (combined_placement_results.json)
```

### Key Files to Modify/Create
- `pixi.toml` - Add Prefect + Dask dependencies
- `src/nngenetree/` - New Python package structure
- `src/nngenetree/flows/` - Prefect flows
- `src/nngenetree/tasks/` - Prefect tasks
- `src/nngenetree/config.py` - Configuration management
- `src/nngenetree/cli.py` - Command-line interface
- `docs/convert-to-prefect-dask.md` - Migration documentation

---

## Phase 1: Environment Setup

### 1.1 Update pixi.toml

```toml
[project]
name = "nngenetree"
version = "2.0.0"
description = "Phylogenetic analysis pipeline with Prefect-Dask"
channels = ["conda-forge", "bioconda"]
platforms = ["linux-64"]

[dependencies]
# Python
python = ">=3.11,<3.13"

# Workflow Engine (replacing Nextflow)
prefect = ">=3.1,<4"
prefect-dask = ">=0.3.6,<1"
dask = ">=2024.11,<2026"
distributed = ">=2024.11,<2026"
dask-jobqueue = ">=0.9,<1"

# Bioinformatics tools (unchanged)
diamond = ">=2.1.12,<3"
blast = ">=2.17.0,<3"
mafft = ">=7.5,<8"
trimal = ">=1.5.0,<2"
fasttree = ">=2.1.0,<3"
iqtree = "==3.0.1"

# Python scientific stack (unchanged)
biopython = ">=1.80,<2"
ete3 = ">=3.1.0,<4"
pandas = ">=2.0,<3"
numpy = ">=1.24,<2"
scipy = ">=1.10,<2"
matplotlib = ">=3.10,<4"
seaborn = ">=0.13,<0.14"
lxml = ">=5.0,<6"
tqdm = ">=4.65,<5"
requests = ">=2.28,<3"
click = ">=8.0,<9"
pydantic = ">=2.0,<3"
pydantic-settings = ">=2.0,<3"

# Runtime
entrez-direct = ">=16.2"

[feature.dev.dependencies]
pytest = ">=8.0,<9"
pytest-asyncio = ">=0.23,<1"
black = ">=24.0,<25"
ruff = ">=0.4,<1"
mypy = ">=1.10,<2"

[tasks]
# Local execution
run-local = "python -m nngenetree.cli run --mode local"
# SLURM execution
run-slurm = "python -m nngenetree.cli run --mode slurm"
# Test
test = "pytest tests/ -v"
# Lint
lint = "ruff check src/ && mypy src/"
format = "black src/ tests/"
```

### 1.2 Create Package Structure

```
nngenetree/
├── src/
│   └── nngenetree/
│       ├── __init__.py
│       ├── cli.py              # Click CLI
│       ├── config.py           # Pydantic settings
│       ├── flows/
│       │   ├── __init__.py
│       │   └── main.py         # Main Prefect flow
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── blast.py        # DIAMOND, extract hits
│       │   ├── alignment.py    # MAFFT, TrimAl
│       │   ├── phylogeny.py    # Tree building
│       │   ├── taxonomy.py     # NCBI lookup
│       │   └── analysis.py     # Neighbors, stats
│       └── utils/
│           ├── __init__.py
│           ├── io.py           # File I/O helpers
│           └── cluster.py      # Dask cluster factory
├── tests/
│   ├── test_tasks.py
│   └── test_flows.py
├── docs/
│   └── convert-to-prefect-dask.md
└── pixi.toml
```

---

## Phase 2: Configuration System

### 2.1 config.py - Pydantic Settings

```python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
from pathlib import Path

class ResourceConfig(BaseSettings):
    """Per-task resource configuration"""
    threads: int = 8
    memory_gb: int = 32
    time_hours: int = 24

class SLURMConfig(BaseSettings):
    """SLURM cluster configuration"""
    queue: str = "normal"
    account: str = ""
    partition: str = "compute"
    qos: str = ""
    cores_per_job: int = 24
    processes_per_job: int = 6  # workers per job
    memory_per_job: str = "64GB"
    walltime: str = "24:00:00"
    max_jobs: int = 50
    min_jobs: int = 2

class PipelineConfig(BaseSettings):
    """Main pipeline configuration"""
    # Execution mode
    mode: Literal["local", "slurm"] = "local"

    # Input/Output
    input_dir: Path
    output_dir: Path | None = None
    blast_db: Path

    # NCBI API
    entrez_email: str

    # Pipeline parameters
    blast_hits: int = 20
    closest_neighbors: int = 10
    query_prefixes: str = ""
    tree_builder: Literal["fasttree", "iqtree"] = "fasttree"

    # Resources
    blast_resources: ResourceConfig = ResourceConfig(threads=8, memory_gb=64, time_hours=24)
    align_resources: ResourceConfig = ResourceConfig(threads=8, memory_gb=32, time_hours=24)
    tree_resources: ResourceConfig = ResourceConfig(threads=8, memory_gb=32, time_hours=24)

    # SLURM settings
    slurm: SLURMConfig = SLURMConfig()

    # Caching
    cache_dir: Path = Path(".nngenetree_cache")
    enable_caching: bool = True

    class Config:
        env_prefix = "NNGENETREE_"
        env_file = ".env"
```

---

## Phase 3: Dask Cluster Factory

### 3.1 cluster.py - Local vs SLURM

```python
from contextlib import contextmanager
from dask.distributed import Client, LocalCluster
from dask_jobqueue import SLURMCluster
from ..config import PipelineConfig, SLURMConfig

@contextmanager
def get_dask_cluster(config: PipelineConfig):
    """Factory for Dask cluster based on execution mode"""

    if config.mode == "local":
        cluster = LocalCluster(
            n_workers=4,
            threads_per_worker=config.blast_resources.threads // 4,
            memory_limit=f"{config.blast_resources.memory_gb // 4}GB"
        )
    else:  # slurm
        slurm = config.slurm
        cluster = SLURMCluster(
            queue=slurm.queue,
            account=slurm.account,
            cores=slurm.cores_per_job,
            processes=slurm.processes_per_job,
            memory=slurm.memory_per_job,
            walltime=slurm.walltime,
            job_extra_directives=[
                f"--qos={slurm.qos}" if slurm.qos else "",
                f"--partition={slurm.partition}"
            ]
        )
        cluster.adapt(minimum_jobs=slurm.min_jobs, maximum_jobs=slurm.max_jobs)

    client = Client(cluster)
    try:
        yield cluster
    finally:
        client.close()
        cluster.close()
```

---

## Phase 4: Task Definitions

### 4.1 tasks/blast.py

```python
from prefect import task
from prefect.cache_policies import INPUTS
from datetime import timedelta
import subprocess
from pathlib import Path

@task(
    name="diamond_blastp",
    retries=3,
    retry_delay_seconds=[60, 300, 600],
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=7),
    tags=["cpu-intensive", "io-intensive"]
)
def diamond_blastp(
    query_fasta: Path,
    blast_db: Path,
    output_dir: Path,
    threads: int = 8,
    max_hits: int = 20
) -> Path:
    """Run DIAMOND BLASTP against NR database"""
    output_file = output_dir / "blast_results.m8"

    cmd = [
        "diamond", "blastp",
        "-d", str(blast_db) + ".dmnd",
        "-q", str(query_fasta),
        "-o", str(output_file),
        "-p", str(threads),
        "-k", str(max_hits),
        "--outfmt", "6"
    ]

    subprocess.run(cmd, check=True)
    return output_file


@task(
    name="process_blast_results",
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=7)
)
def process_blast_results(
    blast_file: Path,
    output_dir: Path,
    max_hits: int = 50,
    min_hits: int = 5
) -> Path:
    """Extract unique subject IDs from BLAST results"""
    # Reuse existing bin/process_blast_for_extraction.py logic
    ...


@task(
    name="extract_hits",
    retries=2,
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=7)
)
def extract_hits(
    subjects_file: Path,
    blast_db: Path,
    output_dir: Path
) -> Path:
    """Extract hit sequences from BLAST database"""
    output_file = output_dir / "extracted_hits.faa"

    cmd = [
        "blastdbcmd",
        "-db", str(blast_db),
        "-entry_batch", str(subjects_file),
        "-out", str(output_file)
    ]

    subprocess.run(cmd, check=True)
    return output_file
```

### 4.2 tasks/alignment.py

```python
@task(
    name="align_sequences",
    retries=2,
    retry_delay_seconds=300,
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=7),
    tags=["cpu-intensive"]
)
def align_sequences(
    combined_fasta: Path,
    output_dir: Path,
    threads: int = 8
) -> Path:
    """Run MAFFT multiple sequence alignment"""
    output_file = output_dir / "aln" / "aligned_sequences.msa"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = f"mafft --thread {threads} {combined_fasta} > {output_file}"
    subprocess.run(cmd, shell=True, check=True)

    return output_file


@task(
    name="trim_alignment",
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=7)
)
def trim_alignment(aligned_file: Path, output_dir: Path) -> Path:
    """Trim alignment with TrimAl"""
    output_file = output_dir / "aln" / "trimmed_alignment.msa"

    cmd = [
        "trimal",
        "-in", str(aligned_file),
        "-out", str(output_file),
        "-gt", "0.1"
    ]

    subprocess.run(cmd, check=True)
    return output_file
```

### 4.3 tasks/phylogeny.py

```python
@task(
    name="build_tree",
    retries=2,
    retry_delay_seconds=600,
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=7),
    tags=["cpu-intensive"]
)
def build_tree(
    trimmed_alignment: Path,
    output_dir: Path,
    builder: str = "fasttree",
    threads: int = 8
) -> Path:
    """Build phylogenetic tree with FastTree or IQ-TREE"""
    tree_dir = output_dir / "tree"
    tree_dir.mkdir(parents=True, exist_ok=True)
    tree_file = tree_dir / "final_tree.treefile"

    if builder == "fasttree":
        cmd = f"fasttree -lg < {trimmed_alignment} > {tree_file}"
        subprocess.run(cmd, shell=True, check=True)
    else:  # iqtree
        cmd = [
            "iqtree",
            "-s", str(trimmed_alignment),
            "-m", "LG+G4",
            "-T", str(threads),
            "--prefix", str(tree_dir / "final_tree")
        ]
        subprocess.run(cmd, check=True)

    return tree_file
```

### 4.4 tasks/taxonomy.py

```python
from prefect import task
from prefect.cache_policies import INPUTS
from Bio import Entrez
import time

@task(
    name="assign_taxonomy",
    retries=5,
    retry_delay_seconds=[10, 30, 60, 120, 300],
    cache_policy=INPUTS,
    cache_expiration=timedelta(days=30),  # Long cache for API results
    tags=["api-call", "rate-limited"]
)
def assign_taxonomy(
    neighbors_csv: Path,
    output_dir: Path,
    entrez_email: str
) -> tuple[Path, Path]:
    """Add NCBI taxonomy to neighbor results"""
    Entrez.email = entrez_email

    # Reuse existing bin/parse_closest_neighbors.py logic
    # with rate limiting (0.34 sec between calls)
    ...
```

---

## Phase 5: Main Flow Definition

### 5.1 flows/main.py

```python
from prefect import flow, get_run_logger
from prefect_dask import DaskTaskRunner
from pathlib import Path
from typing import List

from ..config import PipelineConfig
from ..tasks.blast import diamond_blastp, process_blast_results, extract_hits
from ..tasks.alignment import align_sequences, trim_alignment, combine_sequences
from ..tasks.phylogeny import build_tree
from ..tasks.taxonomy import assign_taxonomy
from ..tasks.analysis import (
    extract_closest_neighbors,
    decorate_tree,
    calculate_tree_stats,
    extract_phylogenetic_placement,
    combine_placement_results
)
from ..utils.cluster import get_dask_cluster


def get_task_runner(config: PipelineConfig):
    """Get appropriate task runner based on mode"""
    if config.mode == "local":
        return DaskTaskRunner(
            cluster_kwargs={
                "n_workers": 4,
                "threads_per_worker": 2
            }
        )
    else:  # slurm
        return DaskTaskRunner(
            cluster_class="dask_jobqueue.SLURMCluster",
            cluster_kwargs={
                "queue": config.slurm.queue,
                "account": config.slurm.account,
                "cores": config.slurm.cores_per_job,
                "processes": config.slurm.processes_per_job,
                "memory": config.slurm.memory_per_job,
                "walltime": config.slurm.walltime,
            },
            adapt_kwargs={
                "minimum_jobs": config.slurm.min_jobs,
                "maximum_jobs": config.slurm.max_jobs
            }
        )


@flow(name="nngenetree-pipeline", retries=1)
def nngenetree_pipeline(config: PipelineConfig) -> Path:
    """Main NNGeneTree phylogenetic analysis pipeline"""
    logger = get_run_logger()

    # Setup output directory
    output_dir = config.output_dir or Path(f"{config.input_dir}_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all input FASTA files
    input_files = list(config.input_dir.glob("*.faa"))
    logger.info(f"Found {len(input_files)} input FASTA files")

    # Process each sample in parallel
    all_placements = []

    for fasta_file in input_files:
        sample_id = fasta_file.stem
        sample_dir = output_dir / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)

        # Submit tasks (parallel execution via Dask)
        blast_result = diamond_blastp.submit(
            query_fasta=fasta_file,
            blast_db=config.blast_db,
            output_dir=sample_dir,
            threads=config.blast_resources.threads,
            max_hits=config.blast_hits
        )

        subjects = process_blast_results.submit(
            blast_file=blast_result,
            output_dir=sample_dir
        )

        hits = extract_hits.submit(
            subjects_file=subjects,
            blast_db=config.blast_db,
            output_dir=sample_dir
        )

        combined = combine_sequences.submit(
            query_fasta=fasta_file,
            hits_fasta=hits,
            output_dir=sample_dir
        )

        aligned = align_sequences.submit(
            combined_fasta=combined,
            output_dir=sample_dir,
            threads=config.align_resources.threads
        )

        trimmed = trim_alignment.submit(
            aligned_file=aligned,
            output_dir=sample_dir
        )

        tree = build_tree.submit(
            trimmed_alignment=trimmed,
            output_dir=sample_dir,
            builder=config.tree_builder,
            threads=config.tree_resources.threads
        )

        neighbors = extract_closest_neighbors.submit(
            tree_file=tree,
            query_fasta=fasta_file,
            subjects_file=subjects,
            output_dir=sample_dir,
            num_neighbors=config.closest_neighbors
        )

        taxonomy = assign_taxonomy.submit(
            neighbors_csv=neighbors,
            output_dir=sample_dir,
            entrez_email=config.entrez_email
        )

        # These can run in parallel after taxonomy
        decorate_tree.submit(
            tree_file=tree,
            taxonomy_file=taxonomy[0],
            query_fasta=fasta_file,
            output_dir=sample_dir
        )

        calculate_tree_stats.submit(
            tree_file=tree,
            taxonomy_file=taxonomy[0],
            combined_fasta=combined,
            output_dir=sample_dir
        )

        placement = extract_phylogenetic_placement.submit(
            tree_file=tree,
            output_dir=sample_dir,
            query_prefixes=config.query_prefixes
        )

        all_placements.append(placement)

    # Combine all results
    final_result = combine_placement_results.submit(
        placement_files=all_placements,
        output_dir=output_dir
    )

    return final_result.result()


@flow(name="nngenetree-main")
def main_flow(config: PipelineConfig):
    """Entry point flow that configures task runner"""
    task_runner = get_task_runner(config)

    # Run pipeline with appropriate task runner
    with task_runner:
        result = nngenetree_pipeline(config)

    return result
```

---

## Phase 6: CLI Interface

### 6.1 cli.py

```python
import click
from pathlib import Path
from .config import PipelineConfig
from .flows.main import main_flow

@click.group()
def cli():
    """NNGeneTree - Phylogenetic Analysis Pipeline"""
    pass

@cli.command()
@click.option("--input-dir", "-i", required=True, type=Path, help="Input directory with .faa files")
@click.option("--output-dir", "-o", type=Path, help="Output directory")
@click.option("--blast-db", "-d", required=True, type=Path, help="Path to BLAST database")
@click.option("--mode", "-m", type=click.Choice(["local", "slurm"]), default="local")
@click.option("--blast-hits", default=20, help="Number of BLAST hits per query")
@click.option("--closest-neighbors", default=10, help="Number of closest neighbors")
@click.option("--tree-builder", type=click.Choice(["fasttree", "iqtree"]), default="fasttree")
@click.option("--query-prefixes", default="", help="Comma-separated query prefixes")
@click.option("--entrez-email", envvar="ENTREZ_EMAIL", help="Email for NCBI API")
@click.option("--slurm-queue", default="normal", help="SLURM queue name")
@click.option("--slurm-account", default="", help="SLURM account")
@click.option("--max-jobs", default=50, help="Maximum concurrent SLURM jobs")
def run(
    input_dir: Path,
    output_dir: Path,
    blast_db: Path,
    mode: str,
    blast_hits: int,
    closest_neighbors: int,
    tree_builder: str,
    query_prefixes: str,
    entrez_email: str,
    slurm_queue: str,
    slurm_account: str,
    max_jobs: int
):
    """Run the NNGeneTree pipeline"""
    from .config import SLURMConfig

    config = PipelineConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        blast_db=blast_db,
        mode=mode,
        blast_hits=blast_hits,
        closest_neighbors=closest_neighbors,
        tree_builder=tree_builder,
        query_prefixes=query_prefixes,
        entrez_email=entrez_email,
        slurm=SLURMConfig(
            queue=slurm_queue,
            account=slurm_account,
            max_jobs=max_jobs
        )
    )

    result = main_flow(config)
    click.echo(f"Pipeline complete! Results: {result}")

if __name__ == "__main__":
    cli()
```

---

## Phase 7: Migration Steps

### Step-by-Step Implementation Order

1. **Setup Environment** (Day 1)
   - Update pixi.toml with new dependencies
   - Create package structure
   - Run `pixi install`

2. **Configuration System** (Day 1)
   - Implement config.py with Pydantic
   - Test configuration loading

3. **Cluster Factory** (Day 1)
   - Implement cluster.py
   - Test local cluster creation
   - Test SLURM cluster creation

4. **Task Migration** (Days 2-3)
   - Migrate each task one-by-one
   - Port existing bin/ scripts as task implementations
   - Add caching decorators
   - Add retry logic

5. **Flow Definition** (Day 3)
   - Implement main flow
   - Wire up task dependencies
   - Test with small dataset locally

6. **CLI Interface** (Day 4)
   - Implement Click CLI
   - Add all configuration options
   - Test end-to-end locally

7. **SLURM Integration** (Day 4)
   - Test SLURM cluster creation
   - Verify job submission
   - Test adaptive scaling

8. **Testing & Documentation** (Day 5)
   - Write unit tests for tasks
   - Write integration tests
   - Create migration documentation
   - Update README

---

## Phase 8: Key Differences from Nextflow

| Aspect | Nextflow | Prefect-Dask |
|--------|----------|--------------|
| Task Definition | DSL process blocks | Python @task decorators |
| Parallelism | Channel-based | .submit() futures |
| Caching | Hash-based work dir | cache_policy + expiration |
| Resume | -resume flag | Automatic via cache |
| SLURM | executor config | DaskTaskRunner + SLURMCluster |
| Error Handling | errorStrategy | retries + retry_delay_seconds |
| Monitoring | Nextflow Tower | Prefect UI / Cloud |
| Configuration | Groovy config | Pydantic + env vars |

---

## Phase 9: Resource Mapping

### Per-Task Resources (SLURM Mode)

| Task | Threads | Memory | Time | Notes |
|------|---------|--------|------|-------|
| diamond_blastp | 8 | 64GB | 24h | CPU + I/O intensive |
| extract_hits | 1 | 16GB | 4h | I/O intensive |
| align_sequences | 8 | 32GB | 24h | CPU intensive |
| build_tree | 8 | 32GB | 24h | CPU intensive |
| assign_taxonomy | 1 | 4GB | 1h | Rate-limited API |
| Others | 1 | 4GB | 10m | Lightweight |

### SLURM Job Configuration

```python
SLURMCluster(
    cores=24,           # 24 cores per SLURM job
    processes=6,        # 6 Dask workers per job
    memory="64GB",      # 64GB per job
    walltime="24:00:00" # 24-hour walltime
)
# Result: Each worker gets 4 threads, ~10GB memory
```

---

## Acceptance Criteria

1. **Functional Parity**: All 14 pipeline steps produce identical outputs
2. **Local Mode**: Runs on single node with multiprocessing
3. **SLURM Mode**: Distributes across cluster nodes via dask-jobqueue
4. **Caching**: Failed runs resume from last completed task
5. **CLI**: Simple command-line interface with all options
6. **Configuration**: Environment variables and config files supported
7. **Testing**: Unit tests for tasks, integration test for flow
8. **Documentation**: Migration guide and usage documentation

---

## Files to Create

```
src/nngenetree/
├── __init__.py
├── cli.py
├── config.py
├── flows/
│   ├── __init__.py
│   └── main.py
├── tasks/
│   ├── __init__.py
│   ├── blast.py
│   ├── alignment.py
│   ├── phylogeny.py
│   ├── taxonomy.py
│   └── analysis.py
└── utils/
    ├── __init__.py
    ├── io.py
    └── cluster.py

tests/
├── __init__.py
├── conftest.py
├── test_tasks.py
└── test_flows.py

docs/
└── convert-to-prefect-dask.md
```

## Critical Files from Current Implementation to Refactor

- `bin/process_blast_for_extraction.py` → tasks/blast.py
- `bin/combine_and_deduplicate.py` → tasks/alignment.py
- `bin/extract_closest_neighbors.py` → tasks/analysis.py
- `bin/parse_closest_neighbors.py` → tasks/taxonomy.py
- `bin/decorate_tree.py` → tasks/analysis.py
- `bin/tree_stats.py` → tasks/analysis.py
- `bin/extract_phylogenetic_neighbors.py` → tasks/analysis.py

---

## User Preferences (Confirmed)

1. **Script Migration**: Refactor existing bin/ scripts into clean task modules (not import)
2. **Prefect Backend**: Local-only execution (no Prefect Cloud/Server)
3. **NCBI Rate Limiting**: Sequential requests with disk cache for reuse

---

## Taxonomy Caching Implementation

```python
# tasks/taxonomy.py
from pathlib import Path
import json
import time
from prefect import task
from Bio import Entrez

class TaxonomyCache:
    """Persistent disk cache for NCBI taxonomy lookups"""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if self.cache_file.exists():
            return json.loads(self.cache_file.read_text())
        return {}

    def save(self):
        self.cache_file.write_text(json.dumps(self.cache, indent=2))

    def get(self, accession: str) -> str | None:
        return self.cache.get(accession)

    def set(self, accession: str, taxonomy: str):
        self.cache[accession] = taxonomy
        self.save()  # Persist immediately


@task(
    name="assign_taxonomy",
    retries=3,
    retry_delay_seconds=[30, 60, 120]
)
def assign_taxonomy(
    neighbors_csv: Path,
    output_dir: Path,
    entrez_email: str,
    cache_dir: Path
) -> tuple[Path, Path]:
    """Add NCBI taxonomy with rate limiting and disk cache"""

    cache = TaxonomyCache(cache_dir / "taxonomy_cache.json")
    Entrez.email = entrez_email

    # Read neighbors, lookup taxonomy with cache
    # Rate limit: 0.34s between uncached requests
    ...
```

---

## Local-Only Prefect Configuration

```python
# No Prefect server required - runs entirely locally
# Results stored in local SQLite database

# Optional: Configure local storage for results
import os
os.environ["PREFECT_LOCAL_STORAGE_PATH"] = ".nngenetree_results"

# Flow runs are tracked locally, can be inspected via:
# prefect flow-run ls
# prefect flow-run inspect <flow-run-id>
```
