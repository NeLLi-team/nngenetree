/*
 * Combine Sequences
 * Merge query and hit sequences with deduplication
 */

process COMBINE_SEQUENCES {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(query_fasta), path(hits_fasta)

    output:
    tuple val(sample_id), path("combined_sequences.faa"), emit: combined_sequences

    script:
    """
    combine_and_deduplicate.py \\
        ${query_fasta} \\
        ${hits_fasta} \\
        combined_sequences.faa \\
        --deduplicate-by-sequence \\
        2> combine_sequences.log
    """
}