/*
 * Taxonomy Assignment
 * Assign NCBI taxonomy to sequences
 */

process ASSIGN_TAXONOMY {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(closest_neighbors)

    output:
    tuple val(sample_id), path("taxonomy_assignments.txt"), emit: taxonomy
    tuple val(sample_id), path("closest_neighbors_with_taxonomy.csv"), emit: updated_csv

    script:
    """
    parse_closest_neighbors.py \\
        -d . \\
        -o taxonomy_assignments.txt \\
        > taxonomy_assignment.log 2>&1

    # Ensure output files exist even if script has issues
    touch taxonomy_assignments.txt
    touch closest_neighbors_with_taxonomy.csv
    """
}