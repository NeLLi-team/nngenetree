# nngenetree
* Recruit best blastp hits vs nr of query sequences, build genetrees, infer nearest neighbors and tree stats

## How to run it
* Set path to blast nr dir that contains ncbi formatted blast db and also diamond formatted nr.dmnd
* Activate conda env with snakemake
```
snakemake --use-conda -j 16 --config input_dir=<dir with faa file(s)>
```
* Adjust config file to change n blastp hits
