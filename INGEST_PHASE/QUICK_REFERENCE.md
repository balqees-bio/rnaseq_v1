# INGEST Phase - Quick Reference

## Running the Examples

```bash
python3 ingest_examples.py
```

This runs 6 comprehensive test cases covering all supported input types.

## Using in Your Code

### Basic Usage

```python
from ingest_phase import IngestPhase

ingest = IngestPhase()
result = ingest.ingest("your_file.fastq")
print(result.validation_status)  # PASS, WARN, or FAIL
```

### Batch Processing

```python
ingest = IngestPhase(output_dir="./results")

files = ["file1.fastq", "file2.fastq", "matrix.tsv"]
for file in files:
    result = ingest.ingest(file)
    print(f"{file}: {result.validation_status}")

# Generate reports
ingest.generate_html_report("report.html")
ingest.generate_report("report.json")
```

### Accessing Results

```python
result = ingest.ingest("file.fastq")

# Available attributes
result.dataset_id           # Unique ID
result.sample_name          # Sample name
result.input_type           # FASTQ, BAM, CELL, MATRIX
result.validation_status    # PASS, WARN, FAIL
result.validation_message   # Detailed message
result.file_size            # File size in bytes
result.total_reads          # Number of reads/rows
result.sequence_length      # Read length or column count
result.is_paired_end        # For FASTQ files
result.detected_format      # Detailed format info
```

## Input Type Detection

The script automatically detects:

| Extension | Type | Detection Method |
| :--- | :--- | :--- |
| .fastq, .fq, .fastq.gz | FASTQ | File extension |
| .bam | BAM | File extension + magic number |
| .tsv, .csv, .txt | CELL or MATRIX | Content analysis |

## Validation Status Meanings

- **PASS** - File is valid and ready for downstream analysis
- **WARN** - File is likely usable but has minor issues
- **FAIL** - File has critical errors and needs correction

## Output Files

After running `ingest_examples.py`:

```
output/
├── ingest_report.html    # Professional HTML report
└── ingest_report.json    # Machine-readable JSON
```

## Common Issues & Solutions

### Issue: "samtools not found"
**Solution**: Install samtools for full BAM validation
```bash
apt-get install samtools  # Linux
brew install samtools     # macOS
```

### Issue: "Unknown file format"
**Solution**: Ensure file extension is correct or use content-based detection

### Issue: "Sequence length != Quality length"
**Solution**: FASTQ file is corrupted. Verify with `gunzip -t file.fastq.gz`

---

**For full documentation, see docs/INGEST_GUIDE.md**
