"""Code duplication detector for finding duplicate code blocks."""

import ast
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from rich.console import Console

console = Console()


@dataclass
class DuplicateBlock:
    """Represents a duplicate code block."""

    hash: str
    lines: List[str]
    locations: List[Tuple[str, int, int]]  # (file_path, start_line, end_line)
    size: int  # Number of lines
    similarity: float = 100.0


@dataclass
class DuplicationResult:
    """Results from duplication detection."""

    total_duplicates: int
    total_duplicated_lines: int
    duplicate_blocks: List[DuplicateBlock] = field(default_factory=list)
    files_with_duplicates: Set[str] = field(default_factory=set)
    duplication_percentage: float = 0.0


class DuplicationDetector:
    """Detects code duplication in codebases."""

    def __init__(self, project_path: Path, min_lines: int = 5, min_similarity: float = 80.0):
        """Initialize duplication detector."""
        self.project_path = project_path.resolve()
        self.min_lines = min_lines
        self.min_similarity = min_similarity

    def detect(self) -> DuplicationResult:
        """Detect code duplication."""
        result = DuplicationResult(total_duplicates=0, total_duplicated_lines=0)

        # Collect all code files
        code_files = self._collect_code_files()

        # Find duplicates
        duplicates = self._find_duplicates(code_files)

        # Process and filter duplicates
        for dup_hash, blocks in duplicates.items():
            if len(blocks) < 2:  # Need at least 2 occurrences
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(blocks)

            if similarity < self.min_similarity:
                continue

            # Create duplicate block
            first_block = blocks[0]
            duplicate_block = DuplicateBlock(
                hash=dup_hash,
                lines=first_block["lines"],
                locations=[(b["file"], b["start_line"], b["end_line"]) for b in blocks],
                size=len(first_block["lines"]),
                similarity=similarity,
            )

            result.duplicate_blocks.append(duplicate_block)
            result.total_duplicates += len(blocks) - 1  # -1 because one is original
            result.total_duplicated_lines += len(first_block["lines"]) * (len(blocks) - 1)

            for block in blocks:
                result.files_with_duplicates.add(block["file"])

        # Calculate duplication percentage
        total_lines = sum(self._count_lines(f) for f in code_files)
        if total_lines > 0:
            result.duplication_percentage = (result.total_duplicated_lines / total_lines) * 100

        return result

    def _collect_code_files(self) -> List[Path]:
        """Collect all code files to analyze."""
        code_files: List[Path] = []
        extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".rb", ".php", ".go", ".rs", ".cpp", ".c", ".h", ".hpp", ".cs"}

        skip_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "venv", "target",
            "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            "vendor", "bower_components", ".next", ".nuxt", "bin", "obj"
        }

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in extensions:
                    try:
                        if file_path.stat().st_size < 10 * 1024 * 1024:  # Skip files > 10MB
                            code_files.append(file_path)
                    except Exception:
                        pass

        return code_files

    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return len(f.readlines())
        except Exception:
            return 0

    def _find_duplicates(self, code_files: List[Path]) -> Dict[str, List[Dict]]:
        """Find duplicate code blocks."""
        duplicates: Dict[str, List[Dict]] = {}

        for file_path in code_files:
            try:
                blocks = self._extract_blocks(file_path)
                for block in blocks:
                    block_hash = self._hash_block(block["lines"])
                    if block_hash not in duplicates:
                        duplicates[block_hash] = []
                    duplicates[block_hash].append({
                        "file": str(file_path.relative_to(self.project_path)),
                        "start_line": block["start_line"],
                        "end_line": block["end_line"],
                        "lines": block["lines"],
                    })
            except Exception as e:
                console.print(f"[dim]Warning: Failed to analyze {file_path}: {e}[/dim]")

        return duplicates

    def _extract_blocks(self, file_path: Path) -> List[Dict]:
        """Extract code blocks from a file."""
        blocks: List[Dict] = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Extract sliding windows of code
            for i in range(len(lines) - self.min_lines + 1):
                block_lines = [line.rstrip() for line in lines[i:i + self.min_lines]]
                
                # Skip if all lines are empty or just whitespace
                if all(not line.strip() for line in block_lines):
                    continue
                
                # Skip if it's all comments
                if all(line.strip().startswith(("//", "#", "*", "/*", "*/")) for line in block_lines if line.strip()):
                    continue

                blocks.append({
                    "start_line": i + 1,
                    "end_line": i + self.min_lines,
                    "lines": block_lines,
                })

            # Also extract larger blocks (up to 20 lines)
            for block_size in range(self.min_lines + 1, min(21, len(lines) + 1)):
                for i in range(len(lines) - block_size + 1):
                    block_lines = [line.rstrip() for line in lines[i:i + block_size]]
                    
                    if all(not line.strip() for line in block_lines):
                        continue
                    
                    blocks.append({
                        "start_line": i + 1,
                        "end_line": i + block_size,
                        "lines": block_lines,
                    })

        except Exception:
            pass

        return blocks

    def _hash_block(self, lines: List[str]) -> str:
        """Create a hash for a code block."""
        # Normalize the block (remove whitespace differences)
        normalized = "\n".join(line.strip() for line in lines if line.strip())
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def _calculate_similarity(self, blocks: List[Dict]) -> float:
        """Calculate similarity between blocks."""
        if len(blocks) < 2:
            return 100.0

        # Compare first block with others
        first_lines = blocks[0]["lines"]
        similarities = []

        for block in blocks[1:]:
            other_lines = block["lines"]
            similarity = self._lines_similarity(first_lines, other_lines)
            similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 100.0

    def _lines_similarity(self, lines1: List[str], lines2: List[str]) -> float:
        """Calculate similarity between two line lists."""
        if len(lines1) != len(lines2):
            return 0.0

        matches = 0
        for l1, l2 in zip(lines1, lines2):
            if l1.strip() == l2.strip():
                matches += 1

        return (matches / len(lines1)) * 100.0 if lines1 else 0.0

