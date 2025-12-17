/*
 * Tree Visualization and Statistics
 * Generate tree visualizations and calculate statistics
 */

process DECORATE_TREE {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}/tree", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(tree), path(taxonomy), path(taxonomy_csv), path(query_fasta)

    output:
    tuple val(sample_id), path("decorated_tree.png"), emit: decorated_tree
    tuple val(sample_id), path("../itol/*"), emit: itol_files, optional: true

    script:
    """
    mkdir -p ../itol

    decorate_tree.py \\
        ${tree} \\
        ${taxonomy} \\
        ${query_fasta} \\
        decorated_tree.png \\
        ../itol \\
        ${params.itol_tax_level} \\
        2> decorate_tree.log
    """
}

process CALCULATE_TREE_STATS {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}/tree", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(tree), path(taxonomy), path(taxonomy_csv), path(combined_sequences)

    output:
    tuple val(sample_id), path("tree_stats.tab"), emit: tree_stats

    script:
    """
    tree_stats.py \\
        ${tree} \\
        ${taxonomy} \\
        ${combined_sequences} \\
        tree_stats.tab \\
        2> tree_stats.log
    """
}