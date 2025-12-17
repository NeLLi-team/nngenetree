/*
 * Extract Hit Sequences
 * Retrieve hit sequences from BLAST database
 */

process EXTRACT_HITS {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus params.resources.extract_hits.threads
    memory "${params.resources.extract_hits.mem_mb} MB"
    time params.resources.extract_hits.time

    input:
    tuple val(sample_id), path(check_done), path(unique_subjects)

    output:
    tuple val(sample_id), path("extracted_hits.faa"), emit: extracted_hits
    tuple val(sample_id), path("extract_hits_errors.log"), emit: error_log

    script:
    """
    blastdbcmd \\
        -db ${params.blast_db} \\
        -entry_batch ${unique_subjects} \\
        > extracted_hits.faa 2> extract_hits_errors.log || true
    """
}