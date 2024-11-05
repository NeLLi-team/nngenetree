import sys
from ete3 import Tree
import pandas as pd
import numpy as np

def get_taxonomy_category(taxonomy):
  main_category = taxonomy.split(';')[0]
  if main_category in ["Bacteria", "Viruses", "Eukaryota", "Archaea"]:
      return main_category
  return "Other"

def calculate_tree_stats(tree_file, taxonomy_file, query_file, output_file):
  # Load the tree
  tree = Tree(tree_file)

  # Load taxonomy assignments
  taxonomy_dict = {}
  with open(taxonomy_file, 'r') as f:
      for line in f:
          parts = line.strip().split('\t')
          if len(parts) == 2:
              taxonomy_dict[parts[0]] = parts[1]

  # Load query sequences
  queries = set()
  with open(query_file, 'r') as f:
      for line in f:
          if line.startswith('>'):
              queries.add(line[1:].split()[0])

  results = []

  for query in queries:
      query_node = tree.search_nodes(name=query)[0]
         
      # 1. Nearest query neighbor
      other_queries = [node for node in tree.iter_leaves() if node.name in queries and node.name != query]
      other_queries.sort(key=lambda n: query_node.get_distance(n))
      nearest_query = other_queries[0]
      nearest_query_distance = query_node.get_distance(nearest_query)

      # Mean distance to 3 closest queries
      mean_distance_3_closest_queries = np.mean([query_node.get_distance(n) for n in other_queries[:3]])
      std_distance_3_closest_queries = np.std([query_node.get_distance(n) for n in other_queries[:3]])

      # Average distance to all other queries
      avg_distance_all_queries = np.mean([query_node.get_distance(n) for n in other_queries])

      # 2. Nearest subject neighbor for each category
      category_neighbors = {cat: {'distance': float('inf'), 'taxonomy': ''} for cat in ['Bacteria', 'Archaea', 'Eukaryota', 'Viruses']}
      
      for node in tree.iter_leaves():
          if node.name in taxonomy_dict:
              category = get_taxonomy_category(taxonomy_dict[node.name])
              if category in category_neighbors:
                  distance = query_node.get_distance(node)
                  if distance < category_neighbors[category]['distance']:
                      category_neighbors[category]['distance'] = distance
                      category_neighbors[category]['taxonomy'] = taxonomy_dict[node.name]

      # 3. Mean and std dev of distances to each category
      category_distances = {cat: [] for cat in ['Bacteria', 'Archaea', 'Eukaryota', 'Viruses']}
      
      for node in tree.iter_leaves():
          if node.name in taxonomy_dict:
              category = get_taxonomy_category(taxonomy_dict[node.name])
              if category in category_distances:
                  category_distances[category].append(query_node.get_distance(node))

      category_stats = {cat: {'mean': np.mean(distances) if distances else 'na',
                              'std': np.std(distances) if distances else 'na'}
                        for cat, distances in category_distances.items()}

      # 4. Mean distances to 3 closest Bacteria, Archaea, Eukaryota, Viruses
      category_3_closest = {cat: {'mean': 'na', 'std': 'na'} for cat in ['Bacteria', 'Archaea', 'Eukaryota', 'Viruses']}
      for cat, distances in category_distances.items():
          if len(distances) >= 3:
              closest_3 = sorted(distances)[:3]
              category_3_closest[cat]['mean'] = np.mean(closest_3)
              category_3_closest[cat]['std'] = np.std(closest_3)

      results.append({
          'query': query,
          'nearest_query': nearest_query.name,
          'nearest_query_distance': nearest_query_distance,
          'mean_distance_3_closest_queries': mean_distance_3_closest_queries,
          'std_distance_3_closest_queries': std_distance_3_closest_queries,
          'avg_distance_all_queries': avg_distance_all_queries,
          **{f'nearest_{cat}_distance': info['distance'] for cat, info in category_neighbors.items()},
          **{f'nearest_{cat}_taxonomy': info['taxonomy'] for cat, info in category_neighbors.items()},
          **{f'{cat}_mean_distance': category_stats[cat]['mean'] for cat in category_stats},
          **{f'{cat}_std_distance': category_stats[cat]['std'] for cat in category_stats},
          **{f'{cat}_mean_distance_3_closest': category_3_closest[cat]['mean'] for cat in category_3_closest},
          **{f'{cat}_std_distance_3_closest': category_3_closest[cat]['std'] for cat in category_3_closest}
      })

  # Create DataFrame and save to file
  df = pd.DataFrame(results)
  df.to_csv(output_file, sep='\t', index=False)

if __name__ == "__main__":
  if len(sys.argv) != 5:
      print("Usage: python tree_stats.py <tree_file> <taxonomy_file> <query_file> <output_file>")
      sys.exit(1)

  tree_file = sys.argv[1]
  taxonomy_file = sys.argv[2]
  query_file = sys.argv[3]
  output_file = sys.argv[4]

  calculate_tree_stats(tree_file, taxonomy_file, query_file, output_file)
