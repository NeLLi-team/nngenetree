"""Command-line interface for NNGeneTree pipeline."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .config import PipelineConfig, ResourceConfig, SLURMConfig
from .flows.main import run_pipeline
from .utils.cluster import get_cluster_info

# Load .env file before CLI parsing so envvar options work
load_dotenv()

app = typer.Typer(
    name="nngenetree",
    help="NNGeneTree - Phylogenetic analysis pipeline with Prefect-Dask",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    input_dir: Annotated[
        Path,
        typer.Option(
            "--input-dir",
            "-i",
            help="Input directory containing .faa files",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ],
    blast_db: Annotated[
        Optional[Path],
        typer.Option(
            "--blast-db",
            "-d",
            envvar="NNGENETREE_BLAST_DB",
            help="Path to BLAST/DIAMOND database",
            resolve_path=True,
        ),
    ] = None,
    output_dir: Annotated[
        Optional[Path],
        typer.Option(
            "--output-dir",
            "-o",
            help="Output directory (default: {input_dir}_output)",
            resolve_path=True,
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "--mode",
            "-m",
            envvar="NNGENETREE_MODE",
            help="Execution mode: local or slurm",
        ),
    ] = "local",
    blast_hits: Annotated[
        int,
        typer.Option(
            "--blast-hits",
            help="Number of BLAST hits per query",
        ),
    ] = 20,
    closest_neighbors: Annotated[
        int,
        typer.Option(
            "--closest-neighbors",
            help="Number of closest neighbors to extract",
        ),
    ] = 10,
    tree_builder: Annotated[
        str,
        typer.Option(
            "--tree-builder",
            help="Tree building method: fasttree or iqtree",
        ),
    ] = "fasttree",
    query_prefixes: Annotated[
        str,
        typer.Option(
            "--query-prefixes",
            help="Comma-separated prefixes to identify query sequences",
        ),
    ] = "GCMeta_,GTDB_,spire_mag_",
    entrez_email: Annotated[
        str,
        typer.Option(
            "--entrez-email",
            envvar="ENTREZ_EMAIL",
            help="Email for NCBI Entrez API",
        ),
    ] = "fschulz@lbl.gov",
    slurm_queue: Annotated[
        str,
        typer.Option(
            "--slurm-queue",
            help="SLURM queue/partition name",
        ),
    ] = "jgi_normal",
    slurm_account: Annotated[
        str,
        typer.Option(
            "--slurm-account",
            help="SLURM account for billing",
        ),
    ] = "grp-org-sc-mgs",
    max_jobs: Annotated[
        int,
        typer.Option(
            "--max-jobs",
            envvar="NNGENETREE_SLURM_MAX_JOBS",
            help="Maximum concurrent SLURM jobs",
        ),
    ] = 50,
    slurm_cores: Annotated[
        int,
        typer.Option(
            "--slurm-cores",
            envvar="NNGENETREE_SLURM_CORES_PER_JOB",
            help="Cores per SLURM job",
        ),
    ] = 32,
    slurm_workers: Annotated[
        int,
        typer.Option(
            "--slurm-workers",
            envvar="NNGENETREE_SLURM_PROCESSES_PER_JOB",
            help="Dask workers per SLURM job",
        ),
    ] = 8,
    slurm_walltime: Annotated[
        str,
        typer.Option(
            "--slurm-walltime",
            envvar="NNGENETREE_SLURM_WALLTIME",
            help="SLURM job walltime (HH:MM:SS)",
        ),
    ] = "08:00:00",
    slurm_memory: Annotated[
        str,
        typer.Option(
            "--slurm-memory",
            envvar="NNGENETREE_SLURM_MEMORY_PER_JOB",
            help="Memory per SLURM job (e.g., 128GB, 192GB)",
        ),
    ] = "128GB",
    threads: Annotated[
        int,
        typer.Option(
            "--threads",
            "-t",
            help="Threads for CPU-intensive tasks",
        ),
    ] = 8,
    local_workers: Annotated[
        int,
        typer.Option(
            "--local-workers",
            "-w",
            help="Number of local Dask workers",
        ),
    ] = 4,
    local_threads_per_worker: Annotated[
        int,
        typer.Option(
            "--threads-per-worker",
            help="Threads per local Dask worker",
        ),
    ] = 2,
) -> None:
    """Run the NNGeneTree phylogenetic analysis pipeline."""
    # Validate blast_db
    if blast_db is None:
        console.print(
            "[red]Error: --blast-db is required. "
            "Set via CLI or NNGENETREE_BLAST_DB environment variable.[/red]"
        )
        raise typer.Exit(1)

    # Validate mode
    if mode not in ("local", "slurm"):
        console.print(f"[red]Error: Invalid mode '{mode}'. Use 'local' or 'slurm'[/red]")
        raise typer.Exit(1)

    # Validate tree builder
    if tree_builder not in ("fasttree", "iqtree"):
        console.print(
            f"[red]Error: Invalid tree builder '{tree_builder}'. "
            "Use 'fasttree' or 'iqtree'[/red]"
        )
        raise typer.Exit(1)

    # Build configuration
    slurm_config = SLURMConfig(
        queue=slurm_queue,
        account=slurm_account,
        max_jobs=max_jobs,
        cores_per_job=slurm_cores,
        processes_per_job=slurm_workers,
        memory_per_job=slurm_memory,
        walltime=slurm_walltime,
    )

    # Create resource configs with specified threads
    resource_config = ResourceConfig(threads=threads)

    config = PipelineConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        blast_db=blast_db,
        mode=mode,  # type: ignore
        blast_hits=blast_hits,
        closest_neighbors=closest_neighbors,
        tree_builder=tree_builder,  # type: ignore
        query_prefixes=query_prefixes,
        entrez_email=entrez_email,
        slurm=slurm_config,
        blast_resources=resource_config,
        align_resources=resource_config,
        tree_resources=resource_config,
        local_workers=local_workers,
        local_threads_per_worker=local_threads_per_worker,
    )

    # Display configuration
    _display_config(config)

    # Run pipeline
    try:
        result = run_pipeline(config)
        console.print(
            Panel(
                f"[green]Pipeline complete![/green]\n\nResults: {result}",
                title="Success",
            )
        )
    except Exception as e:
        console.print(f"[red]Pipeline failed: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def info() -> None:
    """Display information about NNGeneTree."""
    console.print(
        Panel(
            f"[bold]NNGeneTree[/bold] v{__version__}\n\n"
            "Phylogenetic analysis pipeline with Prefect-Dask\n\n"
            "[dim]Pipeline steps:[/dim]\n"
            "  1. DIAMOND BLASTP against NR database\n"
            "  2. Extract hit sequences\n"
            "  3. Multiple sequence alignment (MAFFT)\n"
            "  4. Alignment trimming (TrimAl)\n"
            "  5. Tree building (FastTree/IQ-TREE)\n"
            "  6. Extract closest neighbors\n"
            "  7. Assign NCBI taxonomy\n"
            "  8. Phylogenetic placement",
            title="About NNGeneTree",
        )
    )


@app.command()
def version() -> None:
    """Display version information."""
    console.print(f"NNGeneTree v{__version__}")


def _display_config(config: PipelineConfig) -> None:
    """Display configuration in a nice table."""
    table = Table(title="Pipeline Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Input Directory", str(config.input_dir))
    table.add_row("Output Directory", str(config.get_output_dir()))
    table.add_row("BLAST Database", str(config.blast_db))
    table.add_row("Execution Mode", config.mode)
    table.add_row("Tree Builder", config.tree_builder)
    table.add_row("BLAST Hits", str(config.blast_hits))
    table.add_row("Closest Neighbors", str(config.closest_neighbors))
    table.add_row("Threads", str(config.blast_resources.threads))

    if config.mode == "slurm":
        cluster_info = get_cluster_info(config)
        table.add_row("SLURM Queue", cluster_info["queue"])
        table.add_row("SLURM Account", cluster_info["account"])
        table.add_row("Cores/Job", str(cluster_info["cores_per_job"]))
        table.add_row("Workers/Job", str(cluster_info["processes_per_job"]))
        table.add_row("Memory/Job", cluster_info["memory_per_job"])
        table.add_row("Walltime", cluster_info["walltime"])
        table.add_row("Max Jobs", str(cluster_info["max_jobs"]))

    console.print(table)
    console.print()


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
