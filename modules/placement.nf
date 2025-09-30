/*
 * Phylogenetic Placement
 * Extract phylogenetic neighbors with taxonomy and combine results
 */

process EXTRACT_PHYLOGENETIC_PLACEMENT {
    tag "$sample_id"
    publishDir "${params.output_dir}/${sample_id}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_id), path(tree)

    output:
    tuple val(sample_id), path("placement_results.json"), emit: placement_json
    tuple val(sample_id), path("placement_results.csv"), emit: placement_csv

    script:
    """
    extract_phylogenetic_neighbors.py \\
        --tree ${tree} \\
        --query-prefixes ${params.query_prefixes} \\
        --output-json placement_results.json \\
        --output-csv placement_results.csv \\
        --num-neighbors ${params.num_neighbors_placement} \\
        --self-hit-threshold ${params.self_hit_threshold} \\
        2> phylogenetic_placement.log
    """
}

process COMBINE_PLACEMENT_RESULTS {
    publishDir "${params.output_dir}", mode: 'copy'

    cpus 1

    input:
    tuple val(sample_ids), path(placement_files)

    output:
    path("combined_placement_results.json"), emit: combined_json

    script:
    """
    #!/usr/bin/env python3
    import json
    import os
    from pathlib import Path

    combined_results = {
        "orthogroups": [],
        "total_queries": 0,
        "overall_taxonomy_summary": {
            "domains": {},
            "total_neighbors": 0
        }
    }

    # Process each placement file with its sample ID
    placement_files = "${placement_files}".split()
    sample_ids = "${sample_ids}".split()

    for sample_id, placement_file in zip(sample_ids, placement_files):
        og_name = sample_id

        with open(placement_file, 'r') as f:
            data = json.load(f)

        # Add orthogroup data
        combined_results["orthogroups"].append({
            "name": og_name,
            "query_count": data.get("query_count", 0),
            "taxonomy_summary": data.get("taxonomy_summary", {}),
            "placements": data.get("placements", [])
        })

        # Update totals
        combined_results["total_queries"] += data.get("query_count", 0)

        # Aggregate taxonomy counts
        if "taxonomy_summary" in data and "domains" in data["taxonomy_summary"]:
            for domain, count in data["taxonomy_summary"]["domains"].items():
                current_count = combined_results["overall_taxonomy_summary"]["domains"].get(domain, 0)
                combined_results["overall_taxonomy_summary"]["domains"][domain] = current_count + count
                combined_results["overall_taxonomy_summary"]["total_neighbors"] += count

    # Write combined results
    with open("combined_placement_results.json", 'w') as f:
        json.dump(combined_results, f, indent=2)
    """
}