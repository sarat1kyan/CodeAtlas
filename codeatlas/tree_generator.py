"""Project tree generation with multiple output formats."""

from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.tree import Tree

from codeatlas.scanner import ScanResult

console = Console()


class TreeGenerator:
    """Generates project tree representations."""

    def __init__(self):
        """Initialize tree generator."""
        pass

    def generate_ascii_tree(
        self,
        base_path: Path,
        max_depth: Optional[int] = None,
        include_files: bool = True,
        include_size: bool = False,
    ) -> str:
        """Generate ASCII tree representation."""
        lines: List[str] = []
        self._build_ascii_tree(base_path, base_path, lines, "", max_depth, include_files, include_size)
        return "\n".join(lines)

    def _build_ascii_tree(
        self,
        root: Path,
        current: Path,
        lines: List[str],
        prefix: str,
        max_depth: Optional[int],
        include_files: bool,
        include_size: bool,
        depth: int = 0,
    ) -> None:
        """Recursively build ASCII tree."""
        if max_depth is not None and depth >= max_depth:
            return

        try:
            items = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            dirs = [p for p in items if p.is_dir() and not p.name.startswith(".")]
            files = [p for p in items if p.is_file()] if include_files else []

            all_items = dirs + files
            for i, item in enumerate(all_items):
                is_last = i == len(all_items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = prefix + ("    " if is_last else "│   ")

                name = item.name
                if include_size and item.is_file():
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    name = f"{name} ({size_str})"

                lines.append(prefix + current_prefix + name)

                if item.is_dir():
                    self._build_ascii_tree(
                        root, item, lines, next_prefix, max_depth, include_files, include_size, depth + 1
                    )
        except PermissionError:
            pass

    def generate_rich_tree(
        self,
        base_path: Path,
        scan_result: Optional[ScanResult] = None,
        max_depth: Optional[int] = None,
        include_files: bool = True,
        include_size: bool = False,
    ) -> Tree:
        """Generate Rich tree representation."""
        tree = Tree(f"[bold]{base_path.name}[/bold]")
        self._build_rich_tree(
            base_path, base_path, tree, scan_result, max_depth, include_files, include_size
        )
        return tree

    def _build_rich_tree(
        self,
        root: Path,
        current: Path,
        parent_node: Tree,
        scan_result: Optional[ScanResult],
        max_depth: Optional[int],
        include_files: bool,
        include_size: bool,
        depth: int = 0,
    ) -> None:
        """Recursively build Rich tree."""
        if max_depth is not None and depth >= max_depth:
            return

        try:
            items = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            dirs = [p for p in items if p.is_dir() and not p.name.startswith(".")]
            files = [p for p in items if p.is_file()] if include_files else []

            all_items = dirs + files
            for item in all_items:
                name = item.name
                label = name

                if include_size and item.is_file():
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    label = f"{name} [dim]({size_str})[/dim]"

                # Add stats if available
                if scan_result and item.is_file():
                    rel_path = str(item.relative_to(root))
                    if rel_path in scan_result.per_file:
                        stats = scan_result.per_file[rel_path]
                        label += f" [cyan]{stats.code_lines} lines[/cyan]"

                if item.is_dir():
                    node = parent_node.add(f"[bold blue]{label}[/bold blue]")
                    self._build_rich_tree(
                        root, item, node, scan_result, max_depth, include_files, include_size, depth + 1
                    )
                else:
                    parent_node.add(label)
        except PermissionError:
            pass

    def generate_markdown_tree(
        self,
        base_path: Path,
        scan_result: Optional[ScanResult] = None,
        max_depth: Optional[int] = None,
        include_files: bool = True,
        include_size: bool = False,
        collapsible: bool = True,
    ) -> str:
        """Generate Markdown tree representation."""
        lines: List[str] = []
        lines.append(f"# {base_path.name}\n")
        self._build_markdown_tree(
            base_path, base_path, lines, "", scan_result, max_depth, include_files, include_size, collapsible
        )
        return "\n".join(lines)

    def _build_markdown_tree(
        self,
        root: Path,
        current: Path,
        lines: List[str],
        prefix: str,
        scan_result: Optional[ScanResult],
        max_depth: Optional[int],
        include_files: bool,
        include_size: bool,
        collapsible: bool,
        depth: int = 0,
    ) -> None:
        """Recursively build Markdown tree."""
        if max_depth is not None and depth >= max_depth:
            return

        try:
            items = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            dirs = [p for p in items if p.is_dir() and not p.name.startswith(".")]
            files = [p for p in items if p.is_file()] if include_files else []

            all_items = dirs + files
            for i, item in enumerate(all_items):
                is_last = i == len(all_items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = prefix + ("    " if is_last else "│   ")

                name = item.name
                label = name

                if include_size and item.is_file():
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    label = f"{name} ({size_str})"

                # Add stats if available
                if scan_result and item.is_file():
                    rel_path = str(item.relative_to(root))
                    if rel_path in scan_result.per_file:
                        stats = scan_result.per_file[rel_path]
                        label += f" - {stats.code_lines} lines"

                if collapsible and item.is_dir():
                    lines.append(f"{prefix}{current_prefix}<details><summary>{name}</summary>")
                    lines.append("")
                    self._build_markdown_tree(
                        root,
                        item,
                        lines,
                        next_prefix,
                        scan_result,
                        max_depth,
                        include_files,
                        include_size,
                        collapsible,
                        depth + 1,
                    )
                    lines.append("</details>")
                else:
                    lines.append(f"{prefix}{current_prefix}{label}")

                if item.is_dir() and not collapsible:
                    self._build_markdown_tree(
                        root,
                        item,
                        lines,
                        next_prefix,
                        scan_result,
                        max_depth,
                        include_files,
                        include_size,
                        collapsible,
                        depth + 1,
                    )
        except PermissionError:
            pass

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

