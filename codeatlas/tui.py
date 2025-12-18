"""Textual TUI for interactive comment review and editing."""

from pathlib import Path
from typing import List, Optional

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Horizontal, VerticalScroll
    from textual.widgets import DataTable, Footer, Header, Label, Static
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    # Dummy classes for type checking
    class App:
        pass
    class ComposeResult:
        pass
    class Binding:
        pass
    class DataTable:
        pass
    class RowSelected:
        pass

from codeatlas.comment_parser import Comment
from codeatlas.scanner import ScanResult
from rich.console import Console

console = Console()


if TEXTUAL_AVAILABLE:
    class CommentList(DataTable):
        """Widget displaying list of comments."""

        def __init__(self, comments: List[Comment], *args, **kwargs):
            """Initialize comment list."""
            super().__init__(*args, **kwargs)
            self.comments = comments
            self.cursor_type = "row"

        def on_mount(self) -> None:
            """Setup table on mount."""
            self.add_columns("File", "Line", "Language", "Preview")
            for idx, comment in enumerate(self.comments):
                preview = comment.content[:50] + "..." if len(comment.content) > 50 else comment.content
                # Create unique key from file path and line number
                unique_key = f"{comment.file_path}:{comment.line_number}:{idx}"
                self.add_row(
                    comment.file_path,
                    str(comment.line_number),
                    comment.language,
                    preview,
                    key=unique_key,
                )


    class CommentDetail(Static):
        """Widget displaying comment details."""

        def show_comment(self, comment: Comment) -> None:
            """Display a comment with context."""
            lines: List[str] = []
            lines.append(f"[bold]File:[/bold] {comment.file_path}")
            lines.append(f"[bold]Line:[/bold] {comment.line_number}")
            lines.append(f"[bold]Language:[/bold] {comment.language}")
            lines.append("")
            lines.append("[bold]Context Before:[/bold]")
            for line in comment.context_before:
                lines.append(f"  {line}")
            lines.append("")
            lines.append(f"[bold yellow]Comment:[/bold yellow]")
            lines.append(f"  {comment.content}")
            lines.append("")
            lines.append("[bold]Context After:[/bold]")
            for line in comment.context_after:
                lines.append(f"  {line}")

            self.update("\n".join(lines))


    class CommentTUI(App):
        """Textual TUI application for comment review."""

        CSS = """
        Screen {
            background: $surface;
        }
        
        #comment-list {
            width: 1fr;
            height: 1fr;
        }
        
        #comment-detail {
            width: 1fr;
            height: 1fr;
            border: solid $primary;
        }
        
        .sidebar {
            width: 30%;
            border-right: solid $primary;
        }
        
        .main {
            width: 70%;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("f", "filter", "Filter"),
            Binding("e", "edit", "Edit"),
            Binding("d", "delete", "Delete"),
            Binding("n", "next", "Next"),
            Binding("p", "previous", "Previous"),
        ]

        def __init__(self, scan_result: ScanResult, *args, **kwargs):
            """Initialize TUI with scan result."""
            super().__init__(*args, **kwargs)
            self.scan_result = scan_result
            self.comments: List[Comment] = []
            self.filtered_comments: List[Comment] = []
            self._collect_comments()

        def _collect_comments(self) -> None:
            """Collect all comments from scan result."""
            for file_stats in self.scan_result.per_file.values():
                self.comments.extend(file_stats.comments)
            self.filtered_comments = self.comments

        def compose(self) -> ComposeResult:
            """Compose the UI."""
            yield Header()
            with Horizontal():
                with VerticalScroll(id="comment-list-container"):
                    yield Label("[bold]Comments[/bold]")
                    yield CommentList(self.filtered_comments, id="comment-list")
                with VerticalScroll(id="comment-detail-container"):
                    yield Label("[bold]Comment Details[/bold]")
                    yield CommentDetail(id="comment-detail")
            yield Footer()

        def on_mount(self) -> None:
            """Setup on mount."""
            comment_list = self.query_one("#comment-list", CommentList)
            if self.filtered_comments:
                comment_list.focus()
                self._show_comment(self.filtered_comments[0])

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            """Handle row selection."""
            if event.row_key:
                try:
                    # Extract file path and line number from the unique key
                    key_str = str(event.row_key.value)
                    # Key format: "file_path:line_number:index"
                    # Use rsplit to handle file paths with colons (e.g., Windows paths)
                    parts = key_str.rsplit(":", 2)
                    if len(parts) >= 3:
                        # Reconstruct file path (may contain colons)
                        file_path = parts[0]
                        line_num = int(parts[1])
                        idx = int(parts[2])
                        # Find matching comment by index (most reliable)
                        if 0 <= idx < len(self.filtered_comments):
                            comment = self.filtered_comments[idx]
                            self._show_comment(comment)
                    elif len(parts) >= 2:
                        # Fallback: try to match by file path and line number
                        file_path = parts[0]
                        line_num = int(parts[1])
                        comment = next(
                            (c for c in self.filtered_comments 
                             if c.file_path == file_path and c.line_number == line_num),
                            None
                        )
                        if comment:
                            self._show_comment(comment)
                except (ValueError, AttributeError, IndexError):
                    pass

        def _show_comment(self, comment: Comment) -> None:
            """Show comment in detail view."""
            detail = self.query_one("#comment-detail", CommentDetail)
            detail.show_comment(comment)

        def action_filter(self) -> None:
            """Filter comments."""
            # Simplified - in production would show input dialog
            pass

        def action_edit(self) -> None:
            """Edit selected comment."""
            # Simplified - in production would show edit dialog
            pass

        def action_delete(self) -> None:
            """Delete selected comment."""
            # Simplified - in production would confirm and delete
            pass

        def action_next(self) -> None:
            """Navigate to next comment."""
            comment_list = self.query_one("#comment-list", CommentList)
            comment_list.action_cursor_down()

        def action_previous(self) -> None:
            """Navigate to previous comment."""
            comment_list = self.query_one("#comment-list", CommentList)
            comment_list.action_cursor_up()
else:
    # Dummy class when textual is not available
    class CommentTUI:
        pass


def launch_tui(scan_result: ScanResult) -> None:
    """Launch the TUI application."""
    if not TEXTUAL_AVAILABLE:
        console.print("[red]Error: Textual is not installed. Install it with: pip install textual[/red]")
        console.print("[yellow]Falling back to CLI comment list...[/yellow]")
        # Fallback to CLI display - just show count
        all_comments = []
        for file_stats in scan_result.per_file.values():
            all_comments.extend(file_stats.comments)
        console.print(f"\n[bold]Found {len(all_comments)} comments[/bold]")
        console.print("[yellow]Use 'codeatlas comments <path>' to view comments in CLI mode[/yellow]")
        return
    
    app = CommentTUI(scan_result)
    app.run()

