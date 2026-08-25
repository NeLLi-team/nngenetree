/*
 * BLAST Result Processing
 * Process BLAST results to extract unique subjects
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
        --min-hits ${params.min_hits}
    """
}
