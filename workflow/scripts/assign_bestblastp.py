import typer
from Bio import Entrez
import os
from tqdm import tqdm

app = typer.Typer()

Entrez.email = 'fschulz@lbl.gov'

# Function to fetch taxonomy information for a given accession number
def fetch_taxonomy(accession: str) -> str:
  try:
      handle = Entrez.efetch(db='protein', id=accession, rettype='gb', retmode='xml')
      record = Entrez.read(handle)
      taxonomy = record[0]['GBSeq_taxonomy']
      handle.close()  # Ensure the handle is properly closed after use
      return taxonomy
  except Exception as e:
      return f"Error: {str(e)}"

@app.command()
def main(
  input: str = typer.Option(..., "--input", "-i", help="Input file path containing list of IDs."),
  output: str = typer.Option(..., "--output", "-o", help="Output file path.")
):
  try:
      # Read unique accession numbers from the input file
      with open(input, 'r') as infile:
          unique_accessions = set(line.strip() for line in infile if line.strip())

      total_ids = len(unique_accessions)
      typer.echo(f"Number of unique subject IDs: {total_ids}")

      # Fetch taxonomy for unique accessions
      taxonomy_dict = {}
      typer.echo("Fetching taxonomy information from NCBI...")
      for accession in tqdm(unique_accessions, total=total_ids, desc="Progress"):
          taxonomy = fetch_taxonomy(accession)
          taxonomy_dict[accession] = taxonomy

      # Write output file with taxonomy information
      typer.echo("Writing output file...")
      with open(output, 'w') as outfile:
          for accession in unique_accessions:
              taxonomy = taxonomy_dict.get(accession, "Error: Taxonomy not found")
              outfile.write(f"{accession}\t{taxonomy.replace('; ', ';')}\n")

  except Exception as e:
      typer.echo(f"Failed to process file: {str(e)}")
      raise typer.Exit(code=1)

  typer.echo(f"Results saved to {output}")

if __name__ == "__main__":
  app()
