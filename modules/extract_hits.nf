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
    tuple val(sample_id), path(unique_subjects)

    output:
    tuple val(sample_id), path("extracted_hits.faa"), emit: extracted_hits
    tuple val(sample_id), path("extract_hits_errors.log"), emit: error_log

    script:
    // blastdbcmd exits 1 when any accession is missing; keep what it found and
    // log the counts. main.nf skips samples with no extracted sequence.
    """
    blastdbcmd \\
        -db ${params.blast_db} \\
        -entry_batch ${unique_subjects} \\
        > extracted_hits.faa 2> extract_hits_errors.log || true
    n_requested=\$(grep -c . ${unique_subjects} || true)
    n_extracted=\$(grep -c '^>' extracted_hits.faa || true)
    echo "Extracted \${n_extracted} of \${n_requested} requested sequences" >> extract_hits_errors.log
    """
}