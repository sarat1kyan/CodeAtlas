"""Main CLI interface for CodeAtlas."""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from codeatlas import __version__
from codeatlas.cleanup import CleanupEngine
from codeatlas.comment_editor import CommentEditor
from codeatlas.comment_parser import Comment, CommentParser
from codeatlas.config import Config
from codeatlas.code_quality import CodeQualityAnalyzer
from codeatlas.dependency_checker import DependencyChecker
from codeatlas.export import Exporter
from codeatlas.git_integration import GitIntegration
from codeatlas.language_detector import LanguageDetector
from codeatlas.license_checker import LicenseChecker
from codeatlas.plugin_system import PluginManager
from codeatlas.scanner import CodebaseScanner, ScanResult
from codeatlas.security_scanner import SecurityScanner
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
    from rich.panel import Panel
    from rich.text import Text
    
    version_text = Text()
    version_text.append("CodeAtlas ", style="bold cyan")
    version_text.append(f"v{__version__}", style="bold green")
    
    console.print()
    console.print(Panel.fit(
        version_text,
        border_style="cyan",
        title="[bold]Version[/bold]"
    ))
    console.print()


@app.command()
def scan(
    path: Path = typer.Argument(..., help="Path to scan"),
    skip_gitignored: bool = typer.Option(False, "--skip-gitignored", help="Skip gitignored files"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json, yaml"),
    include_security: bool = typer.Option(False, "--security", help="Include security scan"),
    include_dependencies: bool = typer.Option(False, "--dependencies", help="Include dependency check"),
    include_quality: bool = typer.Option(False, "--quality", help="Include code quality analysis"),
    include_licenses: bool = typer.Option(False, "--licenses", help="Include license check"),
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

    # Additional scans if requested
    security_result = None
    dependency_result = None
    quality_result = None
    license_result = None
    
    if include_security:
        console.print()
        console.print("[cyan]🔒 Running security scan...[/cyan]")
        security_scanner = SecurityScanner(path)
        security_result = security_scanner.scan()
        
        if security_result.total_issues > 0:
            console.print(f"[red]⚠️  Found {security_result.total_issues} security issues[/red]")
        else:
            console.print("[green]✅ No security issues found[/green]")
    
    if include_dependencies:
        console.print()
        console.print("[cyan]📦 Checking dependencies...[/cyan]")
        dependency_checker = DependencyChecker(path)
        dependency_result = dependency_checker.check()
        
        if dependency_result.outdated_count > 0:
            console.print(f"[yellow]⚠️  {dependency_result.outdated_count} outdated dependencies[/yellow]")
        else:
            console.print("[green]✅ All dependencies up to date[/green]")
    
    if include_quality:
        console.print()
        console.print("[cyan]📊 Analyzing code quality...[/cyan]")
        quality_analyzer = CodeQualityAnalyzer(path)
        quality_result = quality_analyzer.analyze()
        
        if quality_result.average_complexity > 10:
            console.print(f"[yellow]⚠️  High average complexity: {quality_result.average_complexity:.1f}[/yellow]")
        else:
            console.print(f"[green]✅ Code quality looks good (complexity: {quality_result.average_complexity:.1f})[/green]")
    
    if include_licenses:
        console.print()
        console.print("[cyan]📜 Checking licenses...[/cyan]")
        license_checker = LicenseChecker(path)
        license_result = license_checker.check()
        
        if license_result.incompatible_licenses:
            console.print(f"[red]⚠️  {len(license_result.incompatible_licenses)} incompatible licenses[/red]")
        else:
            console.print("[green]✅ No license conflicts found[/green]")
    
    # Save to output file if specified
    if output and format == "table":
        exporter = Exporter()
        export_data = {
            "scan": {
                "base_path": str(scan_result.base_path),
                "total_files": scan_result.total_files,
                "total_dirs": scan_result.total_dirs,
                "total_size_bytes": scan_result.total_size_bytes,
                "total_lines": scan_result.total_lines,
                "total_blank": scan_result.total_blank,
                "total_comments": scan_result.total_comments,
                "total_code": scan_result.total_code,
                "per_language": scan_result.per_language,
            },
        }
        
        if security_result:
            export_data["security"] = {
                "total_issues": security_result.total_issues,
                "issues_by_severity": security_result.issues_by_severity,
                "dependency_vulnerabilities": security_result.dependency_vulnerabilities,
            }
        
        if dependency_result:
            export_data["dependencies"] = {
                "total_dependencies": dependency_result.total_dependencies,
                "outdated_count": dependency_result.outdated_count,
                "package_manager": dependency_result.package_manager,
            }
        
        if quality_result:
            export_data["quality"] = {
                "average_complexity": quality_result.average_complexity,
                "average_maintainability": quality_result.average_maintainability,
                "total_files_analyzed": quality_result.total_files_analyzed,
            }
        
        if license_result:
            export_data["licenses"] = {
                "project_license": license_result.project_license.name if license_result.project_license else None,
                "incompatible_count": len(license_result.incompatible_licenses),
                "unlicensed_count": len(license_result.unlicensed_dependencies),
            }
        
        import json
        output.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"[green]Also saved comprehensive JSON to {output}[/green]")


def _display_scan_table(scan_result: ScanResult) -> None:
    """Display scan results in a table."""
    from rich.panel import Panel
    from rich.columns import Columns
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 CodeAtlas Scan Results[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    # Summary with better formatting
    summary_table = Table(
        title="[bold green]📈 Summary Statistics[/bold green]",
        show_header=True,
        header_style="bold bright_cyan",
        border_style="cyan",
        title_style="bold green"
    )
    summary_table.add_column("Metric", style="bold cyan", width=20)
    summary_table.add_column("Value", style="bright_green", justify="right", width=15)

    summary_table.add_row("📁 Total Files", f"[bold]{scan_result.total_files:,}[/bold]")
    summary_table.add_row("📂 Directories", f"[bold]{scan_result.total_dirs:,}[/bold]")
    summary_table.add_row("💾 Total Size", f"[bold]{_format_size(scan_result.total_size_bytes)}[/bold]")
    summary_table.add_row("📝 Total Lines", f"[bold]{scan_result.total_lines:,}[/bold]")
    summary_table.add_row("⚪ Blank Lines", f"{scan_result.total_blank:,}")
    summary_table.add_row("💬 Comment Lines", f"[bold yellow]{scan_result.total_comments:,}[/bold yellow]")
    summary_table.add_row("💻 Code Lines", f"[bold green]{scan_result.total_code:,}[/bold green]")

    console.print(summary_table)

    # Per-language with improved design
    if scan_result.per_language:
        lang_table = Table(
            title="[bold blue]🌐 Per-Language Statistics[/bold blue]",
            show_header=True,
            header_style="bold bright_blue",
            border_style="blue",
            title_style="bold blue"
        )
        lang_table.add_column("Language", style="bold cyan", width=20)
        lang_table.add_column("Files", justify="right", style="bright_white", width=10)
        lang_table.add_column("Lines", justify="right", style="white", width=12)
        lang_table.add_column("Code", justify="right", style="green", width=12)
        lang_table.add_column("Comments", justify="right", style="yellow", width=12)
        lang_table.add_column("Size", justify="right", style="dim white", width=12)

        for lang, stats in sorted(
            scan_result.per_language.items(), key=lambda x: x[1]["code"], reverse=True
        ):
            # Add emoji based on language
            lang_emoji = {
                "Python": "🐍", "JavaScript": "🟨", "TypeScript": "🔷", "Java": "☕",
                "C": "🔵", "C++": "🔷", "C#": "💜", "Go": "🐹", "Rust": "🦀",
                "Ruby": "💎", "PHP": "🐘", "Swift": "🐦", "Kotlin": "🔶",
            }.get(lang, "📄")
            
            lang_table.add_row(
                f"{lang_emoji} {lang}",
                f"{stats['files']:,}",
                f"{stats['lines']:,}",
                f"[green]{stats['code']:,}[/green]",
                f"[yellow]{stats['comments']:,}[/yellow]",
                _format_size(stats["bytes"]),
            )

        console.print()
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
    from rich.panel import Panel
    
    generator = TreeGenerator()
    
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]🌳 Project Tree: {path.name}[/bold cyan]",
        border_style="cyan"
    ))
    console.print()

    if format == "ascii":
        tree_str = generator.generate_ascii_tree(path, max_depth, include_files, include_size)
        if output:
            output.write_text(tree_str, encoding="utf-8")
            console.print(f"[green]✅ Tree saved to {output}[/green]")
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
            console.print(f"[green]✅ Tree saved to {output}[/green]")
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
        console.print(f"\n[bold cyan]🚀 Launching TUI with {len(filtered)} comments...[/bold cyan]\n")
        # Pass filtered comments to TUI by updating scan_result
        # Create a modified scan result with only filtered comments
        from codeatlas.scanner import ScanResult as ScanResultType
        from codeatlas.scanner import FileStats
        
        # Group filtered comments by file - use relative paths for matching
        filtered_by_file: Dict[str, List[Comment]] = {}
        base_path_str = str(scan_result.base_path)
        
        for comment in filtered:
            # Normalize file path for matching
            comment_path = comment.file_path
            # Try to match with relative paths in per_file
            matched = False
            for rel_path, file_stats in scan_result.per_file.items():
                # Check if comment path matches (could be absolute or relative)
                if comment_path.endswith(rel_path) or rel_path in comment_path:
                    if rel_path not in filtered_by_file:
                        filtered_by_file[rel_path] = []
                    filtered_by_file[rel_path].append(comment)
                    matched = True
                    break
            
            # If no match found, use the comment's file path directly
            if not matched:
                key = comment_path.replace(base_path_str, "").lstrip("/\\")
                if not key:
                    key = Path(comment_path).name
                if key not in filtered_by_file:
                    filtered_by_file[key] = []
                filtered_by_file[key].append(comment)
        
        # Create new per_file dict with filtered comments
        filtered_per_file: Dict[str, FileStats] = {}
        for file_path, file_comments in filtered_by_file.items():
            # Get original file stats if available
            if file_path in scan_result.per_file:
                orig_stats = scan_result.per_file[file_path]
                # Create new stats with filtered comments
                filtered_per_file[file_path] = FileStats(
                    path=orig_stats.path,
                    size_bytes=orig_stats.size_bytes,
                    total_lines=orig_stats.total_lines,
                    blank_lines=orig_stats.blank_lines,
                    comment_lines=len(file_comments),
                    code_lines=orig_stats.code_lines,
                    language=orig_stats.language,
                    comments=file_comments,
                    is_binary=orig_stats.is_binary,
                )
            else:
                # Create new stats from comments
                filtered_per_file[file_path] = FileStats(
                    path=file_path,
                    size_bytes=0,
                    total_lines=0,
                    blank_lines=0,
                    comment_lines=len(file_comments),
                    code_lines=0,
                    language=file_comments[0].language if file_comments else None,
                    comments=file_comments,
                    is_binary=False,
                )
        
        # Create filtered scan result
        filtered_scan_result = ScanResultType(
            base_path=scan_result.base_path,
            total_files=len(filtered_per_file),
            total_dirs=scan_result.total_dirs,
            total_size_bytes=sum(s.size_bytes for s in filtered_per_file.values()),
            total_lines=sum(s.total_lines for s in filtered_per_file.values()),
            total_blank=sum(s.blank_lines for s in filtered_per_file.values()),
            total_comments=len(filtered),
            total_code=sum(s.code_lines for s in filtered_per_file.values()),
            per_language=scan_result.per_language,
            per_file=filtered_per_file,
            git_info=scan_result.git_info,
        )
        launch_tui(filtered_scan_result)
    else:
        # Display in table with improved design
        from rich.panel import Panel
        
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]💬 Comments Found: {len(filtered)}[/bold cyan]",
            border_style="cyan"
        ))
        console.print()
        
        if not filtered:
            console.print("[yellow]⚠️  No comments found matching the criteria.[/yellow]")
            console.print("[dim]Try adjusting your filters or scanning a different directory.[/dim]")
        else:
            table = Table(
                title=f"[bold green]📋 Comment List ({len(filtered)} total)[/bold green]",
                show_header=True,
                header_style="bold bright_cyan",
                border_style="cyan",
                title_style="bold green",
                show_lines=True
            )
            table.add_column("File", style="cyan", width=30, overflow="ellipsis")
            table.add_column("Line", justify="right", style="bright_white", width=6)
            table.add_column("Language", style="green", width=12)
            table.add_column("Content", style="yellow", width=50, overflow="ellipsis")

            for comment in filtered[:100]:  # Limit display
                file_display = Path(comment.file_path).name
                if len(file_display) > 28:
                    file_display = file_display[:25] + "..."
                
                preview = comment.content[:47] + "..." if len(comment.content) > 47 else comment.content
                table.add_row(
                    file_display,
                    str(comment.line_number),
                    comment.language or "Unknown",
                    preview,
                )

            console.print(table)
            if len(filtered) > 100:
                console.print(f"\n[yellow]⚠️  Showing first 100 of {len(filtered)} comments[/yellow]")
                console.print("[dim]Use --tui for full interactive view or --output to export all[/dim]")

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

    from rich.panel import Panel
    from rich.syntax import Syntax
    
    if diff:
        console.print()
        console.print(Panel.fit(
            "[bold cyan]📝 Diff Preview[/bold cyan]",
            border_style="cyan"
        ))
        console.print()
        # Use syntax highlighting for diff
        syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
        console.print(syntax)
        console.print()
        if not apply and not dry_run:
            console.print("[yellow]⚠️  Use --apply to apply changes[/yellow]")
        elif dry_run:
            console.print("[yellow]🔍 DRY RUN - No changes applied[/yellow]")
        else:
            console.print("[green]✅ Changes applied successfully[/green]")


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

    from rich.panel import Panel
    from rich.progress import track
    
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]🧹 Code Cleanup[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    console.print(f"[cyan]📁 Found {len(text_files)} files to process[/cyan]\n")
    
    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No files will be modified[/yellow]\n")

    modified_count = 0
    for file_path in track(text_files, description="Cleaning files..."):
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
            if not dry_run:
                console.print(f"[green]✅ Modified: {file_path}[/green]")
            else:
                console.print(f"[yellow]🔍 Would modify: {file_path}[/yellow]")

    console.print()
    if dry_run:
        console.print(f"[bold yellow]🔍 Would modify {modified_count} files (dry run)[/bold yellow]")
    else:
        console.print(f"[bold green]✅ Modified {modified_count} files[/bold green]")


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

    from rich.panel import Panel
    
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]📤 Exporting Scan Results[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    exporter = Exporter()

    if format == "json":
        exporter.export_json(scan_result, output, pretty=True)
        console.print(f"[green]✅ Exported JSON report to {output}[/green]")
    elif format == "yaml":
        exporter.export_yaml(scan_result, output)
        console.print(f"[green]✅ Exported YAML report to {output}[/green]")
    elif format == "markdown":
        exporter.export_markdown(scan_result, output)
        console.print(f"[green]✅ Exported Markdown report to {output}[/green]")
    elif format == "csv":
        exporter.export_csv(scan_result, output)
        console.print(f"[green]✅ Exported CSV report to {output}[/green]")
    else:
        console.print(f"[red]❌ Error: Unknown format {format}[/red]")
        console.print("[yellow]Supported formats: json, yaml, markdown, csv[/yellow]")
        raise typer.Exit(1)


@app.command()
def security(
    path: Path = typer.Argument(..., help="Path to scan for security issues"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
):
    """Scan codebase for security vulnerabilities and issues."""
    from rich.panel import Panel
    from rich.progress import SpinnerColumn, TextColumn
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔒 Security Scan[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    scanner = SecurityScanner(path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Scanning for security issues...", total=None)
        result = scanner.scan()
    
    # Display results
    console.print()
    
    # Summary
    summary_table = Table(
        title="[bold red]🛡️ Security Summary[/bold red]",
        show_header=True,
        header_style="bold bright_red",
        border_style="red",
    )
    summary_table.add_column("Metric", style="bold cyan", width=25)
    summary_table.add_column("Value", style="bright_white", justify="right", width=15)
    
    summary_table.add_row("Total Issues", f"[bold]{result.total_issues}[/bold]")
    summary_table.add_row("Critical", f"[bold red]{result.issues_by_severity.get('critical', 0)}[/bold red]")
    summary_table.add_row("High", f"[red]{result.issues_by_severity.get('high', 0)}[/red]")
    summary_table.add_row("Medium", f"[yellow]{result.issues_by_severity.get('medium', 0)}[/yellow]")
    summary_table.add_row("Low", f"[dim white]{result.issues_by_severity.get('low', 0)}[/dim white]")
    summary_table.add_row("Dependency Vulns", f"[bold yellow]{len(result.dependency_vulnerabilities)}[/bold yellow]")
    
    console.print(summary_table)
    
    # Show issues
    if result.issues:
        console.print()
        issues_table = Table(
            title="[bold yellow]⚠️ Security Issues[/bold yellow]",
            show_header=True,
            header_style="bold bright_yellow",
            border_style="yellow",
        )
        issues_table.add_column("Severity", width=10)
        issues_table.add_column("File", style="cyan", width=30, overflow="ellipsis")
        issues_table.add_column("Line", justify="right", width=6)
        issues_table.add_column("Issue", style="white", width=50, overflow="ellipsis")
        
        for issue in result.issues[:50]:  # Limit display
            severity_color = {
                "critical": "bold red",
                "high": "red",
                "medium": "yellow",
                "low": "dim white",
            }.get(issue.severity.lower(), "white")
            
            file_display = Path(issue.file_path).name
            if len(file_display) > 28:
                file_display = file_display[:25] + "..."
            
            issues_table.add_row(
                f"[{severity_color}]{issue.severity.upper()}[/{severity_color}]",
                file_display,
                str(issue.line_number) if issue.line_number else "-",
                issue.description[:47] + "..." if len(issue.description) > 47 else issue.description,
            )
        
        console.print(issues_table)
        if len(result.issues) > 50:
            console.print(f"\n[yellow]⚠️  Showing first 50 of {len(result.issues)} issues[/yellow]")
    
    # Dependency vulnerabilities
    if result.dependency_vulnerabilities:
        console.print()
        vuln_table = Table(
            title="[bold red]🔴 Dependency Vulnerabilities[/bold red]",
            show_header=True,
            header_style="bold bright_red",
            border_style="red",
        )
        vuln_table.add_column("Package", style="cyan", width=25)
        vuln_table.add_column("Version", width=15)
        vuln_table.add_column("Severity", width=10)
        vuln_table.add_column("Advisory", style="white", width=40, overflow="ellipsis")
        
        for vuln in result.dependency_vulnerabilities[:30]:
            severity = vuln.get("severity", "unknown").lower()
            severity_color = {
                "critical": "bold red",
                "high": "red",
                "medium": "yellow",
                "low": "dim white",
            }.get(severity, "white")
            
            vuln_table.add_row(
                vuln.get("package", "unknown"),
                vuln.get("installed_version", "-"),
                f"[{severity_color}]{severity.upper()}[/{severity_color}]",
                vuln.get("advisory", "")[:37] + "..." if len(vuln.get("advisory", "")) > 37 else vuln.get("advisory", ""),
            )
        
        console.print(vuln_table)
        if len(result.dependency_vulnerabilities) > 30:
            console.print(f"\n[yellow]⚠️  Showing first 30 of {len(result.dependency_vulnerabilities)} vulnerabilities[/yellow]")
    
    # Tools used
    if result.scan_tools:
        console.print(f"\n[dim]Tools used: {', '.join(result.scan_tools)}[/dim]")
    
    # Export if requested
    if output:
        import json
        export_data = {
            "total_issues": result.total_issues,
            "issues_by_severity": result.issues_by_severity,
            "issues": [
                {
                    "severity": issue.severity,
                    "rule_id": issue.rule_id,
                    "description": issue.description,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "cwe_id": issue.cwe_id,
                }
                for issue in result.issues
            ],
            "dependency_vulnerabilities": result.dependency_vulnerabilities,
            "scan_tools": result.scan_tools,
        }
        output.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✅ Exported to {output}[/green]")


@app.command()
def dependencies(
    path: Path = typer.Argument(..., help="Path to check dependencies"),
    check_updates: bool = typer.Option(True, "--check-updates/--no-check-updates", help="Check for outdated packages"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
):
    """Check project dependencies for updates and issues."""
    from rich.panel import Panel
    from rich.progress import SpinnerColumn, TextColumn
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📦 Dependency Check[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    checker = DependencyChecker(path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Checking dependencies...", total=None)
        result = checker.check()
    
    console.print()
    
    # Summary
    summary_table = Table(
        title="[bold green]📊 Dependency Summary[/bold green]",
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
    )
    summary_table.add_column("Metric", style="bold cyan", width=25)
    summary_table.add_column("Value", style="bright_white", justify="right", width=15)
    
    summary_table.add_row("Total Dependencies", f"[bold]{result.total_dependencies}[/bold]")
    summary_table.add_row("Outdated", f"[yellow]{result.outdated_count}[/yellow]")
    summary_table.add_row("Up to Date", f"[green]{result.total_dependencies - result.outdated_count}[/green]")
    summary_table.add_row("Package Manager", result.package_manager or "Unknown")
    summary_table.add_row("Lock File", "✅ Yes" if result.lock_file_exists else "❌ No")
    
    console.print(summary_table)
    
    # Outdated packages
    if result.outdated_count > 0:
        console.print()
        outdated_table = Table(
            title="[bold yellow]⚠️ Outdated Dependencies[/bold yellow]",
            show_header=True,
            header_style="bold bright_yellow",
            border_style="yellow",
        )
        outdated_table.add_column("Package", style="cyan", width=30)
        outdated_table.add_column("Current", width=15)
        outdated_table.add_column("Latest", style="green", width=15)
        
        for dep in result.dependencies:
            if dep.is_outdated:
                outdated_table.add_row(
                    dep.name,
                    dep.version,
                    dep.latest_version or "unknown",
                )
        
        console.print(outdated_table)
    
    # All dependencies
    if result.dependencies:
        console.print()
        deps_table = Table(
            title="[bold blue]📋 All Dependencies[/bold blue]",
            show_header=True,
            header_style="bold bright_blue",
            border_style="blue",
        )
        deps_table.add_column("Package", style="cyan", width=30)
        deps_table.add_column("Version", width=15)
        deps_table.add_column("Status", width=12)
        deps_table.add_column("License", width=20)
        
        for dep in result.dependencies[:50]:
            status = "[yellow]Outdated[/yellow]" if dep.is_outdated else "[green]Up to date[/green]"
            deps_table.add_row(
                dep.name,
                dep.version,
                status,
                dep.license or "Unknown",
            )
        
        console.print(deps_table)
        if len(result.dependencies) > 50:
            console.print(f"\n[yellow]⚠️  Showing first 50 of {len(result.dependencies)} dependencies[/yellow]")
    
    # Export if requested
    if output:
        import json
        export_data = {
            "total_dependencies": result.total_dependencies,
            "outdated_count": result.outdated_count,
            "package_manager": result.package_manager,
            "lock_file_exists": result.lock_file_exists,
            "dependencies": [
                {
                    "name": dep.name,
                    "version": dep.version,
                    "latest_version": dep.latest_version,
                    "is_outdated": dep.is_outdated,
                    "license": dep.license,
                }
                for dep in result.dependencies
            ],
        }
        output.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✅ Exported to {output}[/green]")


@app.command()
def quality(
    path: Path = typer.Argument(..., help="Path to analyze code quality"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
):
    """Analyze code quality, complexity, and maintainability."""
    from rich.panel import Panel
    from rich.progress import SpinnerColumn, TextColumn
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📊 Code Quality Analysis[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    analyzer = CodeQualityAnalyzer(path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Analyzing code quality...", total=None)
        result = analyzer.analyze()
    
    console.print()
    
    # Summary
    summary_table = Table(
        title="[bold green]📈 Quality Summary[/bold green]",
        show_header=True,
        header_style="bold bright_green",
        border_style="green",
    )
    summary_table.add_column("Metric", style="bold cyan", width=25)
    summary_table.add_column("Value", style="bright_white", justify="right", width=15)
    
    summary_table.add_row("Files Analyzed", f"[bold]{result.total_files_analyzed}[/bold]")
    summary_table.add_row("Avg Complexity", f"[bold]{result.average_complexity:.1f}[/bold]")
    summary_table.add_row("Avg Maintainability", f"[bold]{result.average_maintainability:.1f}[/bold]")
    
    # Complexity breakdown
    if result.files_by_complexity:
        console.print()
        complexity_table = Table(
            title="[bold blue]🔍 Complexity Distribution[/bold blue]",
            show_header=True,
            header_style="bold bright_blue",
            border_style="blue",
        )
        complexity_table.add_column("Complexity Level", style="bold cyan", width=20)
        complexity_table.add_column("File Count", justify="right", width=15)
        complexity_table.add_column("Files", style="dim white", width=50, overflow="ellipsis")
        
        for level in ["low", "medium", "high", "very_high"]:
            files = result.files_by_complexity.get(level, [])
            if files:
                color = {
                    "low": "green",
                    "medium": "yellow",
                    "high": "red",
                    "very_high": "bold red",
                }.get(level, "white")
                
                file_list = ", ".join([Path(f).name for f in files[:5]])
                if len(files) > 5:
                    file_list += f" ... (+{len(files) - 5} more)"
                
                complexity_table.add_row(
                    f"[{color}]{level.upper()}[/{color}]",
                    str(len(files)),
                    file_list,
                )
        
        console.print(complexity_table)
    
    # Top complex files
    if result.per_file_metrics:
        console.print()
        top_complex = sorted(
            result.per_file_metrics.items(),
            key=lambda x: x[1].complexity,
            reverse=True,
        )[:10]
        
        complex_table = Table(
            title="[bold red]⚠️ Most Complex Files[/bold red]",
            show_header=True,
            header_style="bold bright_red",
            border_style="red",
        )
        complex_table.add_column("File", style="cyan", width=30, overflow="ellipsis")
        complex_table.add_column("Complexity", justify="right", width=12)
        complex_table.add_column("Maintainability", justify="right", width=15)
        complex_table.add_column("Lines", justify="right", width=10)
        
        for file_path, metrics in top_complex:
            maintainability_color = "green" if metrics.maintainability_index > 70 else "yellow" if metrics.maintainability_index > 50 else "red"
            complex_table.add_row(
                Path(file_path).name,
                str(metrics.complexity),
                f"[{maintainability_color}]{metrics.maintainability_index:.1f}[/{maintainability_color}]",
                str(metrics.lines_of_code),
            )
        
        console.print(complex_table)
    
    # Export if requested
    if output:
        import json
        export_data = {
            "total_files_analyzed": result.total_files_analyzed,
            "average_complexity": result.average_complexity,
            "average_maintainability": result.average_maintainability,
            "files_by_complexity": result.files_by_complexity,
            "per_file_metrics": {
                file_path: {
                    "complexity": metrics.complexity,
                    "maintainability_index": metrics.maintainability_index,
                    "lines_of_code": metrics.lines_of_code,
                    "cyclomatic_complexity": metrics.cyclomatic_complexity,
                    "cognitive_complexity": metrics.cognitive_complexity,
                    "technical_debt": metrics.technical_debt,
                }
                for file_path, metrics in result.per_file_metrics.items()
            },
        }
        output.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✅ Exported to {output}[/green]")


@app.command()
def licenses(
    path: Path = typer.Argument(..., help="Path to check licenses"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for JSON report"),
):
    """Check licenses for project and dependencies."""
    from rich.panel import Panel
    from rich.progress import SpinnerColumn, TextColumn
    
    console.print()
    console.print(Panel.fit(
        "[bold cyan]📜 License Check[/bold cyan]",
        border_style="cyan"
    ))
    console.print()
    
    checker = LicenseChecker(path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("[cyan]Checking licenses...", total=None)
        result = checker.check()
    
    console.print()
    
    # Project license
    if result.project_license:
        console.print("[bold green]📄 Project License:[/bold green]")
        license_table = Table(show_header=False, box=None, padding=(0, 2))
        license_table.add_column(style="cyan", width=20)
        license_table.add_column(style="white")
        
        license_table.add_row("Name:", result.project_license.name)
        if result.project_license.spdx_id:
            license_table.add_row("SPDX ID:", result.project_license.spdx_id)
        license_table.add_row("OSI Approved:", "✅ Yes" if result.project_license.is_osi_approved else "❌ No")
        license_table.add_row("FSF Approved:", "✅ Yes" if result.project_license.is_fsf_approved else "❌ No")
        license_table.add_row("Risk Level:", result.project_license.risk_level.upper())
        
        console.print(license_table)
        console.print()
    
    # Summary
    summary_table = Table(
        title="[bold blue]📊 License Summary[/bold blue]",
        show_header=True,
        header_style="bold bright_blue",
        border_style="blue",
    )
    summary_table.add_column("Metric", style="bold cyan", width=25)
    summary_table.add_column("Value", style="bright_white", justify="right", width=15)
    
    summary_table.add_row("Dependencies Checked", f"[bold]{result.total_dependencies_checked}[/bold]")
    summary_table.add_row("Incompatible", f"[red]{len(result.incompatible_licenses)}[/red]")
    summary_table.add_row("Unlicensed", f"[yellow]{len(result.unlicensed_dependencies)}[/yellow]")
    
    console.print(summary_table)
    
    # Incompatible licenses
    if result.incompatible_licenses:
        console.print()
        console.print("[bold red]⚠️ Incompatible Licenses:[/bold red]")
        for incompatible in result.incompatible_licenses:
            console.print(f"  [red]• {incompatible}[/red]")
    
    # Unlicensed dependencies
    if result.unlicensed_dependencies:
        console.print()
        console.print("[bold yellow]⚠️ Unlicensed Dependencies:[/bold yellow]")
        for unlicensed in result.unlicensed_dependencies:
            console.print(f"  [yellow]• {unlicensed}[/yellow]")
    
    # Dependency licenses
    if result.dependency_licenses:
        console.print()
        license_table = Table(
            title="[bold green]📋 Dependency Licenses[/bold green]",
            show_header=True,
            header_style="bold bright_green",
            border_style="green",
        )
        license_table.add_column("Package", style="cyan", width=30)
        license_table.add_column("License", width=20)
        license_table.add_column("OSI Approved", width=12)
        license_table.add_column("Risk", width=10)
        
        for dep_name, license_info in list(result.dependency_licenses.items())[:50]:
            risk_color = {
                "low": "green",
                "medium": "yellow",
                "high": "red",
                "unknown": "dim white",
            }.get(license_info.risk_level, "white")
            
            license_table.add_row(
                dep_name,
                license_info.name,
                "✅" if license_info.is_osi_approved else "❌",
                f"[{risk_color}]{license_info.risk_level.upper()}[/{risk_color}]",
            )
        
        console.print(license_table)
        if len(result.dependency_licenses) > 50:
            console.print(f"\n[yellow]⚠️  Showing first 50 of {len(result.dependency_licenses)} dependencies[/yellow]")
    
    # Export if requested
    if output:
        import json
        export_data = {
            "project_license": {
                "name": result.project_license.name,
                "spdx_id": result.project_license.spdx_id,
                "is_osi_approved": result.project_license.is_osi_approved,
                "is_fsf_approved": result.project_license.is_fsf_approved,
                "risk_level": result.project_license.risk_level,
            } if result.project_license else None,
            "total_dependencies_checked": result.total_dependencies_checked,
            "incompatible_licenses": result.incompatible_licenses,
            "unlicensed_dependencies": result.unlicensed_dependencies,
            "dependency_licenses": {
                dep_name: {
                    "name": info.name,
                    "spdx_id": info.spdx_id,
                    "is_osi_approved": info.is_osi_approved,
                    "is_fsf_approved": info.is_fsf_approved,
                    "risk_level": info.risk_level,
                }
                for dep_name, info in result.dependency_licenses.items()
            },
        }
        output.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        console.print(f"\n[green]✅ Exported to {output}[/green]")


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
