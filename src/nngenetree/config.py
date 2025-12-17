"""Configuration management for NNGeneTree pipeline using Pydantic."""

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ResourceConfig(BaseSettings):
    """Per-task resource configuration."""

    model_config = SettingsConfigDict(frozen=True)

    threads: int = Field(default=8, ge=1, le=64)
    memory_gb: int = Field(default=32, ge=1, le=512)
    time_hours: int = Field(default=24, ge=1, le=168)


class SLURMConfig(BaseSettings):
    """SLURM cluster configuration."""

    model_config = SettingsConfigDict(
        env_prefix="NNGENETREE_SLURM_",
        frozen=True,
    )

    queue: str = Field(default="jgi_normal", description="SLURM queue/partition name")
    account: str = Field(
        default="grp-org-sc-mgs", description="SLURM account for billing"
    )
    qos: str = Field(default="jgi_normal", description="Quality of Service")
    cores_per_job: int = Field(default=24, ge=1, le=128, description="Cores per job")
    processes_per_job: int = Field(
        default=3, ge=1, le=24, description="Dask workers per SLURM job"
    )
    memory_per_job: str = Field(default="64GB", description="Memory per SLURM job")
    walltime: str = Field(default="24:00:00", description="Job walltime")
    max_jobs: int = Field(default=50, ge=1, le=200, description="Maximum SLURM jobs")
    min_jobs: int = Field(default=2, ge=1, le=50, description="Minimum SLURM jobs")


class PipelineConfig(BaseSettings):
    """Main pipeline configuration."""

    model_config = SettingsConfigDict(
        env_prefix="NNGENETREE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Execution mode
    mode: Literal["local", "slurm"] = Field(
        default="local", description="Execution mode: local or slurm"
    )

    # Input/Output paths
    input_dir: Path = Field(description="Directory containing .faa files")
    output_dir: Path | None = Field(
        default=None, description="Output directory (default: {input_dir}_output)"
    )
    blast_db: Path = Field(description="Path to BLAST/DIAMOND database")

    # NCBI API configuration
    entrez_email: str = Field(
        default="fschulz@lbl.gov", description="Email for NCBI Entrez API"
    )

    # Pipeline parameters
    blast_hits: int = Field(
        default=20, ge=1, le=100, description="Number of BLAST hits per query"
    )
    closest_neighbors: int = Field(
        default=10, ge=1, le=50, description="Number of closest neighbors to extract"
    )
    query_prefixes: str = Field(
        default="GCMeta_,GTDB_,spire_mag_",
        description="Comma-separated prefixes to identify query sequences",
    )
    tree_builder: Literal["fasttree", "iqtree"] = Field(
        default="fasttree", description="Tree building method"
    )

    # Resource configurations
    blast_resources: ResourceConfig = Field(
        default_factory=lambda: ResourceConfig(threads=8, memory_gb=64, time_hours=24)
    )
    align_resources: ResourceConfig = Field(
        default_factory=lambda: ResourceConfig(threads=8, memory_gb=32, time_hours=24)
    )
    tree_resources: ResourceConfig = Field(
        default_factory=lambda: ResourceConfig(threads=8, memory_gb=32, time_hours=24)
    )

    # SLURM configuration
    slurm: SLURMConfig = Field(default_factory=SLURMConfig)

    # Caching configuration
    cache_dir: Path = Field(
        default=Path(".nngenetree_cache"), description="Directory for caching results"
    )
    enable_caching: bool = Field(default=True, description="Enable result caching")

    # Local execution settings
    local_workers: int = Field(
        default=4, ge=1, le=32, description="Number of local Dask workers"
    )
    local_threads_per_worker: int = Field(
        default=2, ge=1, le=16, description="Threads per local worker"
    )

    @field_validator("input_dir", "blast_db", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        """Resolve paths to absolute."""
        return Path(v).resolve()

    @field_validator("output_dir", mode="before")
    @classmethod
    def resolve_output_path(cls, v: str | Path | None) -> Path | None:
        """Resolve output path if provided."""
        if v is None:
            return None
        return Path(v).resolve()

    def get_output_dir(self) -> Path:
        """Get output directory, creating default if not specified."""
        if self.output_dir is not None:
            return self.output_dir
        return Path(f"{self.input_dir}_output").resolve()

    def get_query_prefix_list(self) -> list[str]:
        """Get query prefixes as a list."""
        if not self.query_prefixes:
            return []
        return [p.strip() for p in self.query_prefixes.split(",") if p.strip()]


def load_config(**overrides) -> PipelineConfig:
    """Load configuration from environment and overrides."""
    return PipelineConfig(**overrides)
