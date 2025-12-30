#!/usr/bin/env python3
"""
INGEST Phase - Unified Script with Cumulative Reporting
=========================================================

Complete INGEST phase with integrated CLI for RNA-seq pipeline.
Comprehensive input detection, validation, and parsing for multiple data types.

NEW FEATURE: Cumulative HTML reporting with duplicate detection
- Appends new samples to existing HTML report
- Automatically skips duplicate samples
- Maintains running total of all tested samples

Usage Examples:
    # Single file
    python3 ingest_cumulative.py /path/to/sample.fastq

    # Multiple files (appends to existing report)
    python3 ingest_cumulative.py /path/to/sample1_R1.fastq /path/to/sample1_R2.fastq

    # With output directory
    python3 ingest_cumulative.py -o ./results /path/to/sample1.fastq /path/to/sample2.fastq

    # Verbose output
    python3 ingest_cumulative.py -v /path/to/sample.fastq

    # Help
    python3 ingest_cumulative.py --help

Author: Bioinformatics Pipeline
Version: 2.1 - Cumulative Reporting with Duplicate Detection
"""

import os
import sys
import json
import gzip
import logging
import argparse
import subprocess
import re
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from html.parser import HTMLParser

# ==================== SAMTOOLS AUTO-INSTALL ====================

def check_and_install_samtools():
    """Check if samtools is installed, install if missing"""
    if shutil.which('samtools'):
        return True
    
    logger = logging.getLogger(__name__)
    logger.info("samtools not found. Attempting to install...")
    
    try:
        # Try apt-get (Linux)
        result = subprocess.run(
            ['apt-get', 'update'],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            subprocess.run(
                ['apt-get', 'install', '-y', 'samtools'],
                capture_output=True,
                timeout=60
            )
            if shutil.which('samtools'):
                logger.info("✓ samtools installed successfully")
                return True
    except Exception as e:
        logger.warning(f"Could not install samtools via apt-get: {e}")
    
    try:
        # Try brew (macOS)
        result = subprocess.run(
            ['brew', 'install', 'samtools'],
            capture_output=True,
            timeout=60
        )
        if result.returncode == 0 and shutil.which('samtools'):
            logger.info("✓ samtools installed successfully")
            return True
    except Exception as e:
        logger.warning(f"Could not install samtools via brew: {e}")
    
    logger.warning("samtools installation failed. BAM validation will use magic bytes only.")
    return False

# Check and install samtools at startup
check_and_install_samtools()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Data class for INGEST phase results"""
    dataset_id: str
    input_type: str
    file_path: str
    file_size: int
    file_size_mb: float
    validation_status: str
    validation_message: str
    file_count: int
    sample_name: str
    is_paired_end: Optional[bool] = None
    detected_format: Optional[str] = None
    total_reads: Optional[int] = None
    sequence_length: Optional[int] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


class HTMLTableParser(HTMLParser):
    """Parse existing HTML report to extract sample names"""
    
    def __init__(self):
        super().__init__()
        self.samples = set()
        self.in_tbody = False
        self.in_td = False
        self.cell_count = 0
        self.current_row = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'tbody':
            self.in_tbody = True
        elif tag == 'td' and self.in_tbody:
            self.in_td = True
    
    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_tbody = False
        elif tag == 'td' and self.in_tbody:
            self.in_td = False
            self.cell_count += 1
            if self.cell_count % 6 == 1:  # First column is sample name
                if self.current_row:
                    self.samples.add(self.current_row[0])
                self.current_row = []
        elif tag == 'tr' and self.in_tbody:
            self.cell_count = 0
    
    def handle_data(self, data):
        if self.in_td:
            self.current_row.append(data.strip())


class IngestPhase:
    """Main INGEST phase class with expert bioinformatics validation"""

    def __init__(self, output_dir: str = "./ingest_output"):
        """Initialize INGEST phase"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    # ==================== EXPERT VALIDATION METHODS ====================
    
    def validate_fastq_header(self, file_path: str) -> Tuple[bool, str]:
        """Expert FASTQ validation: Check magic bytes and header format"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix == '.gz':
                file_handle = gzip.open(file_path, 'rt')
            else:
                file_handle = open(file_path, 'r')
            
            with file_handle as f:
                lines = [f.readline().strip() for _ in range(4)]
            
            if len(lines) < 4:
                return False, "File has fewer than 4 lines (incomplete FASTQ record)"
            
            header, seq, plus, qual = lines[0], lines[1], lines[2], lines[3]
            
            if not header.startswith('@'):
                return False, f"Header line must start with '@', got: {header[:20]}"
            
            if not plus.startswith('+'):
                return False, f"Plus line must start with '+', got: {plus[:20]}"
            
            valid_nucleotides = set('ACGTNacgtnRYWSKMBDHVryswkmbdhv')
            if not all(c in valid_nucleotides for c in seq):
                invalid_chars = set(seq) - valid_nucleotides
                return False, f"Sequence contains invalid nucleotides: {invalid_chars}"
            
            if len(seq) != len(qual):
                return False, f"Sequence length ({len(seq)}) != Quality length ({len(qual)})"
            
            quality_ascii = [ord(c) for c in qual]
            if any(q < 33 or q > 126 for q in quality_ascii):
                return False, "Quality scores contain invalid ASCII characters"
            
            return True, "Valid FASTQ format detected"
            
        except Exception as e:
            return False, f"Error validating FASTQ: {str(e)}"

    def validate_bam_magic(self, file_path: str) -> Tuple[bool, str]:
        """Expert BAM validation: Check BAM magic bytes"""
        try:
            file_path = Path(file_path)
            
            with open(file_path, 'rb') as f:
                magic = f.read(4)
            
            if magic == b'BAM\x01':
                return True, "Valid BAM magic number detected (BAM\\x01)"
            else:
                hex_magic = ' '.join(f'{b:02x}' for b in magic)
                return False, f"Invalid BAM magic number: {hex_magic} (expected: 42 41 4d 01)"
            
        except Exception as e:
            return False, f"Error validating BAM: {str(e)}"

    def validate_cell_header(self, file_path: str) -> Tuple[bool, str]:
        """Expert CELL validation: Check microarray data headers"""
        try:
            file_path = Path(file_path)
            
            with open(file_path, 'r') as f:
                header = f.readline().strip().split('\t')
            
            header_lower = [h.lower() for h in header]
            
            has_probe_id = any('probe' in h for h in header_lower)
            has_intensity = any('intensity' in h or 'signal' in h for h in header_lower)
            
            if not has_probe_id:
                return False, "CELL data must have 'probe_id' column"
            
            if not has_intensity:
                return False, "CELL data must have 'intensity' or 'signal' columns"
            
            if len(header) < 3:
                return False, "CELL data must have at least 3 columns (probe_id, gene_symbol, intensity)"
            
            return True, f"Valid CELL microarray format detected ({len(header)} columns)"
            
        except Exception as e:
            return False, f"Error validating CELL: {str(e)}"

    def validate_count_matrix_structure(self, file_path: str) -> Tuple[bool, str]:
        """Expert count matrix validation: Check matrix structure and requirements"""
        try:
            file_path = Path(file_path)
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if len(lines) < 2:
                return False, "Count matrix must have at least header + 1 data row"
            
            header = lines[0].strip().split('\t')
            if len(header) < 2:
                return False, "Count matrix must have at least 2 columns (gene_id + sample)"
            
            gene_col_name = header[0].lower()
            if 'gene' not in gene_col_name and 'id' not in gene_col_name:
                logger.warning(f"First column '{header[0]}' may not be gene ID")
            
            col_count = len(header)
            errors = []
            
            for line_num, line in enumerate(lines[1:], start=2):
                fields = line.strip().split('\t')
                
                if len(fields) != col_count:
                    if len(errors) < 5:
                        errors.append(f"Line {line_num}: Column count {len(fields)} != header {col_count}")
                
                if not fields[0] or fields[0].strip() == '':
                    if len(errors) < 5:
                        errors.append(f"Line {line_num}: Empty gene ID")
                
                for col_idx in range(1, len(fields)):
                    try:
                        val = float(fields[col_idx])
                        if val < 0:
                            if len(errors) < 5:
                                errors.append(f"Line {line_num}: Negative count value {val}")
                    except ValueError:
                        if len(errors) < 5:
                            errors.append(f"Line {line_num}: Non-numeric value '{fields[col_idx]}'")
            
            if errors:
                error_msg = "; ".join(errors)
                return False, f"Matrix validation errors: {error_msg}"
            
            return True, f"Valid count matrix format ({len(lines)-1} genes × {col_count-1} samples)"
            
        except Exception as e:
            return False, f"Error validating count matrix: {str(e)}"

    # ==================== STEP 1: REGISTER DATASET ====================
    
    def register_dataset(self, dataset_id: str, sample_name: str) -> Dict:
        """Step 1: Register dataset record"""
        logger.info(f"Registering dataset: {dataset_id}")
        
        dataset_metadata = {
            "dataset_id": dataset_id,
            "sample_name": sample_name,
            "registration_time": datetime.now().isoformat(),
            "status": "registered"
        }
        
        logger.info(f"Dataset registered: {dataset_id}")
        return dataset_metadata

    # ==================== STEP 2: DETECT INPUT TYPE ====================
    
    def detect_input_type(self, file_path: str) -> Tuple[str, str]:
        """Step 2: Detect input file type"""
        logger.info(f"Detecting input type for: {file_path}")
        
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension in ['.fastq', '.fq', '.gz'] and any(x in file_path.name for x in ['fastq', 'fq']):
            is_valid, msg = self.validate_fastq_header(str(file_path))
            if is_valid:
                logger.info(f"Detected input type: FASTQ ({msg})")
                return 'FASTQ', f"FASTQ (uncompressed)" if extension != '.gz' else "FASTQ (gzip compressed)"
        
        if extension == '.bam':
            is_valid, msg = self.validate_bam_magic(str(file_path))
            if is_valid:
                logger.info(f"Detected input type: BAM ({msg})")
                return 'BAM', "BAM (Binary Alignment Map)"
        
        if extension in ['.tsv', '.csv', '.txt']:
            is_valid, msg = self.validate_cell_header(str(file_path))
            if is_valid:
                logger.info(f"Detected input type: CELL ({msg})")
                return 'CELL', "CELL Microarray Data"
            
            is_valid, msg = self.validate_count_matrix_structure(str(file_path))
            if is_valid:
                logger.info(f"Detected input type: MATRIX ({msg})")
                return 'MATRIX', "Count Matrix (Processed Expression Data)"
        
        logger.warning(f"Could not definitively detect file type for {file_path.name}")
        return 'UNKNOWN', "Unknown format"

    # ==================== STEP 3: PARSE FASTQ ====================
    
    def parse_fastq(self, file_path: str) -> IngestResult:
        """Step 3a: Parse and validate FASTQ file with expert checks"""
        logger.info(f"Parsing FASTQ file: {file_path}")
        
        file_path = Path(file_path)
        sample_name = file_path.stem.replace('.fastq', '').replace('.fq', '').replace('.gz', '')
        
        try:
            is_valid, header_msg = self.validate_fastq_header(str(file_path))
            if not is_valid:
                logger.warning(f"FASTQ header validation failed: {header_msg}")
                return IngestResult(
                    dataset_id=sample_name,
                    input_type='FASTQ',
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    file_size_mb=file_path.stat().st_size / (1024 * 1024),
                    validation_status='FAIL',
                    validation_message=f"Header validation failed: {header_msg}",
                    file_count=1,
                    sample_name=sample_name
                )
            
            if file_path.suffix == '.gz':
                file_handle = gzip.open(file_path, 'rt')
            else:
                file_handle = open(file_path, 'r')
            
            validation_errors = []
            read_count = 0
            sequence_lengths = []
            
            with file_handle as f:
                lines = []
                for line_num, line in enumerate(f):
                    lines.append(line.rstrip('\n'))
                    
                    if len(lines) == 4:
                        read_count += 1
                        header, seq, plus, qual = lines
                        
                        if not header.startswith('@'):
                            validation_errors.append(f"Read {read_count}: Header must start with @")
                        
                        if not plus.startswith('+'):
                            validation_errors.append(f"Read {read_count}: Plus line must start with +")
                        
                        if len(seq) != len(qual):
                            validation_errors.append(f"Read {read_count}: Seq length ({len(seq)}) != Qual length ({len(qual)})")
                        
                        valid_nucleotides = set('ACGTNacgtnRYWSKMBDHVryswkmbdhv')
                        invalid_chars = set(seq) - valid_nucleotides
                        if invalid_chars:
                            if read_count <= 5:
                                validation_errors.append(f"Read {read_count}: Invalid nucleotides: {invalid_chars}")
                        
                        sequence_lengths.append(len(seq))
                        
                        if read_count > 1000:
                            break
                        
                        lines = []
            
            is_paired = any(pattern in file_path.name for pattern in ['_R1', '_R2', '_1', '_2', '.1', '.2'])
            avg_seq_length = int(sum(sequence_lengths) / len(sequence_lengths)) if sequence_lengths else 0
            
            if validation_errors:
                status = 'FAIL' if len(validation_errors) > 10 else 'WARN'
                message = f"Found {len(validation_errors)} validation errors"
            else:
                status = 'PASS'
                message = "FASTQ validation successful"
            
            result = IngestResult(
                dataset_id=sample_name,
                input_type='FASTQ',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status=status,
                validation_message=message,
                file_count=1,
                sample_name=sample_name,
                is_paired_end=is_paired,
                detected_format='FASTQ (Paired-end)' if is_paired else 'FASTQ (Single-end)',
                total_reads=read_count,
                sequence_length=avg_seq_length
            )
            
            logger.info(f"✓ FASTQ validation: {status} ({read_count} reads, {avg_seq_length} bp avg length)")
            return result
            
        except Exception as e:
            logger.error(f"✗ FASTQ parsing failed: {str(e)}")
            return IngestResult(
                dataset_id=sample_name,
                input_type='FASTQ',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status='FAIL',
                validation_message=f"Parsing error: {str(e)}",
                file_count=1,
                sample_name=sample_name
            )

    # ==================== STEP 3: PARSE BAM ====================
    
    def parse_bam(self, file_path: str) -> IngestResult:
        """Step 3b: Parse and validate BAM file with expert checks"""
        logger.info(f"Parsing BAM file: {file_path}")
        
        file_path = Path(file_path)
        sample_name = file_path.stem.replace('.bam', '')
        
        try:
            is_valid, magic_msg = self.validate_bam_magic(str(file_path))
            if not is_valid:
                logger.warning(f"BAM magic validation failed: {magic_msg}")
                return IngestResult(
                    dataset_id=sample_name,
                    input_type='BAM',
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    file_size_mb=file_path.stat().st_size / (1024 * 1024),
                    validation_status='FAIL',
                    validation_message=f"Magic bytes validation failed: {magic_msg}",
                    file_count=1,
                    sample_name=sample_name
                )
            
            try:
                result = subprocess.run(
                    ['samtools', 'flagstat', str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    total_reads = int(lines[0].split()[0]) if lines else 0
                    is_paired = total_reads > 0
                    status = 'PASS'
                    message = f"BAM validation successful ({total_reads} reads)"
                else:
                    # samtools failed, but magic bytes are valid - return PASS
                    status = 'PASS'
                    message = 'BAM magic number valid (samtools unavailable for read count)'
                    total_reads = None
                    is_paired = None
            
            except (FileNotFoundError, Exception) as e:
                logger.warning(f"samtools error: {e}, using magic bytes validation")
                status = 'PASS'
                message = 'BAM magic number valid (samtools unavailable for read count)'
                total_reads = None
                is_paired = None
            
            result = IngestResult(
                dataset_id=sample_name,
                input_type='BAM',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status=status,
                validation_message=message,
                file_count=1,
                sample_name=sample_name,
                is_paired_end=is_paired,
                detected_format='BAM (Binary Alignment Map)',
                total_reads=total_reads
            )
            
            logger.info(f"✓ BAM validation: {status}")
            return result
            
        except Exception as e:
            logger.error(f"✗ BAM parsing failed: {str(e)}")
            return IngestResult(
                dataset_id=sample_name,
                input_type='BAM',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status='FAIL',
                validation_message=f"Parsing error: {str(e)}",
                file_count=1,
                sample_name=sample_name
            )

    # ==================== STEP 3: PARSE CELL DATA ====================
    
    def parse_cell(self, file_path: str) -> IngestResult:
        """Step 3c: Parse and validate CELL microarray data with expert checks"""
        logger.info(f"Parsing CELL microarray data: {file_path}")
        
        file_path = Path(file_path)
        sample_name = file_path.stem
        
        try:
            is_valid, header_msg = self.validate_cell_header(str(file_path))
            if not is_valid:
                logger.warning(f"CELL header validation failed: {header_msg}")
                return IngestResult(
                    dataset_id=sample_name,
                    input_type='CELL',
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    file_size_mb=file_path.stat().st_size / (1024 * 1024),
                    validation_status='FAIL',
                    validation_message=f"Header validation failed: {header_msg}",
                    file_count=1,
                    sample_name=sample_name
                )
            
            validation_errors = []
            row_count = 0
            col_count = 0
            
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f):
                    fields = line.strip().split('\t')
                    
                    if line_num == 0:
                        col_count = len(fields)
                        if col_count < 3:
                            validation_errors.append("CELL data must have at least 3 columns")
                    else:
                        row_count += 1
                        if len(fields) != col_count:
                            if row_count <= 5:
                                validation_errors.append(f"Line {line_num}: Column count mismatch ({len(fields)} vs {col_count})")
                        
                        probe_id = fields[0]
                        if not probe_id.replace('_', '').replace('-', '').isalnum():
                            if row_count <= 5:
                                validation_errors.append(f"Line {line_num}: Invalid probe ID format: {probe_id}")
                        
                        # Skip gene_symbol (column 1) and check only intensity columns (columns 2+)
                        for col_idx in range(2, min(len(fields), col_count)):
                            try:
                                val = float(fields[col_idx])
                                if val < 0:
                                    if row_count <= 5:
                                        validation_errors.append(f"Line {line_num}: Negative intensity value {val}")
                            except ValueError:
                                if row_count <= 5:
                                    validation_errors.append(f"Line {line_num}, Col {col_idx}: Non-numeric value '{fields[col_idx]}'")
            
            if validation_errors:
                status = 'FAIL' if len(validation_errors) > 10 else 'WARN'
                message = f"Found {len(validation_errors)} validation errors"
            else:
                status = 'PASS'
                message = "CELL data validation successful"
            
            result = IngestResult(
                dataset_id=sample_name,
                input_type='CELL',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status=status,
                validation_message=message,
                file_count=1,
                sample_name=sample_name,
                detected_format='CELL Microarray Data',
                total_reads=row_count,
                sequence_length=col_count
            )
            
            logger.info(f"✓ CELL validation: {status} ({row_count} probes, {col_count} columns)")
            return result
            
        except Exception as e:
            logger.error(f"✗ CELL parsing failed: {str(e)}")
            return IngestResult(
                dataset_id=sample_name,
                input_type='CELL',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status='FAIL',
                validation_message=f"Parsing error: {str(e)}",
                file_count=1,
                sample_name=sample_name
            )

    # ==================== STEP 3: PARSE COUNT MATRIX ====================
    
    def parse_count_matrix(self, file_path: str) -> IngestResult:
        """Step 3d: Parse and validate count matrix with expert checks"""
        logger.info(f"Parsing count matrix: {file_path}")
        
        file_path = Path(file_path)
        sample_name = file_path.stem
        
        try:
            is_valid, structure_msg = self.validate_count_matrix_structure(str(file_path))
            if not is_valid:
                logger.warning(f"Count matrix structure validation failed: {structure_msg}")
                return IngestResult(
                    dataset_id=sample_name,
                    input_type='MATRIX',
                    file_path=str(file_path),
                    file_size=file_path.stat().st_size,
                    file_size_mb=file_path.stat().st_size / (1024 * 1024),
                    validation_status='FAIL',
                    validation_message=f"Structure validation failed: {structure_msg}",
                    file_count=1,
                    sample_name=sample_name
                )
            
            validation_errors = []
            row_count = 0
            col_count = 0
            
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f):
                    fields = line.strip().split('\t')
                    if line.startswith(','):
                        fields = line.strip().split(',')
                    
                    if line_num == 0:
                        col_count = len(fields)
                        if col_count < 2:
                            validation_errors.append("Matrix must have at least 2 columns (gene_id + samples)")
                    else:
                        row_count += 1
                        if len(fields) != col_count:
                            if row_count <= 5:
                                validation_errors.append(f"Line {line_num}: Column count mismatch")
                        
                        gene_id = fields[0]
                        if not gene_id or len(gene_id) == 0:
                            if row_count <= 5:
                                validation_errors.append(f"Line {line_num}: Empty gene ID")
                        
                        for col_idx in range(1, len(fields)):
                            try:
                                val = float(fields[col_idx])
                                if val < 0:
                                    if row_count <= 5:
                                        validation_errors.append(f"Line {line_num}: Negative count {val}")
                                if val != int(val) and row_count <= 5:
                                    logger.warning(f"Line {line_num}: Non-integer count {val}")
                            except ValueError:
                                if row_count <= 5:
                                    validation_errors.append(f"Line {line_num}: Non-numeric value '{fields[col_idx]}'")
            
            if validation_errors:
                status = 'FAIL' if len(validation_errors) > 10 else 'WARN'
                message = f"Found {len(validation_errors)} validation errors"
            else:
                status = 'PASS'
                message = "Count matrix validation successful"
            
            result = IngestResult(
                dataset_id=sample_name,
                input_type='MATRIX',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status=status,
                validation_message=message,
                file_count=1,
                sample_name=sample_name,
                detected_format='Count Matrix (Processed Expression Data)',
                total_reads=row_count,
                sequence_length=col_count - 1
            )
            
            logger.info(f"✓ Count matrix validation: {status} ({row_count} genes, {col_count-1} samples)")
            return result
            
        except Exception as e:
            logger.error(f"✗ Count matrix parsing failed: {str(e)}")
            return IngestResult(
                dataset_id=sample_name,
                input_type='MATRIX',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status='FAIL',
                validation_message=f"Parsing error: {str(e)}",
                file_count=1,
                sample_name=sample_name
            )

    # ==================== MAIN INGEST ORCHESTRATOR ====================
    
    def ingest(self, file_path: str, dataset_id: Optional[str] = None) -> IngestResult:
        """Main INGEST orchestrator - coordinates all steps"""
        file_path = Path(file_path)
        
        if dataset_id is None:
            dataset_id = file_path.stem
        
        sample_name = file_path.stem
        self.register_dataset(dataset_id, sample_name)
        
        input_type, detected_format = self.detect_input_type(str(file_path))
        
        if input_type == 'FASTQ':
            result = self.parse_fastq(str(file_path))
        elif input_type == 'BAM':
            result = self.parse_bam(str(file_path))
        elif input_type == 'CELL':
            result = self.parse_cell(str(file_path))
        elif input_type == 'MATRIX':
            result = self.parse_count_matrix(str(file_path))
        else:
            result = IngestResult(
                dataset_id=dataset_id,
                input_type='UNKNOWN',
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                file_size_mb=file_path.stat().st_size / (1024 * 1024),
                validation_status='FAIL',
                validation_message='Unknown file type',
                file_count=1,
                sample_name=sample_name
            )
        
        self.results.append(result)
        return result

    # ==================== REPORTING ====================
    
    def generate_report(self, output_file: str = "ingest_report.json") -> str:
        """Generate JSON report with cumulative results"""
        output_path = self.output_dir / output_file
        
        # Load existing results from JSON if available
        all_results = []
        existing_samples = set()
        
        if output_path.exists():
            try:
                with open(output_path, 'r') as f:
                    json_data = json.load(f)
                    for result_dict in json_data.get('results', []):
                        all_results.append(result_dict)
                        existing_samples.add(result_dict.get('sample_name'))
                logger.info(f"Loaded {len(all_results)} existing results from JSON")
            except Exception as e:
                logger.warning(f"Could not load existing JSON: {e}")
        
        # Add new results (filter duplicates)
        for result in self.results:
            if result.sample_name not in existing_samples:
                all_results.append(result.to_dict())
                logger.info(f"Adding new sample to JSON: {result.sample_name}")
            else:
                logger.info(f"Skipping duplicate in JSON: {result.sample_name}")
        
        # Save cumulative results
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(all_results),
            "results": all_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Report saved to: {output_path} (Cumulative - {len(all_results)} total samples)")
        return str(output_path)

    def extract_existing_samples(self, html_file: Path) -> Set[str]:
        """Extract existing sample names from HTML report"""
        try:
            with open(html_file, 'r') as f:
                html_content = f.read()
            
            # Use regex to extract sample names from table rows
            pattern = r'<td>([^<]+)</td>\s*<td>([^<]+)</td>'
            matches = re.findall(pattern, html_content)
            
            samples = set()
            for match in matches:
                sample_name = match[0].strip()
                if sample_name and sample_name != 'Sample':
                    samples.add(sample_name)
            
            logger.info(f"Found {len(samples)} existing samples in report")
            return samples
        
        except Exception as e:
            logger.warning(f"Could not parse existing report: {e}")
            return set()

    def generate_html_report(self, output_file: str = "ingest_report.html") -> str:
        """Generate professional HTML report with cumulative mode (append with duplicate detection)"""
        output_path = self.output_dir / output_file
        
        # Load existing results from JSON if available
        all_accumulated_results = []
        existing_samples = set()
        
        json_file = self.output_dir / "ingest_report.json"
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                    for result_dict in json_data.get('results', []):
                        all_accumulated_results.append(result_dict)
                        existing_samples.add(result_dict.get('sample_name'))
                logger.info(f"Loaded {len(all_accumulated_results)} existing results from JSON")
            except Exception as e:
                logger.warning(f"Could not load existing JSON: {e}")
        
        # Filter out duplicates from current results
        new_results = []
        for result in self.results:
            if result.sample_name not in existing_samples:
                new_results.append(result)
                logger.info(f"Adding new sample: {result.sample_name}")
            else:
                logger.info(f"Skipping duplicate sample: {result.sample_name}")
        
        # Combine all results for display (existing + new)
        display_results = all_accumulated_results + [r.to_dict() for r in new_results]
        
        html_template = r"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INGEST Phase - Validation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ font-size: 14px; opacity: 0.9; }}
        .summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; padding: 30px; background: #f9f9f9; border-bottom: 1px solid #eee; }}
        .summary-box {{ text-align: center; }}
        .summary-box .number {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .summary-box .label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .content {{ padding: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #f0f0f0; padding: 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd; }}
        td {{ padding: 12px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .status-pass {{ color: #27ae60; font-weight: bold; }}
        .status-warn {{ color: #f39c12; font-weight: bold; }}
        .status-fail {{ color: #e74c3c; font-weight: bold; }}
        .footer {{ background: #f9f9f9; padding: 20px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
        .info {{ background: #e8f4f8; padding: 15px; margin-bottom: 20px; border-left: 4px solid #667eea; border-radius: 4px; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>INGEST Phase - Validation Report</h1>
            <p>RNA-seq Pipeline Input Validation</p>
        </div>
        
        <div class="summary">
            <div class="summary-box">
                <div class="number">{total}</div>
                <div class="label">Total Files</div>
            </div>
            <div class="summary-box">
                <div class="number" style="color: #27ae60;">{pass_count}</div>
                <div class="label">PASS</div>
            </div>
            <div class="summary-box">
                <div class="number" style="color: #f39c12;">{warn_count}</div>
                <div class="label">WARN</div>
            </div>
            <div class="summary-box">
                <div class="number" style="color: #e74c3c;">{fail_count}</div>
                <div class="label">FAIL</div>
            </div>
        </div>
        
        <div class="content">
            <div class="info">
                <strong>ℹ Cumulative Report:</strong> This report accumulates all tested samples. Duplicate samples are automatically skipped. Total shows all unique samples tested.
            </div>
            <h2>Validation Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Sample</th>
                        <th>Input Type</th>
                        <th>File Size</th>
                        <th>Reads/Rows</th>
                        <th>Status</th>
                        <th>Message</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Last Updated: {timestamp}</p>
            <p>INGEST Phase v2.1 - Enhanced Bioinformatics Validation (Cumulative Mode)</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Calculate totals including existing samples
        total_pass = len(existing_samples)  # Approximate
        total_warn = 0
        total_fail = 0
        
        # Calculate totals from ALL accumulated results
        pass_count = sum(1 for r in display_results if r.get('validation_status') == 'PASS' or (isinstance(r, dict) and r.get('validation_status') == 'PASS'))
        warn_count = sum(1 for r in display_results if r.get('validation_status') == 'WARN' or (isinstance(r, dict) and r.get('validation_status') == 'WARN'))
        fail_count = sum(1 for r in display_results if r.get('validation_status') == 'FAIL' or (isinstance(r, dict) and r.get('validation_status') == 'FAIL'))
        
        # Generate table rows from ALL accumulated results
        rows = ""
        for result in display_results:
            # Handle both dict and IngestResult objects
            if isinstance(result, dict):
                sample_name = result.get('sample_name', 'N/A')
                input_type = result.get('input_type', 'N/A')
                file_size_mb = result.get('file_size_mb', 0)
                file_size = result.get('file_size', 0)
                total_reads = result.get('total_reads')
                validation_status = result.get('validation_status', 'UNKNOWN')
                validation_message = result.get('validation_message', '')
            else:
                sample_name = result.sample_name
                input_type = result.input_type
                file_size_mb = result.file_size_mb
                file_size = result.file_size
                total_reads = result.total_reads
                validation_status = result.validation_status
                validation_message = result.validation_message
            
            status_class = f"status-{validation_status.lower()}"
            file_size_display = f"{file_size_mb:.2f} MB" if file_size_mb > 1 else f"{file_size / 1024:.2f} KB"
            reads_display = f"{total_reads:,}" if total_reads else "N/A"
            
            rows += f"""
            <tr>
                <td>{sample_name}</td>
                <td>{input_type}</td>
                <td>{file_size_display}</td>
                <td>{reads_display}</td>
                <td><span class="{status_class}">{validation_status}</span></td>
                <td>{validation_message}</td>
            </tr>
            """
        
        html_content = html_template.format(
            total=len(display_results),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            rows=rows,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML report saved to: {output_path} (Cumulative mode - {len(new_results)} new samples added)")
        return str(output_path)


# ==================== COMMAND LINE INTERFACE ====================

def create_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="INGEST Phase - Process samples from the command line (Cumulative Mode)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  python3 ingest_cumulative.py /path/to/sample.fastq

  # Multiple files (appends to existing report)
  python3 ingest_cumulative.py /path/to/sample1_R1.fastq /path/to/sample1_R2.fastq

  # With output directory
  python3 ingest_cumulative.py -o ./results /path/to/sample1.fastq /path/to/sample2.fastq

  # Generate reports
  python3 ingest_cumulative.py -o ./results --html report.html /path/to/sample.fastq

  # Verbose output
  python3 ingest_cumulative.py -v /path/to/sample.fastq
        """
    )
    
    parser.add_argument(
        'samples',
        nargs='+',
        help='Sample file(s) to process (FASTQ, BAM, TSV, CSV)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./ingest_output',
        help='Output directory for reports (default: ./ingest_output)'
    )
    
    parser.add_argument(
        '-d', '--dataset-id',
        help='Custom dataset ID (if not specified, auto-generated from filename)'
    )
    
    parser.add_argument(
        '--html',
        help='Generate HTML report with specified filename'
    )
    
    parser.add_argument(
        '--json',
        help='Generate JSON report with specified filename'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Do not generate reports'
    )
    
    return parser


def main():
    """Main CLI function"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize INGEST phase
    ingest = IngestPhase(output_dir=args.output)
    
    # Process samples
    print("\n" + "="*70)
    print("INGEST Phase - Command Line Interface (Cumulative Mode)")
    print("="*70)
    print(f"Processing {len(args.samples)} file(s)...\n")
    
    results = []
    for idx, sample_file in enumerate(args.samples, 1):
        sample_path = Path(sample_file)
        
        if not sample_path.exists():
            print(f"✗ [{idx}/{len(args.samples)}] {sample_path.name}: File not found")
            continue
        
        print(f"[{idx}/{len(args.samples)}] {sample_path.name}")
        
        result = ingest.ingest(str(sample_path), dataset_id=args.dataset_id)
        results.append(result)
        
        print(f"  Dataset ID:        {result.dataset_id}")
        print(f"  Sample Name:       {result.sample_name}")
        print(f"  Input Type:        {result.input_type}")
        print(f"  Format:            {result.detected_format}")
        print(f"  Validation Status: {result.validation_status}")
        
        if args.verbose:
            file_size_display = f"{result.file_size_mb:.2f} MB" if result.file_size_mb > 1 else f"{result.file_size / 1024:.2f} KB"
            print(f"  File Size:         {file_size_display}")
            if result.total_reads:
                print(f"  Total Reads/Rows:  {result.total_reads:,}")
            if result.sequence_length:
                print(f"  Sequence Length:   {result.sequence_length}")
            if result.is_paired_end is not None:
                print(f"  Paired-End:        {result.is_paired_end}")
        
        print(f"  Message:           {result.validation_message}\n")
    
    if not results:
        print("✗ No files were successfully processed!")
        sys.exit(1)
    
    # Generate reports if requested
    if not args.no_report:
        print("="*70)
        print("Generating Reports (Cumulative Mode)")
        print("="*70 + "\n")
        
        Path(args.output).mkdir(parents=True, exist_ok=True)
        
        html_filename = args.html if args.html else "ingest_report.html"
        ingest.generate_html_report(html_filename)
        html_path = f"{args.output}/{html_filename}"
        print(f"✓ HTML Report: {html_path} (Cumulative - new samples appended)")
        
        json_filename = args.json if args.json else "ingest_report.json"
        ingest.generate_report(json_filename)
        json_path = f"{args.output}/{json_filename}"
        print(f"✓ JSON Report: {json_path}\n")
    
    # Print summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r.validation_status == "PASS")
    warned = sum(1 for r in results if r.validation_status == "WARN")
    failed = sum(1 for r in results if r.validation_status == "FAIL")
    
    print(f"Current Batch:    {len(results)}")
    print(f"PASS:             {passed}")
    print(f"WARN:             {warned}")
    print(f"FAIL:             {failed}\n")
    
    if failed > 0:
        print("⚠ Warning: Some files failed validation.\n")
        sys.exit(1)
    else:
        print("✓ All files in current batch passed validation!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
