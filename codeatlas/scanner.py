"""Codebase scanner with parallel processing and statistics collection."""

import os
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from codeatlas.cache import ScanCache
from codeatlas.comment_parser import Comment, CommentParser
from codeatlas.config import Config
from codeatlas.language_detector import LanguageDetector

console = Console()


@dataclass
class FileStats:
    """Statistics for a single file."""

    path: str
    size_bytes: int
    total_lines: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    language: Optional[str]
    comments: List[Comment]
    is_binary: bool = False


@dataclass
class ScanResult:
    """Complete scan result for a codebase."""

    base_path: Path
    total_files: int
    total_dirs: int
    total_size_bytes: int
    total_lines: int
    total_blank: int
    total_comments: int
    total_code: int
    per_language: Dict[str, Dict[str, int]]
    per_file: Dict[str, FileStats]
    git_info: Optional[Dict[str, Any]] = None


class CodebaseScanner:
    """Scans codebases and collects statistics."""

    def __init__(
        self,
        config: Optional[Config] = None,
        language_detector: Optional[LanguageDetector] = None,
        comment_parser: Optional[CommentParser] = None,
    ):
        """Initialize scanner."""
        self.config = config or Config()
        self.language_detector = language_detector or LanguageDetector()
        self.comment_parser = comment_parser or CommentParser(self.language_detector)
        self.cache: Optional[ScanCache] = None

        if self.config.get("cache.enabled", True):
            cache_dir = Path(self.config.get("cache.directory", ".codeatlas/cache"))
            self.cache = ScanCache(cache_dir)

    def _is_binary_file(self, file_path: Path, content: bytes) -> bool:
        """Detect if file is binary."""
        # Check for null bytes
        if b"\x00" in content[:8192]:
            return True

        # Check file extension
        binary_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".ico",
            ".svg",
            ".pdf",
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            ".o",
            ".obj",
            ".pyc",
            ".pyo",
            ".class",
            ".jar",
            ".war",
            ".ear",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot",
        }
        if file_path.suffix.lower() in binary_extensions:
            return True

        return False

    def _read_file_safe(self, file_path: Path, max_size_mb: int = 10) -> Tuple[Optional[str], bool]:
        """
        Safely read a text file.

        Returns:
            Tuple of (content, is_binary)
        """
        try:
            stat = file_path.stat()
            max_size = max_size_mb * 1024 * 1024
            if stat.st_size > max_size:
                return None, True

            with open(file_path, "rb") as f:
                raw_content = f.read()

            if self._is_binary_file(file_path, raw_content):
                return None, True

            # Try to detect encoding
            detected = chardet.detect(raw_content)
            encoding = detected.get("encoding", "utf-8")

            try:
                content = raw_content.decode(encoding, errors="replace")
                return content, False
            except Exception:
                return None, True
        except Exception:
            return None, True

    def _scan_file(self, file_path: Path, base_path: Path) -> Optional[FileStats]:
        """Scan a single file and return statistics."""
        # Check cache
        if self.cache:
            cached = self.cache.get(file_path)
            if cached:
                # Re-parse comments if needed (not cached)
                if not cached.get("is_binary", False):
                    content, _ = self._read_file_safe(
                        file_path, max_size_mb=self.config.get("scan.max_file_size_mb", 10)
                    )
                    if content:
                        language = cached.get("language")
                        comments = self.comment_parser.parse_comments(str(file_path), content, language)
                        cached["comments"] = comments
                else:
                    cached["comments"] = []
                return FileStats(**cached)

        content, is_binary = self._read_file_safe(
            file_path, max_size_mb=self.config.get("scan.max_file_size_mb", 10)
        )

        if is_binary or content is None:
            return FileStats(
                path=str(file_path.relative_to(base_path)),
                size_bytes=file_path.stat().st_size,
                total_lines=0,
                blank_lines=0,
                comment_lines=0,
                code_lines=0,
                language=None,
                comments=[],
                is_binary=True,
            )

        # Detect language
        language = self.language_detector.detect(file_path, content)

        # Parse comments
        comments = self.comment_parser.parse_comments(str(file_path), content, language)

        # Count lines
        lines = content.split("\n")
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        
        # Count comment lines properly (block comments span multiple lines)
        comment_lines = 0
        comment_line_set = set()
        for comment in comments:
            if comment.is_block and comment.block_start and comment.block_end:
                # Block comment spans multiple lines
                for line_num in range(comment.block_start, comment.block_end + 1):
                    comment_line_set.add(line_num)
            else:
                # Single line comment
                comment_line_set.add(comment.line_number)
        comment_lines = len(comment_line_set)
        
        code_lines = total_lines - blank_lines - comment_lines

        stats = FileStats(
            path=str(file_path.relative_to(base_path)),
            size_bytes=len(content.encode("utf-8")),
            total_lines=total_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            code_lines=code_lines,
            language=language,
            comments=comments,
            is_binary=False,
        )

        # Cache result (exclude comments for serialization)
        if self.cache:
            cache_data = {
                "path": stats.path,
                "size_bytes": stats.size_bytes,
                "total_lines": stats.total_lines,
                "blank_lines": stats.blank_lines,
                "comment_lines": stats.comment_lines,
                "code_lines": stats.code_lines,
                "language": stats.language,
                "is_binary": stats.is_binary,
                # Comments are not cached (re-parse on demand)
            }
            self.cache.set(file_path, cache_data)

        return stats

    def _should_skip_path(self, path: Path, base_path: Path, skip_gitignored: bool) -> bool:
        """Check if path should be skipped."""
        # Skip hidden files/dirs (except .codeatlas)
        if path.name.startswith(".") and path.name != ".codeatlas":
            return True

        # Skip common build/dependency dirs
        skip_dirs = {
            "__pycache__",
            "node_modules",
            ".git",
            ".svn",
            ".hg",
            "venv",
            "env",
            ".venv",
            "build",
            "dist",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        }
        if path.name in skip_dirs:
            return True

        # Git integration (if enabled)
        if skip_gitignored:
            from codeatlas.git_integration import GitIntegration

            git = GitIntegration(base_path)
            if git.is_gitignored(path):
                return True

        return False

    def scan(
        self,
        base_path: Path,
        skip_gitignored: bool = False,
        progress: Optional[Progress] = None,
    ) -> ScanResult:
        """
        Scan a codebase and return statistics.

        Args:
            base_path: Root path to scan
            skip_gitignored: Whether to skip gitignored files
            progress: Optional Rich progress bar

        Returns:
            ScanResult object
        """
        base_path = base_path.resolve()
        if not base_path.exists():
            raise ValueError(f"Path does not exist: {base_path}")

        # Collect all files
        all_files: List[Path] = []
        all_dirs: Set[Path] = set()

        task = None
        if progress:
            task = progress.add_task("[cyan]Collecting files...", total=None)

        for root, dirs, files in os.walk(base_path):
            root_path = Path(root)
            all_dirs.add(root_path)

            # Filter dirs
            dirs[:] = [d for d in dirs if not self._should_skip_path(root_path / d, base_path, skip_gitignored)]

            for file in files:
                file_path = root_path / file
                if not self._should_skip_path(file_path, base_path, skip_gitignored):
                    all_files.append(file_path)

        if progress and task:
            progress.update(task, total=len(all_files))

        # Scan files in parallel
        num_workers = self.config.get("scan.parallel_workers")
        if num_workers is None:
            num_workers = min(32, (os.cpu_count() or 1) + 4)

        per_file: Dict[str, FileStats] = {}
        per_language: Dict[str, Dict[str, int]] = {}

        scan_task = None
        if progress:
            scan_task = progress.add_task("[green]Scanning files...", total=len(all_files))

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_file = {
                executor.submit(self._scan_file, file_path, base_path): file_path
                for file_path in all_files
            }

            for future in as_completed(future_to_file):
                try:
                    stats = future.result()
                    if stats:
                        per_file[stats.path] = stats

                        # Aggregate by language
                        lang = stats.language or "Unknown"
                        if lang not in per_language:
                            per_language[lang] = {
                                "files": 0,
                                "lines": 0,
                                "blank": 0,
                                "comments": 0,
                                "code": 0,
                                "bytes": 0,
                            }
                        per_language[lang]["files"] += 1
                        per_language[lang]["lines"] += stats.total_lines
                        per_language[lang]["blank"] += stats.blank_lines
                        per_language[lang]["comments"] += stats.comment_lines
                        per_language[lang]["code"] += stats.code_lines
                        per_language[lang]["bytes"] += stats.size_bytes
                except Exception as e:
                    file_path = future_to_file[future]
                    console.print(f"[yellow]Warning: Failed to scan {file_path}: {e}[/yellow]")

                if progress and scan_task:
                    progress.update(scan_task, advance=1)

        # Calculate totals
        total_files = len(per_file)
        total_dirs = len(all_dirs)
        total_size_bytes = sum(s.size_bytes for s in per_file.values())
        total_lines = sum(s.total_lines for s in per_file.values())
        total_blank = sum(s.blank_lines for s in per_file.values())
        total_comments = sum(s.comment_lines for s in per_file.values())
        total_code = sum(s.code_lines for s in per_file.values())

        return ScanResult(
            base_path=base_path,
            total_files=total_files,
            total_dirs=total_dirs,
            total_size_bytes=total_size_bytes,
            total_lines=total_lines,
            total_blank=total_blank,
            total_comments=total_comments,
            total_code=total_code,
            per_language=per_language,
            per_file=per_file,
        )

