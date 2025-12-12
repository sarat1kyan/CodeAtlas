"""Tests for language detection."""

from pathlib import Path

import pytest

from codeatlas.language_detector import LanguageDetector


class TestLanguageDetector:
    """Test language detection."""

    def test_detect_python_by_extension(self):
        """Test Python detection by extension."""
        detector = LanguageDetector()
        lang = detector.detect_from_path(Path("test.py"))
        assert lang == "Python"

    def test_detect_javascript_by_extension(self):
        """Test JavaScript detection by extension."""
        detector = LanguageDetector()
        lang = detector.detect_from_path(Path("test.js"))
        assert lang == "JavaScript"

    def test_detect_from_shebang(self):
        """Test detection from shebang."""
        detector = LanguageDetector()
        content = "#!/usr/bin/env python3\nprint('hello')"
        lang = detector.detect_from_shebang(content)
        assert lang == "Python"

    def test_detect_from_content(self):
        """Test detection from content patterns."""
        detector = LanguageDetector()
        content = "def hello():\n    print('world')"
        lang = detector.detect_from_content(content)
        assert lang == "Python"

