/*
 * Taxonomy Assignment
 * Assign NCBI taxonomy to sequences
 */

process ASSIGN_TAXONOMY {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1
    // NCBI allows 3 Entrez requests per second per IP without an API key;
    // one lookup at a time keeps parallel samples under that limit.
    maxForks 1
    // Entrez requests have no socket timeout; a stalled connection is killed
    // here and the task retried instead of blocking the serialized queue.
    time '30m'

    input:
    tuple val(sample_id), path(closest_neighbors), path(unique_subjects)

    output:
    tuple val(sample_id), path("taxonomy_assignments.txt"), emit: taxonomy
    tuple val(sample_id), path("closest_neighbors_with_taxonomy.csv"), emit: updated_csv

    script:
    """
    parse_closest_neighbors.py \\
        -d . \\
        --subjects ${unique_subjects} \\
        --og ${sample_id} \\
        -o taxonomy_assignments.txt \\
        > taxonomy_assignment.log 2>&1
    """
}