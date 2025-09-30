#!/usr/bin/env nextflow

/*
 * NNGeneTree - Nextflow Pipeline
 * ================================
 * Phylogenetic analysis and taxonomic classification of protein sequences
 *
 * Converted from Snakemake to Nextflow
 * Version: 1.0.0
 */

nextflow.enable.dsl=2

// Import process modules
include { DIAMOND_BLASTP } from './modules/diamond_blastp'
include { PROCESS_BLAST_RESULTS } from './modules/process_blast'
include { CHECK_BLAST_OUTPUT } from './modules/process_blast'
include { EXTRACT_HITS } from './modules/extract_hits'
include { COMBINE_SEQUENCES } from './modules/combine_sequences'
include { ALIGN_SEQUENCES } from './modules/alignment'
include { TRIM_ALIGNMENT } from './modules/alignment'
include { BUILD_TREE } from './modules/phylogeny'
include { EXTRACT_CLOSEST_NEIGHBORS } from './modules/phylogeny'
include { ASSIGN_TAXONOMY } from './modules/taxonomy'
include { DECORATE_TREE } from './modules/visualization'
include { CALCULATE_TREE_STATS } from './modules/visualization'
include { EXTRACT_PHYLOGENETIC_PLACEMENT } from './modules/placement'
include { COMBINE_PLACEMENT_RESULTS } from './modules/placement'

// Print startup banner
log.info """
╔════════════════════════════════════════╗
║   🧬 NNGeneTree Pipeline (Nextflow)    ║
╠════════════════════════════════════════╣
║ Version: 1.0.0                         ║
║ Input:   ${params.input_dir}
║ Output:  ${params.output_dir}
║ Database: ${params.blast_db}
╚════════════════════════════════════════╝
""".stripIndent()

// Main workflow
workflow {
    // Create input channel from FASTA files
    input_fasta_ch = Channel
        .fromPath("${params.input_dir}/*.faa")
        .map { file -> tuple(file.baseName, file) }

    // Log number of input files found
    input_fasta_ch
        .count()
        .subscribe { count -> log.info "Found ${count} input FASTA file(s)" }

    // Re-create channel for processing (consumed by count)
    input_fasta_ch = Channel
        .fromPath("${params.input_dir}/*.faa")
        .map { file -> tuple(file.baseName, file) }

    // Step 1: DIAMOND BLASTP search
    DIAMOND_BLASTP(input_fasta_ch)

    // Step 2: Process BLAST results to extract unique subjects
    PROCESS_BLAST_RESULTS(DIAMOND_BLASTP.out.blast_results)

    // Step 3: Check BLAST output validity
    CHECK_BLAST_OUTPUT(PROCESS_BLAST_RESULTS.out.unique_subjects)

    // Step 4: Extract hit sequences from database
    EXTRACT_HITS(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(PROCESS_BLAST_RESULTS.out.unique_subjects)
    )

    // Step 5: Combine query and hit sequences (with deduplication)
    COMBINE_SEQUENCES(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(input_fasta_ch, by: 0)
            .map { sample_id, check, query_file -> tuple(sample_id, query_file) }
            .join(EXTRACT_HITS.out.extracted_hits)
    )

    // Step 6: Align sequences with MAFFT
    ALIGN_SEQUENCES(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(COMBINE_SEQUENCES.out.combined_sequences)
    )

    // Step 7: Trim alignment with TrimAl
    TRIM_ALIGNMENT(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(ALIGN_SEQUENCES.out.aligned_sequences)
    )

    // Step 8: Build phylogenetic tree with IQ-TREE
    BUILD_TREE(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(TRIM_ALIGNMENT.out.trimmed_alignment)
    )

    // Step 9: Extract closest neighbors from tree
    EXTRACT_CLOSEST_NEIGHBORS(
        input_fasta_ch
            .join(PROCESS_BLAST_RESULTS.out.unique_subjects)
            .join(BUILD_TREE.out.tree)
    )

    // Step 10: Assign NCBI taxonomy to neighbors
    ASSIGN_TAXONOMY(EXTRACT_CLOSEST_NEIGHBORS.out.closest_neighbors)

    // Step 11: Decorate tree with taxonomy and generate visualization
    DECORATE_TREE(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(BUILD_TREE.out.tree)
            .join(ASSIGN_TAXONOMY.out.taxonomy)
            .join(ASSIGN_TAXONOMY.out.updated_csv)
            .join(input_fasta_ch, by: 0)
            .map { sample_id, check, tree, taxonomy, csv, query ->
                tuple(sample_id, tree, taxonomy, csv, query)
            }
    )

    // Step 12: Calculate tree statistics
    CALCULATE_TREE_STATS(
        CHECK_BLAST_OUTPUT.out.check_done
            .join(BUILD_TREE.out.tree)
            .join(ASSIGN_TAXONOMY.out.taxonomy)
            .join(ASSIGN_TAXONOMY.out.updated_csv)
            .join(COMBINE_SEQUENCES.out.combined_sequences)
            .map { sample_id, check, tree, taxonomy, csv, combined ->
                tuple(sample_id, tree, taxonomy, csv, combined)
            }
    )

    // Step 13: Extract phylogenetic placement with taxonomy
    EXTRACT_PHYLOGENETIC_PLACEMENT(BUILD_TREE.out.tree)

    // Step 14: Combine all placement results
    all_placements = EXTRACT_PHYLOGENETIC_PLACEMENT.out.placement_json
        .toList()
        .map { list ->
            def sample_ids = list.collect { it[0] }
            def files = list.collect { it[1] }
            tuple(sample_ids, files)
        }

    COMBINE_PLACEMENT_RESULTS(all_placements)
}

// Workflow completion handler
workflow.onComplete {
    log.info """
    ╔════════════════════════════════════════╗
    ║     Pipeline Execution Complete        ║
    ╠════════════════════════════════════════╣
    ║ Status:   ${workflow.success ? '✅ SUCCESS' : '❌ FAILED'}
    ║ Duration: ${workflow.duration}
    ║ Output:   ${params.output_dir}
    ╚════════════════════════════════════════╝
    """.stripIndent()
}

workflow.onError {
    log.error """
    ╔════════════════════════════════════════╗
    ║         Pipeline Error Occurred        ║
    ╠════════════════════════════════════════╣
    ║ Error:    ${workflow.errorMessage}
    ╚════════════════════════════════════════╝
    """.stripIndent()
}