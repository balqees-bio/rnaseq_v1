# INGEST Phase - RNA-seq Pipeline

Production-ready input detection, validation, and parsing for multiple data types.

## Quick Start

1. **Run the examples**:
   ```bash
   python3 ingest_examples.py
   ```

2. **View the results**:
   - Console output shows detailed validation results
   - `output/ingest_report.html` - Professional HTML report
   - `output/ingest_report.json` - Machine-readable JSON report

## Files Included

- **ingest_phase.py** - Main INGEST phase script (production-ready)
- **ingest_examples.py** - Comprehensive example usage and test cases
- **docs/INGEST_GUIDE.md** - Detailed documentation
- **test_data/** - Example files for all supported formats:
  - sample_R1.fastq, sample_R2.fastq (paired-end FASTQ)
  - count_matrix.tsv (processed expression data)
  - cell_data.tsv (microarray data)

## Supported Input Types

- **FASTQ** - Raw sequencing data (paired-end and single-end)
- **BAM** - Aligned reads (requires samtools for full validation)
- **CELL** - Microarray data
- **MATRIX** - Processed count matrices

## Key Features

✓ Automatic input type detection
✓ Comprehensive validation with PASS/WARN/FAIL status
✓ Detailed HTML and JSON reports
✓ Paired-end detection
✓ Standalone and pipeline-integrable
✓ Production-ready code with error handling

## Usage Example

```python
from ingest_phase import IngestPhase

# Create instance
ingest = IngestPhase(output_dir="./results")

# Process a file
result = ingest.ingest("path/to/file.fastq")

# Check result
print(f"Status: {result.validation_status}")
print(f"Message: {result.validation_message}")

# Generate reports
ingest.generate_html_report("report.html")
ingest.generate_report("report.json")
```

## Documentation

See `docs/INGEST_GUIDE.md` for comprehensive documentation.

---

**Version**: 1.0  
**Status**: Production Ready  
**Last Updated**: December 2025
