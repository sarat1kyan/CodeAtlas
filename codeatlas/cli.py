"""Main CLI interface for CodeAtlas."""

import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from codeatlas import __version__
from codeatlas.cleanup import CleanupEngine
from codeatlas.comment_editor import CommentEditor
from codeatlas.comment_parser import Comment, CommentParser
from codeatlas.config import Config
from codeatlas.export import Exporter
from codeatlas.git_integration import GitIntegration
from codeatlas.language_detector import LanguageDetector
from codeatlas.plugin_system import PluginManager
from codeatlas.scanner import CodebaseScanner, ScanResult
from codeatlas.tree_generator import TreeGenerator
from codeatlas.tui import launch_tui

app = typer.Typer(
    name="codeatlas",
    help="CodeAtlas - A production-ready CLI + TUI tool for codebase analysis and comment management",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Show version information."""
    console.print(f"CodeAtlas v{__version__}")


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Path to scan"),
    skip_gitignored: bool = typer.Option(False, "--skip-gitignored", help="Skip gitignored files"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, yaml"),
):
    """Scan a codebase and display statistics."""
    config = Config(path)
    scanner = CodebaseScanner(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        scan_result = scanner.scan(path, skip_gitignored=skip_gitignored, progress=progress)

    # Git integration
    git = GitIntegration(path)
    if git.is_git_repo():
        scan_result.git_info = git.get_git_info()
        if scan_result.git_info.get("status"):
            status = scan_result.git_info["status"]
            console.print("\n[bold]Git Status:[/bold]")
            console.print(f"  Modified: {len(status.get('modified', []))}")
            console.print(f"  Untracked: {len(status.get('untracked', []))}")
            console.print(f"  Added: {len(status.get('added', []))}")

    # Display results
    if format == "table":
        _display_scan_table(scan_result)
    elif format == "json":
        exporter = Exporter()
        exporter.export_json(scan_result, output or Path("scan_result.json"))
        console.print(f"[green]Exported to {output or 'scan_result.json'}[/green]")
    elif format == "yaml":
        exporter = Exporter()
        exporter.export_yaml(scan_result, output or Path("scan_result.yaml"))
        console.print(f"[green]Exported to {output or 'scan_result.yaml'}[/green]")

    # Save to output file if specified
    if output and format == "table":
        exporter = Exporter()
        exporter.export_json(scan_result, output)
        console.print(f"[green]Also saved JSON to {output}[/green]")


def _display_scan_table(scan_result: ScanResult) -> None:
    """Display scan results in a table."""
    console.print("\n[bold cyan]CodeAtlas Scan Results[/bold cyan]\n")

    # Summary
    table = Table(title="Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Files", f"{scan_result.total_files:,}")
    table.add_row("Total Directories", f"{scan_result.total_dirs:,}")
    table.add_row("Total Size", _format_size(scan_result.total_size_bytes))
    table.add_row("Total Lines", f"{scan_result.total_lines:,}")
    table.add_row("Blank Lines", f"{scan_result.total_blank:,}")
    table.add_row("Comment Lines", f"{scan_result.total_comments:,}")
    table.add_row("Code Lines", f"{scan_result.total_code:,}")

    console.print(table)

    # Per-language
    if scan_result.per_language:
        lang_table = Table(title="Per-Language Statistics", show_header=True, header_style="bold magenta")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Files", justify="right")
        lang_table.add_column("Lines", justify="right")
        lang_table.add_column("Code", justify="right")
        lang_table.add_column("Comments", justify="right")
        lang_table.add_column("Size", justify="right")

        for lang, stats in sorted(
            scan_result.per_language.items(), key=lambda x: x[1]["code"], reverse=True
        ):
            lang_table.add_row(
                lang,
                f"{stats['files']:,}",
                f"{stats['lines']:,}",
                f"{stats['code']:,}",
                f"{stats['comments']:,}",
                _format_size(stats["bytes"]),
            )

        console.print("\n")
        console.print(lang_table)


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


@app.command()
def tree(
    path: Path = typer.Argument(..., help="Path to generate tree for"),
    format: str = typer.Option("rich", "--format", "-f", help="Format: ascii, rich, markdown"),
    max_depth: Optional[int] = typer.Option(None, "--max-depth", "-d", help="Maximum depth"),
    include_files: bool = typer.Option(True, "--files/--no-files", help="Include files"),
    include_size: bool = typer.Option(False, "--size", help="Include file sizes"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Generate project tree."""
    generator = TreeGenerator()

    if format == "ascii":
        tree_str = generator.generate_ascii_tree(path, max_depth, include_files, include_size)
        if output:
            output.write_text(tree_str, encoding="utf-8")
            console.print(f"[green]Tree saved to {output}[/green]")
        else:
            console.print(tree_str)
    elif format == "rich":
        tree_obj = generator.generate_rich_tree(path, None, max_depth, include_files, include_size)
        console.print(tree_obj)
    elif format == "markdown":
        tree_str = generator.generate_markdown_tree(
            path, None, max_depth, include_files, include_size, collapsible=True
        )
        if output:
            output.write_text(tree_str, encoding="utf-8")
            console.print(f"[green]Tree saved to {output}[/green]")
        else:
            console.print(tree_str)


@app.command()
def comments(
    path: Path = typer.Argument(..., help="Path to scan for comments"),
    filter_file: Optional[str] = typer.Option(None, "--file", help="Filter by file path pattern"),
    filter_lang: Optional[str] = typer.Option(None, "--language", help="Filter by language"),
    filter_text: Optional[str] = typer.Option(None, "--text", help="Filter by text regex"),
    tui: bool = typer.Option(False, "--tui", help="Launch interactive TUI"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON"),
):
    """List and review comments in codebase."""
    config = Config(path)
    scanner = CodebaseScanner(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        scan_result = scanner.scan(path, progress=progress)

    # Collect all comments
    all_comments: List[Comment] = []
    for file_stats in scan_result.per_file.values():
        all_comments.extend(file_stats.comments)

    # Apply filters
    filtered = all_comments
    if filter_file:
        filtered = [c for c in filtered if filter_file in c.file_path]
    if filter_lang:
        filtered = [c for c in filtered if c.language == filter_lang]
    if filter_text:
        import re

        pattern = re.compile(filter_text, re.IGNORECASE)
        filtered = [c for c in filtered if pattern.search(c.content)]

    if tui:
        # Create temporary scan result with filtered comments
        # (simplified - in production would properly filter)
        launch_tui(scan_result)
    else:
        # Display in table
        table = Table(title=f"Comments ({len(filtered)} found)", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Line", justify="right")
        table.add_column("Language", style="green")
        table.add_column("Content", style="yellow")

        for comment in filtered[:100]:  # Limit display
            preview = comment.content[:60] + "..." if len(comment.content) > 60 else comment.content
            table.add_row(
                comment.file_path,
                str(comment.line_number),
                comment.language,
                preview,
            )

        console.print(table)
        if len(filtered) > 100:
            console.print(f"\n[yellow]Showing first 100 of {len(filtered)} comments[/yellow]")

        if output:
            import json

            comments_data = [
                {
                    "file": c.file_path,
                    "line": c.line_number,
                    "language": c.language,
                    "content": c.content,
                }
                for c in filtered
            ]
            output.write_text(json.dumps(comments_data, indent=2), encoding="utf-8")
            console.print(f"[green]Exported to {output}[/green]")


@app.command()
def edit(
    file_path: Path = typer.Argument(..., help="File path with optional line number (file:line)"),
    replace: Optional[str] = typer.Option(None, "--replace", help="New comment text"),
    delete: bool = typer.Option(False, "--delete", help="Delete comment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show diff without applying"),
    apply: bool = typer.Option(False, "--apply", help="Apply changes (required for non-dry-run)"),
):
    """Edit comments in files."""
    # Parse file:line format
    if ":" in str(file_path):
        parts = str(file_path).split(":", 1)
        file_path = Path(parts[0])
        line_number = int(parts[1])
    else:
        console.print("[red]Error: Must specify line number as file:line[/red]")
        raise typer.Exit(1)

    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)

    config = Config(file_path.parent)
    editor = CommentEditor(config)

    if delete:
        diff = editor.delete_comment(file_path, line_number, dry_run=dry_run or not apply)
    elif replace:
        diff = editor.edit_comment(file_path, line_number, replace, dry_run=dry_run or not apply)
    else:
        console.print("[red]Error: Must specify --replace or --delete[/red]")
        raise typer.Exit(1)

    if diff:
        console.print("\n[bold]Diff:[/bold]")
        console.print(diff)
        if not apply and not dry_run:
            console.print("\n[yellow]Use --apply to apply changes[/yellow]")


@app.command()
def cleanup(
    path: Path = typer.Argument(..., help="Path to clean up"),
    remove_trailing_spaces: bool = typer.Option(False, "--remove-trailing-spaces", help="Remove trailing spaces"),
    normalize_indentation: bool = typer.Option(False, "--normalize-indentation", help="Normalize indentation"),
    tab_width: int = typer.Option(4, "--tab-width", help="Tab width for indentation"),
    remove_duplicate_blanks: bool = typer.Option(False, "--remove-duplicate-blanks", help="Remove duplicate blank lines"),
    max_consecutive_blanks: int = typer.Option(2, "--max-blanks", help="Max consecutive blank lines"),
    remove_commented_code: bool = typer.Option(False, "--remove-commented-code", help="Remove commented code"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed"),
):
    """Clean up code files."""
    config = Config(path)
    cleanup_engine = CleanupEngine(config)

    # Find all text files
    text_files: List[Path] = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp"}:
                text_files.append(file_path)

    console.print(f"[cyan]Found {len(text_files)} files to process[/cyan]\n")

    modified_count = 0
    for file_path in text_files:
        result = cleanup_engine.cleanup_file(
            file_path,
            remove_trailing_spaces=remove_trailing_spaces,
            normalize_indentation=normalize_indentation,
            tab_width=tab_width,
            remove_duplicate_blanks=remove_duplicate_blanks,
            max_consecutive_blanks=max_consecutive_blanks,
            remove_commented_code=remove_commented_code,
            dry_run=dry_run,
        )

        if result and result["modified"]:
            modified_count += 1
            console.print(f"[green]Modified: {file_path}[/green]")

    console.print(f"\n[bold]Modified {modified_count} files[/bold]")


@app.command()
def export(
    path: Path = typer.Argument(..., help="Path to scan and export"),
    format: str = typer.Option("json", "--format", "-f", help="Format: json, yaml, markdown, csv"),
    output: Path = typer.Argument(..., help="Output file path"),
    skip_gitignored: bool = typer.Option(False, "--skip-gitignored", help="Skip gitignored files"),
):
    """Export scan results to various formats."""
    config = Config(path)
    scanner = CodebaseScanner(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        scan_result = scanner.scan(path, skip_gitignored=skip_gitignored, progress=progress)

    # Git integration
    git = GitIntegration(path)
    if git.is_git_repo():
        scan_result.git_info = git.get_git_info()

    exporter = Exporter()

    if format == "json":
        exporter.export_json(scan_result, output, pretty=True)
    elif format == "yaml":
        exporter.export_yaml(scan_result, output)
    elif format == "markdown":
        exporter.export_markdown(scan_result, output)
    elif format == "csv":
        exporter.export_csv(scan_result, output)
    else:
        console.print(f"[red]Error: Unknown format {format}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Exported to {output}[/green]")


@app.command()
def plugins(
    list_plugins: bool = typer.Option(False, "--list", help="List loaded plugins"),
    load: Optional[str] = typer.Option(None, "--load", help="Load a specific plugin"),
):
    """Manage plugins."""
    manager = PluginManager()

    if load:
        plugin_path = Path(f"codeatlas_plugins/{load}.py")
        if plugin_path.exists():
            manager.load_plugin(plugin_path)
        else:
            console.print(f"[red]Error: Plugin {load} not found[/red]")
            raise typer.Exit(1)
    elif list_plugins:
        plugins_info = manager.list_plugins()
        if plugins_info:
            table = Table(title="Loaded Plugins", show_header=True)
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="green")
            table.add_column("Author", style="yellow")

            for plugin in plugins_info:
                table.add_row(plugin["name"], plugin["version"], plugin["author"])

            console.print(table)
        else:
            console.print("[yellow]No plugins loaded[/yellow]")
    else:
        console.print("[yellow]Use --list to list plugins or --load to load a plugin[/yellow]")
