"""Tests for export functionality."""

import tempfile
from pathlib import Path

import pytest

from codeatlas.export import Exporter
from codeatlas.scanner import ScanResult


class TestExporter:
    """Test export functionality."""

    def test_export_json(self):
        """Test JSON export."""
        exporter = Exporter()
        scan_result = ScanResult(
            base_path=Path("/test"),
            total_files=1,
            total_dirs=1,
            total_size_bytes=1000,
            total_lines=100,
            total_blank=10,
            total_comments=20,
            total_code=70,
            per_language={},
            per_file={},
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = Path(f.name)

        try:
            exporter.export_json(scan_result, output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
        finally:
            output_path.unlink()

