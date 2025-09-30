/*
 * DIAMOND BLASTP Process
 * Run DIAMOND BLASTP search against database
 */

process DIAMOND_BLASTP {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus params.resources.run_diamond_blastp.threads
    memory "${params.resources.run_diamond_blastp.mem_mb} MB"
    time params.resources.run_diamond_blastp.time

    input:
    tuple val(sample_id), path(query_fasta)

    output:
    tuple val(sample_id), path("blast_results.m8"), emit: blast_results

    script:
    """
    diamond blastp \\
        -d ${params.blast_db}.dmnd \\
        -q ${query_fasta} \\
        -o blast_results.m8 \\
        -p ${task.cpus} \\
        -k ${params.blast_hits} \\
        --outfmt 6
    """
}