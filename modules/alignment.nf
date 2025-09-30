/*
 * Sequence Alignment
 * MAFFT alignment and TrimAl trimming
 */

process ALIGN_SEQUENCES {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}/aln", mode: 'copy'

    cpus params.resources.align_sequences.threads
    memory "${params.resources.align_sequences.mem_mb} MB"
    time params.resources.align_sequences.time
    disk "${params.resources.align_sequences.disk_mb} MB"

    input:
    tuple val(sample_id), path(check_done), path(combined_sequences)

    output:
    tuple val(sample_id), path("aligned_sequences.msa"), emit: aligned_sequences

    script:
    """
    mafft --thread ${task.cpus} ${combined_sequences} > aligned_sequences.msa
    """
}

process TRIM_ALIGNMENT {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}/aln", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(check_done), path(aligned_sequences)

    output:
    tuple val(sample_id), path("trimmed_alignment.msa"), emit: trimmed_alignment

    script:
    """
    trimal -in ${aligned_sequences} -out trimmed_alignment.msa -gt 0.1
    """
}