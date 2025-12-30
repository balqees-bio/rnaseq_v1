# Test Data Files

This directory contains example files for testing the INGEST phase.

## Files

- **sample_R1.fastq** - Paired-end FASTQ file (read 1)
- **sample_R2.fastq** - Paired-end FASTQ file (read 2)
- **count_matrix.tsv** - Expression count matrix (10 genes × 6 samples)
- **cell_data.tsv** - Microarray intensity data (10 probes × 6 samples)

## File Formats

### FASTQ Files
- Standard Illumina FASTQ format
- 5 reads per file
- 50 bp read length
- Quality scores in Phred+33 format

### Count Matrix
- Tab-separated values
- Gene IDs in first column
- Sample names in header
- Integer count values

### CELL Data
- Tab-separated values
- Probe IDs and gene symbols
- Intensity values for multiple samples
- Numeric data only

## Usage

These files are used by `ingest_examples.py` for testing. They can also be used as templates for your own data.

---

**All test files are synthetic and created for demonstration purposes.**
