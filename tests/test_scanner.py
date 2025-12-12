"""Tests for codebase scanner."""

import tempfile
from pathlib import Path

import pytest

from codeatlas.config import Config
from codeatlas.scanner import CodebaseScanner


class TestCodebaseScanner:
    """Test codebase scanner."""

    def test_scan_simple_repo(self):
        """Test scanning a simple repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            test_file = repo_path / "test.py"
            test_file.write_text("# Test file\ndef hello():\n    print('world')\n")

            config = Config(repo_path)
            scanner = CodebaseScanner(config)
            result = scanner.scan(repo_path)

            assert result.total_files == 1
            assert result.total_code > 0

