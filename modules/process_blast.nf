/*
 * BLAST Result Processing
 * Process BLAST results and validate output
 */

process PROCESS_BLAST_RESULTS {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(blast_result)

    output:
    tuple val(sample_id), path("unique_subjects.txt"), emit: unique_subjects

    script:
    """
    process_blast_for_extraction.py \\
        ${blast_result} \\
        unique_subjects.txt \\
        --max-hits ${params.blast_hits} \\
        --min-hits 5
    """
}

process CHECK_BLAST_OUTPUT {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(unique_subjects)

    output:
    tuple val(sample_id), path("check_blast_output.done"), emit: check_done
    tuple val(sample_id), path("check_blast_output.log"), emit: check_log

    script:
    """
    check_blast_output.py ${unique_subjects} > check_blast_output.log 2>&1
    touch check_blast_output.done
    """
}