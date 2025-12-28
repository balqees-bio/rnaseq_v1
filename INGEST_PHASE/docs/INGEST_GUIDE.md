# INGEST Phase - RNA-seq Pipeline

**Version 1.0 | December 2025**

---

## 1. Overview

This document provides a comprehensive guide to the **INGEST Phase**, a standalone Python script designed for robust input detection, validation, and parsing for RNA-seq and other transcriptomic data. It is the first and most critical step in any bioinformatics pipeline, ensuring data quality and integrity before downstream analysis.

This script is built to be **accurate, professional, and easy to use**, with clear outputs and comprehensive validation checks.

### Key Features

- **Multi-Format Support**: Handles FASTQ, BAM, CELL microarray, and processed count matrices.
- **Comprehensive Validation**: Performs detailed checks on file format, integrity, and content.
- **Clear Reporting**: Generates both machine-readable JSON and human-readable HTML reports.
- **Standalone & Integratable**: Can be run as a standalone script for testing or easily integrated into a larger pipeline.
- **Example-Driven**: Comes with a full suite of test data and example usage scripts.

---

## 2. How It Works: The INGEST Steps

The script follows a logical sequence of steps as defined in the pipeline overview:

| Step Order | Step ID | Step Label | Description |
| :--- | :--- | :--- | :--- |
| 1 | `register_dataset` | Register Dataset | Creates a unique record for the dataset with a timestamp. |
| 2 | `detect_input` | Detect Input Type | Automatically determines the file type (FASTQ, BAM, CELL, MATRIX). |
| 3 | `raw_parse` | Parse & Validate | Applies specific validation rules based on the detected file type. |
| 4 | `proc_parse` | Parse Processed | Validates the shape and headers of pre-processed matrices. |
| 5 | `generate_report` | Generate Reports | Creates detailed JSON and HTML reports of the results. |

---

## 3. Getting Started: Running the Examples

To get started and see the script in action, follow these steps.

### Prerequisites

- Python 3.7+
- `samtools` (optional, for full BAM validation)

### Step 1: File Structure

Ensure you have the following files in your directory:

```
/
├── ingest_phase.py           # The main script
├── ingest_examples.py        # The example runner script
└── ingest_test_data/         # Directory with test files
    ├── sample_R1.fastq
    ├── sample_R2.fastq
    ├── cell_data.tsv
    └── count_matrix.tsv
```

### Step 2: Run the Examples

Execute the example script from your terminal:

```bash
python3 ingest_examples.py
```

This will run a series of tests covering all supported input types and generate a summary report on the console.

### Step 3: Review the Output

After running the examples, you will find the following outputs:

1.  **Console Output**: A detailed log of each test case and its result.
2.  **Output Directory**: A new directory named `ingest_output/` will be created with the following reports:
    -   `ingest_report.json`: A machine-readable JSON file with detailed results for each processed file.
    -   `ingest_report.html`: A professional, human-readable HTML report summarizing the validation results.

**Example HTML Report:**

(A professional HTML report with summary boxes and a detailed results table will be generated. Open `ingest_output/ingest_report.html` in a web browser to view it.)

---

## 4. Input File Types & Validation Rules

### a) FASTQ Files (`.fastq`, `.fq`, `.fastq.gz`, `.fq.gz`)

-   **Detection**: Based on file extension.
-   **Validation Checks**:
    -   Header line must start with `@`.
    -   Sequence and quality score lengths must match for each read.
    -   Plus line must start with `+`.
    -   Detects if the file is likely part of a paired-end set (e.g., `_R1`, `_2`).

### b) BAM Files (`.bam`)

-   **Detection**: Based on `.bam` extension.
-   **Validation Checks**:
    -   Verifies the BAM magic number (`BAM\x01`) at the beginning of the file.
    -   If `samtools` is installed, uses `samtools flagstat` to get total reads and check for paired-end flags.

### c) CELL Microarray Data (`.tsv`, `.txt`)

-   **Detection**: Heuristic-based content analysis. Looks for common CELL file headers like `probe_id`, `gene_symbol`, `intensity`.
-   **Validation Checks**:
    -   Ensures consistent column counts across rows.
    -   Validates that probe IDs have a valid format.
    -   Checks that intensity/signal columns contain numeric data.

### d) Count Matrix (`.tsv`, `.csv`, `.txt`)

-   **Detection**: Heuristic-based content analysis. Checks if the file has a header with sample names and subsequent rows with gene IDs and numeric data.
-   **Validation Checks**:
    -   Ensures the matrix has a consistent shape (all rows have the same number of columns).
    -   Validates that gene IDs are not empty.
    -   Ensures all count values are non-negative numbers.

---

## 5. Interpreting the Results

The script provides a clear validation status for each file:

| Status | Meaning |
| :--- | :--- |
| **PASS** | The file is correctly formatted and passed all validation checks. | 
| **WARN** | The file is likely usable, but has minor issues (e.g., `samtools` not found for full BAM check, or a few inconsistent rows in a large matrix). | 
| **FAIL** | The file has critical formatting errors and is not suitable for downstream analysis without correction. |

---

## 6. Integrating into Your Pipeline

The `ingest_phase.py` script is designed to be modular.

### How to Use the `IngestPhase` Class

1.  **Import the class**:
    ```python
    from ingest_phase import IngestPhase
    ```

2.  **Instantiate the class**:
    ```python
    ingest_handler = IngestPhase(output_dir="./my_pipeline_output/ingest")
    ```

3.  **Process a file**:
    ```python
    file_to_process = "/path/to/your/data.fastq.gz"
    try:
        result = ingest_handler.ingest(file_to_process)
        print(f"Validation status: {result.validation_status}")
    except FileNotFoundError:
        print("File not found!")
    except ValueError as e:
        print(f"Unknown file type: {e}")
    ```

4.  **Generate reports** after processing multiple files:
    ```python
    # ... process multiple files ...
    ingest_handler.generate_html_report("my_ingest_report.html")
    ```

This professional, well-documented, and tested script provides a reliable foundation for the INGEST phase of your transcriptomic pipeline.
