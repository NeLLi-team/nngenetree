#!/usr/bin/env nextflow

/*
 * NNGeneTree - Nextflow Pipeline
 * ================================
 * Phylogenetic analysis and taxonomic classification of protein sequences
 *
 * Converted from Snakemake to Nextflow
 * Version: see manifest in nextflow.config
 */

nextflow.enable.dsl=2

// Import process modules
include { DIAMOND_BLASTP } from './modules/diamond_blastp'
include { PROCESS_BLAST_RESULTS } from './modules/process_blast'
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

// Validate required configuration: the DIAMOND database must exist
if (!params.blast_db || params.blast_db == 'null' || !file("${params.blast_db}.dmnd").exists()) {
    error """
    ╔══════════════════════════════════════════════════════════════════╗
    ║  ERROR: DIAMOND database not found: ${params.blast_db}.dmnd
    ║  Configure the database path using ONE of:                       ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  Option 1: Create conf/local.config (recommended)                ║
    ║    cp conf/local.config.template conf/local.config               ║
    ║    # Edit conf/local.config and set blast_db path                ║
    ║                                                                  ║
    ║  Option 2: Set environment variable                              ║
    ║    export NR_DATABASE=/path/to/nr                                ║
    ║                                                                  ║
    ║  Option 3: Command-line parameter                                ║
    ║    nngenetree <dir> local --blast_db /path/to/nr                 ║
    ╚══════════════════════════════════════════════════════════════════╝
    """.stripIndent()
}

// Print startup banner
log.info """
============================================
  NNGeneTree Pipeline (Nextflow)
============================================
  Version:  ${workflow.manifest.version}
  Input:    ${params.input_dir}
  Output:   ${params.output_dir}
  Database: ${params.blast_db}
============================================
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

    // Step 1: DIAMOND BLASTP search
    DIAMOND_BLASTP(input_fasta_ch)

    // Step 2: Process BLAST results to extract unique subjects
    PROCESS_BLAST_RESULTS(DIAMOND_BLASTP.out.blast_results)

    // Step 3: Gate on BLAST output - skip samples with fewer than 2 unique subjects
    blast_gate = PROCESS_BLAST_RESULTS.out.unique_subjects
        .branch {
            ok: it[1].countLines() >= 2
            skip: true
        }
    blast_gate.skip.subscribe { log.warn "Skipping ${it[0]}: fewer than 2 unique BLAST subjects" }
    unique_subjects_ch = blast_gate.ok

    // Step 4: Extract hit sequences from database
    EXTRACT_HITS(unique_subjects_ch)

    // Step 5: Combine query and hit sequences (with deduplication)
    COMBINE_SEQUENCES(
        input_fasta_ch
            .join(EXTRACT_HITS.out.extracted_hits)
    )

    // Step 6: Align sequences with MAFFT
    ALIGN_SEQUENCES(COMBINE_SEQUENCES.out.combined_sequences)

    // Step 7: Trim alignment with TrimAl
    TRIM_ALIGNMENT(ALIGN_SEQUENCES.out.aligned_sequences)

    // Step 8: Build phylogenetic tree with IQ-TREE
    BUILD_TREE(TRIM_ALIGNMENT.out.trimmed_alignment)

    // Step 9: Extract closest neighbors from tree
    EXTRACT_CLOSEST_NEIGHBORS(
        input_fasta_ch
            .join(unique_subjects_ch)
            .join(BUILD_TREE.out.tree)
    )

    // Step 10: Assign NCBI taxonomy to neighbors
    ASSIGN_TAXONOMY(
        EXTRACT_CLOSEST_NEIGHBORS.out.closest_neighbors
            .join(unique_subjects_ch)
    )

    // Step 11: Decorate tree with taxonomy and generate visualization
    DECORATE_TREE(
        BUILD_TREE.out.tree
            .join(ASSIGN_TAXONOMY.out.taxonomy)
            .join(input_fasta_ch)
    )

    // Step 12: Calculate tree statistics
    CALCULATE_TREE_STATS(
        BUILD_TREE.out.tree
            .join(ASSIGN_TAXONOMY.out.taxonomy)
            .join(input_fasta_ch)
    )

    // Step 13: Extract phylogenetic placement with taxonomy
    EXTRACT_PHYLOGENETIC_PLACEMENT(
        BUILD_TREE.out.tree
            .join(ASSIGN_TAXONOMY.out.taxonomy)
    )

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
    ============================================
      Pipeline Execution Complete
    ============================================
      Status:   ${workflow.success ? 'SUCCESS' : 'FAILED'}
      Duration: ${workflow.duration}
      Output:   ${params.output_dir}
    ============================================
    """.stripIndent()
}

workflow.onError {
    log.error """
    ============================================
      Pipeline Error Occurred
    ============================================
      Error: ${workflow.errorMessage}
    ============================================
    """.stripIndent()
}