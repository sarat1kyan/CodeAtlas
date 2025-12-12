"""Git integration for CodeAtlas."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set

from rich.console import Console

console = Console()


class GitIntegration:
    """Git repository integration."""

    def __init__(self, repo_path: Path):
        """Initialize git integration."""
        self.repo_path = repo_path.resolve()
        self._is_git_repo: Optional[bool] = None
        self._git_root: Optional[Path] = None

    def is_git_repo(self) -> bool:
        """Check if path is a git repository."""
        if self._is_git_repo is not None:
            return self._is_git_repo

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                check=False,
            )
            self._is_git_repo = result.returncode == 0
            if self._is_git_repo:
                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    self._git_root = Path(result.stdout.strip())
            return self._is_git_repo
        except Exception:
            self._is_git_repo = False
            return False

    def get_git_root(self) -> Optional[Path]:
        """Get git repository root."""
        if self.is_git_repo():
            return self._git_root
        return None

    def get_git_status(self) -> Dict[str, List[str]]:
        """
        Get git status summary.

        Returns:
            Dictionary with keys: modified, untracked, added, deleted, renamed
        """
        if not self.is_git_repo():
            return {}

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return {}

            status: Dict[str, List[str]] = {
                "modified": [],
                "untracked": [],
                "added": [],
                "deleted": [],
                "renamed": [],
            }

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue

                status_code = line[:2]
                file_path = line[3:].strip()

                if status_code.startswith("??"):
                    status["untracked"].append(file_path)
                elif status_code.startswith("A") or status_code.startswith("M") and "A" in status_code:
                    status["added"].append(file_path)
                elif status_code.startswith("D"):
                    status["deleted"].append(file_path)
                elif status_code.startswith("R"):
                    status["renamed"].append(file_path)
                elif status_code.startswith("M"):
                    status["modified"].append(file_path)

            return status
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get git status: {e}[/yellow]")
            return {}

    def is_gitignored(self, file_path: Path) -> bool:
        """
        Check if a file is gitignored.

        Args:
            file_path: Path to check

        Returns:
            True if file is gitignored
        """
        if not self.is_git_repo():
            return False

        git_root = self.get_git_root()
        if not git_root:
            return False

        try:
            # Get relative path from git root
            try:
                rel_path = file_path.relative_to(git_root)
            except ValueError:
                # File is outside git repo
                return False

            result = subprocess.run(
                ["git", "check-ignore", "-q", str(rel_path)],
                cwd=git_root,
                capture_output=True,
                check=False,
            )

            # Exit code 0 means file is ignored
            return result.returncode == 0
        except Exception:
            return False

    def get_gitignored_paths(self) -> Set[Path]:
        """
        Get set of gitignored paths relative to repo root.

        Returns:
            Set of Path objects relative to git root
        """
        if not self.is_git_repo():
            return set()

        git_root = self.get_git_root()
        if not git_root:
            return set()

        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--ignored", "--exclude-standard"],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return set()

            ignored = set()
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    ignored.add(git_root / line.strip())

            return ignored
        except Exception:
            return set()

    def check_merge_markers(self, file_path: Path) -> bool:
        """Check if file contains git merge conflict markers."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                return (
                    "<<<<<<<" in content
                    or "=======" in content
                    or ">>>>>>>" in content
                )
        except Exception:
            return False

    def get_git_info(self) -> Dict[str, any]:
        """
        Get comprehensive git information.

        Returns:
            Dictionary with git repository information
        """
        if not self.is_git_repo():
            return {}

        status = self.get_git_status()
        git_root = self.get_git_root()

        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=False,
            )
            branch = result.stdout.strip() if result.returncode == 0 else None

            # Get commit hash
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=git_root,
                capture_output=True,
                text=True,
                check=False,
            )
            commit_hash = result.stdout.strip() if result.returncode == 0 else None

            return {
                "is_git_repo": True,
                "root": str(git_root) if git_root else None,
                "branch": branch,
                "commit": commit_hash,
                "status": status,
            }
        except Exception:
            return {"is_git_repo": True, "root": str(git_root) if git_root else None}

