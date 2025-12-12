"""Code cleanup operations (trailing spaces, indentation, etc.)."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console

from codeatlas.config import Config

console = Console()


class CleanupEngine:
    """Performs various code cleanup operations."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize cleanup engine."""
        self.config = config or Config()

    def remove_trailing_spaces(
        self, content: str, dry_run: bool = False
    ) -> Tuple[str, List[int]]:
        """
        Remove trailing spaces from lines.

        Returns:
            Tuple of (modified_content, list of modified line numbers)
        """
        lines = content.split("\n")
        modified_lines: List[int] = []
        new_lines: List[str] = []

        for i, line in enumerate(lines, 1):
            original = line
            cleaned = line.rstrip()
            if original != cleaned:
                modified_lines.append(i)
            new_lines.append(cleaned)

        new_content = "\n".join(new_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return new_content, modified_lines

    def normalize_indentation(
        self,
        content: str,
        tab_width: int = 4,
        convert_tabs_to_spaces: bool = True,
        dry_run: bool = False,
    ) -> Tuple[str, List[int]]:
        """
        Normalize indentation (tabs to spaces or vice versa).

        Returns:
            Tuple of (modified_content, list of modified line numbers)
        """
        lines = content.split("\n")
        modified_lines: List[int] = []
        new_lines: List[str] = []

        for i, line in enumerate(lines, 1):
            if convert_tabs_to_spaces:
                # Convert tabs to spaces
                new_line = line.expandtabs(tab_width)
                if new_line != line:
                    modified_lines.append(i)
                new_lines.append(new_line)
            else:
                # Convert spaces to tabs (heuristic)
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    tabs = leading_spaces // tab_width
                    spaces = leading_spaces % tab_width
                    new_line = "\t" * tabs + " " * spaces + line.lstrip()
                    if new_line != line:
                        modified_lines.append(i)
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)

        new_content = "\n".join(new_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return new_content, modified_lines

    def remove_duplicate_blank_lines(
        self, content: str, max_consecutive: int = 2, dry_run: bool = False
    ) -> Tuple[str, List[int]]:
        """
        Remove duplicate blank lines beyond max_consecutive.

        Returns:
            Tuple of (modified_content, list of modified line numbers)
        """
        lines = content.split("\n")
        modified_lines: List[int] = []
        new_lines: List[str] = []
        consecutive_blanks = 0

        for i, line in enumerate(lines, 1):
            if not line.strip():
                consecutive_blanks += 1
                if consecutive_blanks <= max_consecutive:
                    new_lines.append(line)
                else:
                    modified_lines.append(i)
            else:
                consecutive_blanks = 0
                new_lines.append(line)

        new_content = "\n".join(new_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return new_content, modified_lines

    def remove_commented_code(
        self, content: str, language: Optional[str] = None, dry_run: bool = False
    ) -> Tuple[str, List[int]]:
        """
        Heuristically detect and optionally remove commented-out code.

        Returns:
            Tuple of (modified_content, list of removed line numbers)
        """
        # This is a simplified heuristic - in production, this would be more sophisticated
        lines = content.split("\n")
        removed_lines: List[int] = []
        new_lines: List[str] = []

        code_indicators = [
            r"^\s*#\s*(def|class|if|for|while|return|import|from)\s+",
            r"^\s*//\s*(function|const|let|var|class|if|for|while)\s+",
            r"^\s*#\s*\w+\s*\(.*\)\s*:?\s*$",
        ]

        for i, line in enumerate(lines, 1):
            is_commented_code = False
            for pattern in code_indicators:
                if re.match(pattern, line, re.IGNORECASE):
                    is_commented_code = True
                    break

            if is_commented_code:
                removed_lines.append(i)
            else:
                new_lines.append(line)

        new_content = "\n".join(new_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return new_content, removed_lines

    def cleanup_file(
        self,
        file_path: Path,
        remove_trailing_spaces: bool = False,
        normalize_indentation: bool = False,
        tab_width: int = 4,
        convert_tabs_to_spaces: bool = True,
        remove_duplicate_blanks: bool = False,
        max_consecutive_blanks: int = 2,
        remove_commented_code: bool = False,
        dry_run: bool = False,
    ) -> Optional[Dict[str, any]]:
        """
        Apply all requested cleanup operations to a file.

        Returns:
            Dictionary with cleanup results or None if error
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            all_modified_lines: List[int] = []

            if remove_trailing_spaces:
                content, modified = self.remove_trailing_spaces(content, dry_run)
                all_modified_lines.extend(modified)

            if normalize_indentation:
                content, modified = self.normalize_indentation(
                    content, tab_width, convert_tabs_to_spaces, dry_run
                )
                all_modified_lines.extend(modified)

            if remove_duplicate_blanks:
                content, modified = self.remove_duplicate_blank_lines(
                    content, max_consecutive_blanks, dry_run
                )
                all_modified_lines.extend(modified)

            if remove_commented_code:
                language = None  # Could detect from file extension
                content, removed = self.remove_commented_code(content, language, dry_run)
                all_modified_lines.extend(removed)

            if not dry_run and content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return {
                "file": str(file_path),
                "modified": content != original_content,
                "modified_lines": sorted(set(all_modified_lines)),
            }
        except Exception as e:
            console.print(f"[red]Error cleaning up {file_path}: {e}[/red]")
            return None

