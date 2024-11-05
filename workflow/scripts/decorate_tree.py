import sys
import traceback
from ete3 import Tree, TreeStyle, NodeStyle, CircleFace
import colorsys
import os

# Set the QT_QPA_PLATFORM environment variable to 'offscreen'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def get_color(category):
  colors = {
      "Bacteria": "#FF0000",
      "Viruses": "#00FF00",
      "Eukaryota": "#0000FF",
      "Archaea": "#FFFF00",
      "Other": "#808080"
  }
  return colors.get(category, "#808080")

def get_taxonomy_category(taxonomy):
  main_category = taxonomy.split(';')[0]
  if main_category in ["Bacteria", "Viruses", "Eukaryota", "Archaea"]:
      return main_category
  return "Other"

def decorate_tree(tree_file, taxonomy_file, query_file, tree_output_prefix, itol_output_prefix):
  try:
      # Read taxonomy assignments
      taxonomy_dict = {}
      with open(taxonomy_file, 'r') as f:
          for line in f:
              parts = line.strip().split('\t')
              if len(parts) == 2:
                  taxonomy_dict[parts[0]] = get_taxonomy_category(parts[1])

      print(f"Loaded {len(taxonomy_dict)} taxonomy assignments", file=sys.stderr)

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

      # Decorate tree
      for node in tree.traverse():
          if node.is_leaf():
              category = taxonomy_dict.get(node.name, "Other")
              node.add_features(category=category)
              
              nstyle = NodeStyle()
              nstyle["fgcolor"] = get_color(category)
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
                  node.add_features(category=child_categories[0])
              else:
                  node.add_features(category="Other")
              
              nstyle = NodeStyle()
              nstyle["fgcolor"] = get_color(node.category)
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
      create_itol_files(tree, taxonomy_dict, queries, itol_output_prefix)
      print("Created iTOL files", file=sys.stderr)

  except Exception as e:
      print(f"An error occurred in decorate_tree: {str(e)}", file=sys.stderr)
      print(traceback.format_exc(), file=sys.stderr)
      raise

def create_itol_files(tree, taxonomy_dict, queries, output_prefix):
  try:
      output_dir = output_prefix
      print(f"{output_prefix}")
      if not os.path.exists(output_dir):
          os.makedirs(output_dir)
      # Labels file
      with open(os.path.join(output_dir, 'itol_labels.txt'), 'w') as f:
          f.write("LABELS\nSEPARATOR TAB\nDATA\n")
          for leaf in tree.iter_leaves():
              category = taxonomy_dict.get(leaf.name, "Other")
              f.write(f"{leaf.name}\t{category}\n")

      # Branch colors file
      with open(os.path.join(output_dir, 'itol_branch_colors.txt'), 'w') as f:
          f.write("TREE_COLORS\nSEPARATOR TAB\nDATA\n")
          for node in tree.traverse():
              if not node.is_root():
                  color = get_color(node.category)
                  f.write(f"{node.name}\tbranch\t{color}\tnormal\t1\n")

      # Circles for queries file
      with open(os.path.join(output_dir, 'itol_query_circles.txt'), 'w') as f:
          f.write("DATASET_SYMBOL\nSEPARATOR TAB\nDATASET_LABEL\tQuery sequences\nCOLOR\t#FF0000\nMAX_SIZE\t10\nSHOW_INTERNAL\t0\nDATA\n")
          for leaf in tree.iter_leaves():
              if leaf.name in queries:
                  f.write(f"{leaf.name}\t1\t#FF0000\n")

  except Exception as e:
      print(f"An error occurred in create_itol_files: {str(e)}", file=sys.stderr)
      print(traceback.format_exc(), file=sys.stderr)
      raise

if __name__ == "__main__":
  if len(sys.argv) != 6:
      print("Usage: python decorate_tree.py <tree_file> <taxonomy_file> <query_file> <tree_output_prefix> <itol_output_prefix>", file=sys.stderr)
      sys.exit(1)

  tree_file = sys.argv[1]
  taxonomy_file = sys.argv[2]
  query_file = sys.argv[3]
  tree_output_prefix = sys.argv[4]
  itol_output_prefix = sys.argv[5]

  try:
      decorate_tree(tree_file, taxonomy_file, query_file, tree_output_prefix, itol_output_prefix)
  except Exception as e:
      print(f"An error occurred in main: {str(e)}", file=sys.stderr)
      print(traceback.format_exc(), file=sys.stderr)
      sys.exit(1)
