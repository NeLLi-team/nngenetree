"""Dask cluster factory for local and SLURM execution."""

from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

from dask.distributed import Client, LocalCluster

if TYPE_CHECKING:
    from dask.distributed import Client as DaskClient

    from ..config import PipelineConfig


@contextmanager
def get_dask_client(config: "PipelineConfig") -> Generator["DaskClient", None, None]:
    """Create a Dask client based on execution mode.

    Args:
        config: Pipeline configuration with mode and cluster settings.

    Yields:
        Dask Client connected to appropriate cluster.
    """
    if config.mode == "local":
        cluster = _create_local_cluster(config)
    else:
        cluster = _create_slurm_cluster(config)

    client = Client(cluster)
    try:
        yield client
    finally:
        client.close()
        cluster.close()


def _create_local_cluster(config: "PipelineConfig") -> LocalCluster:
    """Create a local Dask cluster."""
    return LocalCluster(
        n_workers=config.local_workers,
        threads_per_worker=config.local_threads_per_worker,
        memory_limit=f"{config.blast_resources.memory_gb // config.local_workers}GB",
    )


def _create_slurm_cluster(config: "PipelineConfig"):
    """Create a SLURM cluster via dask-jobqueue."""
    from dask_jobqueue import SLURMCluster

    slurm = config.slurm

    # Build job extra directives
    job_extra_directives = []
    if slurm.qos:
        job_extra_directives.append(f"--qos={slurm.qos}")
    if slurm.account:
        job_extra_directives.append(f"--account={slurm.account}")

    cluster = SLURMCluster(
        queue=slurm.queue,
        cores=slurm.cores_per_job,
        processes=slurm.processes_per_job,
        memory=slurm.memory_per_job,
        walltime=slurm.walltime,
        job_extra_directives=job_extra_directives,
        local_directory="/tmp/dask-worker-space",
        log_directory=str(config.get_output_dir() / "dask_logs"),
    )

    # Enable adaptive scaling
    cluster.adapt(minimum_jobs=slurm.min_jobs, maximum_jobs=slurm.max_jobs)

    return cluster


def get_cluster_info(config: "PipelineConfig") -> dict:
    """Get information about cluster configuration.

    Returns:
        Dictionary with cluster configuration details.
    """
    if config.mode == "local":
        return {
            "mode": "local",
            "workers": config.local_workers,
            "threads_per_worker": config.local_threads_per_worker,
            "total_threads": config.local_workers * config.local_threads_per_worker,
        }

    slurm = config.slurm
    return {
        "mode": "slurm",
        "queue": slurm.queue,
        "account": slurm.account,
        "cores_per_job": slurm.cores_per_job,
        "processes_per_job": slurm.processes_per_job,
        "memory_per_job": slurm.memory_per_job,
        "walltime": slurm.walltime,
        "min_jobs": slurm.min_jobs,
        "max_jobs": slurm.max_jobs,
    }
