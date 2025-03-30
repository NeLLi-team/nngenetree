import sys
import traceback
from ete3 import Tree, TreeStyle, NodeStyle, CircleFace
import colorsys
import os
import random
import hashlib
import re
import csv

# Set the QT_QPA_PLATFORM environment variable to 'offscreen'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def get_taxonomy_level(taxonomy, level):
    """Extract the taxonomy at the specified level."""
    if not taxonomy or taxonomy == 'Unknown' or ';' not in taxonomy:
        return 'Unknown'
    
    parts = taxonomy.split(';')
    level_index = {
        'domain': 0,
        'phylum': 1,
        'class': 2,
        'order': 3,
        'family': 4,
        'genus': 5,
        'species': 6
    }
    
    idx = level_index.get(level.lower(), 0)
    
    if idx < len(parts):
        return parts[idx]
    return 'Unknown'

def generate_color_palette(categories):
    """Generate a color palette for the given categories."""
    colors = {}
    
    # Predefined colors for common domains
    predefined = {
        'Bacteria': '#FF0000',  # Red
        'Archaea': '#FFCC00',   # Yellow
        'Eukaryota': '#0000FF', # Blue
        'Viruses': '#00CC00',   # Green
        'Unknown': '#808080'    # Gray
    }
    
    # Use predefined colors for common categories
    for cat in categories:
        if cat in predefined:
            colors[cat] = predefined[cat]
    
    # Generate colors for remaining categories
    remaining = [cat for cat in categories if cat not in colors]
    
    if remaining:
        # Generate evenly spaced colors in HSV space
        for i, cat in enumerate(remaining):
            hue = i / float(len(remaining))
            r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 0.9)
            # Convert to hex
            hex_color = '#{:02X}{:02X}{:02X}'.format(int(r*255), int(g*255), int(b*255))
            colors[cat] = hex_color
    
    return colors

def get_color_hash(text):
    """Generate a consistent color based on text hash."""
    # Get stable hash value
    hash_object = hashlib.md5(text.encode())
    hash_hex = hash_object.hexdigest()
    
    # Convert first 6 hex chars to RGB
    r = int(hash_hex[0:2], 16) / 255.0
    g = int(hash_hex[2:4], 16) / 255.0
    b = int(hash_hex[4:6], 16) / 255.0
    
    # Ensure color is vibrant enough
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = max(0.7, s)  # Increase saturation if too low
    v = max(0.7, v)  # Increase value if too low
    
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    
    # Convert back to hex
    return '#{:02X}{:02X}{:02X}'.format(int(r*255), int(g*255), int(b*255))

def get_accession_variations(node_name):
    """
    Generate different variations of the accession ID from a node name.
    
    Args:
        node_name (str): The original node name from the tree
        
    Returns:
        list: List of possible accession variations to try
    """
    variations = [node_name]  # Original name
    
    # For names with pipe symbols (e.g., "IMGM3300034524_BIN255|Ga0310146_00006_20")
    if '|' in node_name:
        parts = node_name.split('|')
        variations.append(parts[0])  # Before pipe
        variations.append(parts[-1])  # After pipe
        
    # For names with multiple dots (e.g., "MBP8793264.1")
    if '.' in node_name and re.match(r'[A-Z]+\d+\.\d+', node_name):
        base = node_name.split('.')[0]
        variations.append(base)  # Base without version
        
    # Try extracting standard accession patterns
    accession_patterns = [
        r'([A-Z]+_\d+\.\d+)',      # GenBank: ABC_123456.1
        r'([A-Z]{1,5}\d{5,8})',    # RefSeq: WP_123456789
        r'([A-Z]{1,5}\d{5,8}\.\d+)' # Versioned: WP_123456789.1
    ]
    
    for pattern in accession_patterns:
        match = re.search(pattern, node_name)
        if match:
            variations.append(match.group(1))
    
    return list(set(variations))  # Remove duplicates

def clean_csv_field(field):
    """Clean a CSV field by removing extra commas and dealing with malformed data."""
    return field.strip()

def parse_csv_taxonomy_file(csv_file):
    """
    Parse the CSV file with taxonomy information, handling malformed data.
    
    Args:
        csv_file (str): Path to the CSV file
        
    Returns:
        dict: Mapping from queries/subjects to taxonomy
    """
    taxonomy_dict = {}
    
    try:
        with open(csv_file, 'r') as f:
            content = f.read()
            
            # Split by lines and process manually
            lines = content.strip().split('\n')
            if not lines:
                return taxonomy_dict
            
            # Skip header
            for i in range(1, len(lines)):
                line = lines[i]
                
                # Find the last occurrence of a numeric substring followed by comma and taxonomy
                taxonomy_match = re.search(r'(\d+\.\d+),([^,]+;[^,]+.*)$', line)
                if taxonomy_match:
                    taxonomy = taxonomy_match.group(2)
                    
                    # Extract the query and subject from the beginning of the line
                    parts = line.split(',')
                    if len(parts) >= 2:
                        query = parts[0].strip()
                        subject = parts[1].strip()
                        
                        # Add both query and subject with taxonomy
                        taxonomy_dict[query] = taxonomy
                        taxonomy_dict[subject] = taxonomy
                        
                        print(f"Added mapping: {query} -> {taxonomy}", file=sys.stderr)
                        print(f"Added mapping: {subject} -> {taxonomy}", file=sys.stderr)
                        
                        # Add variations for better matching
                        for name in [query, subject]:
                            for variation in get_accession_variations(name):
                                if variation != name and variation not in taxonomy_dict:
                                    taxonomy_dict[variation] = taxonomy
    except Exception as e:
        print(f"Error parsing CSV taxonomy file: {str(e)}", file=sys.stderr)
    
    return taxonomy_dict

def decorate_tree(tree_file, taxonomy_file, query_file, tree_output_prefix, itol_output_prefix, tax_level='domain'):
    try:
        # Read taxonomy assignments (full taxonomy strings) from the taxonomy.txt file
        taxonomy_dict = {}
        with open(taxonomy_file, 'r') as f:
            # Skip header
            header = next(f, None)
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    # Format: OG, accession, taxonomy
                    accession = parts[1]
                    full_taxonomy = parts[2]
                    taxonomy_dict[accession] = full_taxonomy
                    
                    # Also add variations of the accession ID
                    for variation in get_accession_variations(accession):
                        if variation != accession:
                            taxonomy_dict[variation] = full_taxonomy
                    
                    print(f"Loaded taxonomy for {accession}: {full_taxonomy}", file=sys.stderr)

        print(f"Loaded {len(taxonomy_dict)} taxonomy assignments from taxonomy file", file=sys.stderr)

        # Read taxonomy from CSV file for additional lookup
        csv_file = os.path.dirname(taxonomy_file) + "/closest_neighbors_with_taxonomy.csv"
        if os.path.exists(csv_file):
            csv_taxonomy_dict = parse_csv_taxonomy_file(csv_file)
            print(f"Loaded {len(csv_taxonomy_dict)} taxonomy entries from CSV", file=sys.stderr)
            
            # Merge the dictionaries, with CSV taking precedence
            taxonomy_dict.update(csv_taxonomy_dict)

        # Read query sequences
        queries = set()
        with open(query_file, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    queries.add(line[1:].split()[0])

        print(f"Loaded {len(queries)} query sequences", file=sys.stderr)

        # Load tree
        tree = Tree(tree_file)
        print(f"Loaded tree with {len(tree)} leaves", file=sys.stderr)
        
        # Print first few leaf names to check what format they're in
        print("Sample leaf names:", file=sys.stderr)
        for leaf in list(tree.iter_leaves())[:5]:
            print(f" - {leaf.name}", file=sys.stderr)
            
            # For each leaf, try to find a matching taxonomy
            variations = get_accession_variations(leaf.name)
            for variation in variations:
                if variation in taxonomy_dict:
                    print(f"   Match found: {variation} -> {taxonomy_dict[variation]}", file=sys.stderr)

        # Extract taxonomy categories at the specified level
        categories = {}
        for node_name, full_taxonomy in taxonomy_dict.items():
            tax_category = get_taxonomy_level(full_taxonomy, tax_level)
            categories[node_name] = tax_category
        
        # Generate colors for unique taxonomy categories
        unique_categories = set(categories.values()) | {'Unknown'}
        color_map = generate_color_palette(unique_categories)

        # Create a node_to_taxonomy mapping
        node_to_taxonomy = {}
        
        # Decorate tree
        for node in tree.traverse():
            if node.is_leaf():
                # Try to find taxonomy for this node using different variations of the name
                taxonomy = 'Unknown'
                variations = get_accession_variations(node.name)
                
                # Try each variation against the taxonomy dictionary
                for variation in variations:
                    if variation in taxonomy_dict:
                        taxonomy = taxonomy_dict[variation]
                        print(f"Found taxonomy for {node.name} using variation {variation}", file=sys.stderr)
                        break
                
                # Store in our mapping
                node_to_taxonomy[node.name] = taxonomy
                
                # Get taxonomy category
                category = get_taxonomy_level(taxonomy, tax_level) if taxonomy != 'Unknown' else 'Unknown'
                node.add_features(category=category, full_taxonomy=taxonomy)
                
                nstyle = NodeStyle()
                nstyle["fgcolor"] = color_map.get(category, "#808080")
                nstyle["size"] = 0
                
                if node.name in queries:
                    circle_face = CircleFace(radius=5, color="red", style="sphere")
                    node.add_face(circle_face, column=0, position="aligned")
                
                node.set_style(nstyle)

        # Color internal nodes
        for node in tree.traverse(strategy="postorder"):
            if not node.is_leaf():
                child_categories = [child.category for child in node.children]
                if len(set(child_categories)) == 1:
                    node.add_features(category=child_categories[0], full_taxonomy='')
                else:
                    node.add_features(category='Mixed', full_taxonomy='')
                
                nstyle = NodeStyle()
                nstyle["fgcolor"] = color_map.get(node.category, "#808080")
                nstyle["size"] = 0
                node.set_style(nstyle)

        # Set tree style
        ts = TreeStyle()
        ts.show_leaf_name = True
        ts.branch_vertical_margin = 10
        ts.scale = 1000

        # Save decorated tree
        tree.render(tree_output_prefix, tree_style=ts, dpi=300, w=1000, units="px")
        print(f"Saved decorated tree to {tree_output_prefix}", file=sys.stderr)

        # Create iTOL files
        create_itol_files(tree, node_to_taxonomy, queries, itol_output_prefix, color_map, tax_level)
        print(f"{itol_output_prefix}", file=sys.stderr)
        print("Created iTOL files", file=sys.stderr)

    except Exception as e:
        print(f"An error occurred in decorate_tree: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise

def create_itol_files(tree, taxonomy_dict, queries, output_prefix, color_map, tax_level):
    try:
        output_dir = output_prefix
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Labels file - use full taxonomy
        with open(os.path.join(output_dir, 'itol_labels.txt'), 'w') as f:
            f.write("LABELS\nSEPARATOR TAB\nDATA\n")
            for leaf in tree.iter_leaves():
                # Get the full taxonomy from node attributes or our dictionary
                taxonomy = getattr(leaf, 'full_taxonomy', taxonomy_dict.get(leaf.name, 'Unknown'))
                
                # If taxonomy is still Unknown, try variations of the name
                if taxonomy == 'Unknown':
                    variations = get_accession_variations(leaf.name)
                    for variation in variations:
                        if variation in taxonomy_dict and taxonomy_dict[variation] != 'Unknown':
                            taxonomy = taxonomy_dict[variation]
                            break
                
                f.write(f"{leaf.name}\t{taxonomy}\n")

        # Branch colors file
        with open(os.path.join(output_dir, 'itol_branch_colors.txt'), 'w') as f:
            f.write("TREE_COLORS\nSEPARATOR TAB\nDATA\n")
            for node in tree.traverse():
                if not node.is_root():
                    if hasattr(node, 'category'):
                        color = color_map.get(node.category, "#808080")
                        f.write(f"{node.name}\tbranch\t{color}\tnormal\t1\n")

        # Circles for queries file
        with open(os.path.join(output_dir, 'itol_query_circles.txt'), 'w') as f:
            f.write("DATASET_SYMBOL\n")
            f.write("SEPARATOR TAB\n")
            f.write("DATASET_LABEL\tQuery sequences\n")
            f.write("COLOR\t#FF0000\n")
            f.write("MAX_SIZE\t10\n")
            f.write("SHOW_INTERNAL\t0\n")
            f.write("DATA\n")
            for leaf in tree.iter_leaves():
                if leaf.name in queries:
                    f.write(f"{leaf.name}\t1\t#FF0000\n")

        # Create taxonomy color strip
        with open(os.path.join(output_dir, 'itol_colorstrip.txt'), 'w') as f:
            f.write("DATASET_COLORSTRIP\n")
            f.write("SEPARATOR TAB\n")
            f.write(f"DATASET_LABEL\tTaxonomy ({tax_level})\n")
            f.write("COLOR\t#000000\n")
            f.write("COLOR_BRANCHES\t1\n")
            
            # Add legend
            f.write("LEGEND_TITLE\tTaxonomy Legend\n")
            f.write("LEGEND_SHAPES\t1\n")
            f.write("LEGEND_COLORS\t")
            f.write("\t".join(color_map.values()))
            f.write("\n")
            f.write("LEGEND_LABELS\t")
            f.write("\t".join(color_map.keys()))
            f.write("\n")
            
            # Add data
            f.write("DATA\n")
            for leaf in tree.iter_leaves():
                if hasattr(leaf, 'category'):
                    color = color_map.get(leaf.category, "#808080")
                    f.write(f"{leaf.name}\t{color}\t{leaf.category}\n")

    except Exception as e:
        print(f"An error occurred in create_itol_files: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python decorate_tree.py <tree_file> <taxonomy_file> <query_file> <tree_output_prefix> <itol_output_prefix> [tax_level]", file=sys.stderr)
        sys.exit(1)

    tree_file = sys.argv[1]
    taxonomy_file = sys.argv[2]
    query_file = sys.argv[3]
    tree_output_prefix = sys.argv[4]
    itol_output_prefix = sys.argv[5]
    tax_level = sys.argv[6] if len(sys.argv) > 6 else 'domain'

    try:
        decorate_tree(tree_file, taxonomy_file, query_file, tree_output_prefix, itol_output_prefix, tax_level)
    except Exception as e:
        print(f"An error occurred in main: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
