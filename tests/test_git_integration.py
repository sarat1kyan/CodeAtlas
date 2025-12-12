"""Tests for git integration."""

import tempfile
from pathlib import Path

import pytest

from codeatlas.git_integration import GitIntegration


class TestGitIntegration:
    """Test git integration."""

    def test_is_git_repo_false(self):
        """Test non-git repo detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git = GitIntegration(Path(tmpdir))
            assert not git.is_git_repo()

