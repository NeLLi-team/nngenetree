/*
 * Phylogenetic Analysis
 * IQ-TREE and neighbor extraction
 */

process BUILD_TREE {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}/tree", mode: 'copy'

    cpus params.resources.build_tree.threads
    memory "${params.resources.build_tree.mem_mb} MB"
    time params.resources.build_tree.time

    input:
    tuple val(sample_id), path(check_done), path(trimmed_alignment)

    output:
    tuple val(sample_id), path("final_tree.treefile"), emit: tree
    tuple val(sample_id), path("final_tree.iqtree"), emit: log
    tuple val(sample_id), path("final_tree.*"), emit: all_files

    script:
    """
    iqtree -s ${trimmed_alignment} \\
        -m LG+G4 \\
        -T ${task.cpus} \\
        --prefix final_tree
    """
}

process EXTRACT_CLOSEST_NEIGHBORS {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(query_fasta), path(unique_subjects), path(tree)

    output:
    tuple val(sample_id), path("closest_neighbors.csv"), emit: closest_neighbors

    script:
    def query_filter_cmd = params.query_filter ? "--query_filter ${params.query_filter}" : ""
    """
    extract_closest_neighbors.py \\
        --tree ${tree} \\
        --query ${query_fasta} \\
        --subjects ${unique_subjects} \\
        --output closest_neighbors.csv \\
        --num_neighbors ${params.closest_neighbors} \\
        ${query_filter_cmd}
    """
}