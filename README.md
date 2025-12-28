# INGEST PHASE


## 🚀 Quick Start

### Single File

```bash
python3 ingest.py /path/to/sample.fastq
```

### Multiple Files

```bash
python3 ingest.py /path/to/sample1_R1.fastq /path/to/sample1_R2.fastq /path/to/sample2_R1.fastq /path/to/sample2_R2.fastq
```

### With Custom Output

```bash
python3 ingest.py -o ./my_results /path/to/sample.fastq
```

### Verbose Output

```bash
python3 ingest.py -v /path/to/sample.fastq
```

### Help

```bash
python3 ingest.py --help
```

---

## 📋 Command Reference

### Basic Syntax

```bash
python3 ingest.py [OPTIONS] SAMPLE_FILE [SAMPLE_FILE ...]
```

### Options

| Option | Short | Description |
| :--- | :--- | :--- |
| `--help` | `-h` | Show help message |
| `--output` | `-o` | Output directory (default: ./ingest_output) |
| `--dataset-id` | `-d` | Custom dataset ID |
| `--html` | - | HTML report filename |
| `--json` | - | JSON report filename |
| `--verbose` | `-v` | Verbose output |
| `--no-report` | - | Skip report generation |

---

## 💡 Real-World Examples

### Example 1: Single FASTQ

```bash
python3 ingest.py /data/sample1_R1.fastq.gz
```

**Output:**
```
======================================================================
INGEST Phase - Command Line Interface
======================================================================
Processing 1 file(s)...
[1/1] sample1_R1.fastq
  Dataset ID:        sample1_R1
  Sample Name:       sample1_R1
  Input Type:        FASTQ
  Format:            FASTQ (Paired-end)
  Validation Status: PASS
  File Size:         2.45 MB
  Total Reads:       150,000
  Sequence Length:   150 bp
  Paired-End:        True
  Message:           FASTQ validation successful

======================================================================
Generating Reports
======================================================================
✓ HTML Report: ./ingest_output/ingest_report.html
✓ JSON Report: ./ingest_output/ingest_report.json

======================================================================
SUMMARY
======================================================================
Total Processed:  1
PASS:             1
WARN:             0
FAIL:             0
✓ All files passed validation!
```

---

### Example 2: Paired-End FASTQ (Your 6 Samples)

```bash
python3 ingest.py \
  /data/sample1_R1.fastq.gz \
  /data/sample1_R2.fastq.gz \
  /data/sample2_R1.fastq.gz \
  /data/sample2_R2.fastq.gz \
  /data/sample3_R1.fastq.gz \
  /data/sample3_R2.fastq.gz \
  -o ./results \
  -v
```

**Output:**
```
Processing 6 file(s)...

[1/6] sample1_R1.fastq
  Input Type:        FASTQ
  Validation Status: PASS
  File Size:         2.45 MB
  Total Reads:       150,000
  Paired-End:        True

[2/6] sample1_R2.fastq
  Input Type:        FASTQ
  Validation Status: PASS
  File Size:         2.48 MB
  Total Reads:       150,000
  Paired-End:        True

[3/6] sample2_R1.fastq
  Input Type:        FASTQ
  Validation Status: PASS
  File Size:         2.42 MB
  Total Reads:       148,000
  Paired-End:        True

[4/6] sample2_R2.fastq
  Input Type:        FASTQ
  Validation Status: PASS
  File Size:         2.45 MB
  Total Reads:       148,000
  Paired-End:        True

[5/6] sample3_R1.fastq
  Input Type:        FASTQ
  Validation Status: PASS
  File Size:         2.50 MB
  Total Reads:       152,000
  Paired-End:        True

[6/6] sample3_R2.fastq
  Input Type:        FASTQ
  Validation Status: PASS
  File Size:         2.52 MB
  Total Reads:       152,000
  Paired-End:        True

======================================================================
SUMMARY
======================================================================
Total Processed:  6
PASS:             6
WARN:             0
FAIL:             0
✓ All files passed validation!
```

---

### Example 3: Count Matrix

```bash
python3 ingest.py /data/expression_matrix.tsv -v
```

**Output:**
```
[1/1] expression_matrix.tsv
  Input Type:        MATRIX
  Format:            Count Matrix (Processed Expression Data)
  Validation Status: PASS
  File Size:         125.5 MB
  Total Genes:       20,000
  Samples:           6
  Message:           Count matrix validation successful
```

---

### Example 4: Multiple File Types

```bash
python3 ingest.py \
  /data/sample1_R1.fastq.gz \
  /data/sample1_R2.fastq.gz \
  /data/expression_matrix.tsv \
  /data/microarray_data.tsv \
  -o ./results \
  --html my_report.html \
  --json my_data.json
```

---

### Example 5: All FASTQ Files in Directory

```bash
python3 ingest.py /data/samples/*.fastq.gz -o ./results
```

---

### Example 6: Custom Dataset ID

```bash
python3 ingest.py -d my_experiment /path/to/sample.fastq
```

---

### Example 7: Skip Reports

```bash
python3 ingest.py --no-report /path/to/sample.fastq
```

---

## 📊 File Size Display

All reports show file sizes in human-readable format:

```
File Size: 2.45 MB (2,568,192 bytes)
```

Automatically converts to:
- **Bytes** - For files < 1 KB
- **KB** - For files 1 KB - 1 MB
- **MB** - For files 1 MB - 1 GB
- **GB** - For files > 1 GB

---

## 🔍 Validation Features

### FASTQ Validation
- ✅ Header starts with `@`
- ✅ Plus line starts with `+`
- ✅ Valid nucleotides (ACGTN)
- ✅ Quality scores ASCII 33-126
- ✅ Sequence/quality length match

### BAM Validation
- ✅ Magic bytes: `BAM\x01`
- ✅ Binary format integrity
- ✅ Read count (via samtools)
- ✅ Paired-end detection

### CELL Validation
- ✅ Contains `probe_id` column
- ✅ Contains `intensity` column
- ✅ Valid probe ID format
- ✅ Numeric intensity values

### Count Matrix Validation
- ✅ Header row with gene_id + samples
- ✅ Gene IDs not empty
- ✅ All counts numeric
- ✅ All counts non-negative
- ✅ Consistent columns

---

## 📈 HTML Report

The generated HTML report includes:

✅ **Summary Statistics**
- Total files processed
- PASS/WARN/FAIL counts

✅ **Detailed Table**
- Sample name
- Input type
- File size (in MB/KB)
- Read/row count
- Validation status
- Detailed message

✅ **Professional Design**
- Color-coded status
- Responsive layout
- Print-friendly

---

## 📄 JSON Report

Machine-readable format for integration:

```json
{
  "timestamp": "2025-12-28T14:30:00.000000",
  "total_files": 2,
  "results": [
    {
      "dataset_id": "sample1_R1",
      "input_type": "FASTQ",
      "file_path": "/data/sample1_R1.fastq.gz",
      "file_size": 2568192,
      "file_size_mb": 2.45,
      "validation_status": "PASS",
      "validation_message": "FASTQ validation successful",
      "total_reads": 150000,
      "sequence_length": 150,
      "is_paired_end": true,
      "detected_format": "FASTQ (Paired-end)"
    }
  ]
}
```

---

## 🎯 Validation Status Codes

| Status | Meaning | Action |
| :--- | :--- | :--- |
| **PASS** | File is valid and ready | Proceed to next phase |
| **WARN** | File is usable but has minor issues | Review and proceed with caution |
| **FAIL** | File has critical errors | Fix file before proceeding |

---

## 🐛 Troubleshooting

### File Not Found

```bash
# Check if file exists
ls -la /path/to/file.fastq

# Use absolute path
python3 ingest.py /absolute/path/to/file.fastq
```

### Invalid FASTQ

```bash
# Check first line
head -1 /path/to/file.fastq

# Should start with @
```

### Invalid BAM

```bash
# Check magic bytes
hexdump -C /path/to/file.bam | head -1

# Should show: 42 41 4d 01
```

### samtools Not Found

```bash
# Install samtools
apt-get install samtools    # Linux
brew install samtools       # Mac
conda install samtools      # Conda
```

---

## 📁 Directory Structure

```
project/
├── ingest.py                    ← Single unified script
├── ingest_test_data/            ← Test data
│   ├── sample_R1.fastq
│   ├── sample_R2.fastq
│   ├── count_matrix.tsv
│   └── cell_data.tsv
├── ingest_output/               ← Reports (auto-created)
│   ├── ingest_report.html
│   └── ingest_report.json
└── results/                     ← Custom output (optional)
    ├── my_report.html
    └── my_data.json
```

---

## ✅ Best Practices

1. **Always validate before analysis**
   ```bash
   python3 ingest.py /path/to/samples/*.fastq.gz
   ```

2. **Check HTML report for details**
   - Open in web browser
   - Review any WARN status
   - Fix FAIL status files

3. **Keep validation logs**
   ```bash
   python3 ingest.py /path/to/file.fastq > validation.log 2>&1
   ```

4. **Batch validate multiple samples**
   ```bash
   python3 ingest.py -o ./results /data/batch1/*.fastq.gz
   ```

5. **Use verbose mode for debugging**
   ```bash
   python3 ingest.py -v /path/to/file.fastq
   ```

---

## 🚀 Integration Examples

### Python Script

```python
from ingest import IngestPhase

ingest = IngestPhase(output_dir="./results")

# Process single file
result = ingest.ingest("/path/to/sample.fastq")
print(f"Status: {result.validation_status}")
print(f"File Size: {result.file_size_mb:.2f} MB")
print(f"Reads: {result.total_reads:,}")

# Generate reports
ingest.generate_html_report("report.html")
ingest.generate_report("report.json")
```


---


