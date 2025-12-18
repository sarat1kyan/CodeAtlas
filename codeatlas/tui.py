"""Textual TUI for interactive comment review and editing."""

from pathlib import Path
from typing import List, Optional

try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical, VerticalScroll
    from textual.widgets import DataTable, Footer, Header, Input, Label, Static
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
            self.zebra_stripes = True

        def on_mount(self) -> None:
            """Setup table on mount."""
            self.add_columns("File", "Line", "Language", "Preview")
            if not self.comments:
                self.add_row("(No comments found)", "", "", "", key="empty")
            else:
                for idx, comment in enumerate(self.comments):
                    # Truncate file path for display
                    file_display = Path(comment.file_path).name
                    if len(file_display) > 30:
                        file_display = file_display[:27] + "..."
                    
                    preview = comment.content[:40] + "..." if len(comment.content) > 40 else comment.content
                    # Create unique key from file path and line number
                    unique_key = f"{comment.file_path}:{comment.line_number}:{idx}"
                    self.add_row(
                        file_display,
                        str(comment.line_number),
                        comment.language or "Unknown",
                        preview,
                        key=unique_key,
                    )


    class CommentDetail(Static):
        """Widget displaying comment details."""

        def __init__(self, *args, **kwargs):
            """Initialize comment detail."""
            super().__init__(*args, **kwargs)
            self.update("[dim]Select a comment to view details[/dim]")

        def show_comment(self, comment: Comment) -> None:
            """Display a comment with context."""
            from rich.text import Text
            
            lines: List[str] = []
            lines.append(f"[bold cyan]File:[/bold cyan] {comment.file_path}")
            lines.append(f"[bold cyan]Line:[/bold cyan] {comment.line_number}")
            lines.append(f"[bold cyan]Language:[/bold cyan] {comment.language or 'Unknown'}")
            lines.append("")
            
            if comment.context_before:
                lines.append("[bold yellow]Context Before:[/bold yellow]")
                for line in comment.context_before[-3:]:  # Show last 3 lines
                    lines.append(f"  [dim]{line}[/dim]")
                lines.append("")
            
            lines.append(f"[bold green]Comment:[/bold green]")
            lines.append(f"  {comment.content}")
            lines.append("")
            
            if comment.context_after:
                lines.append("[bold yellow]Context After:[/bold yellow]")
                for line in comment.context_after[:3]:  # Show first 3 lines
                    lines.append(f"  [dim]{line}[/dim]")

            self.update("\n".join(lines))


    class CommentTUI(App):
        """Textual TUI application for comment review."""

        CSS = """
        Screen {
            background: $surface;
        }
        
        #comment-list-container {
            width: 50%;
            border: solid $primary;
            margin: 1;
        }
        
        #comment-detail-container {
            width: 50%;
            border: solid $primary;
            margin: 1;
        }
        
        #comment-list {
            width: 100%;
            height: 1fr;
        }
        
        #comment-detail {
            width: 100%;
            height: 1fr;
            padding: 1;
        }
        
        Label {
            padding: 1;
            text-style: bold;
            background: $primary;
            color: $text;
        }
        
        DataTable {
            border: solid $primary;
        }
        
        DataTable:focus {
            border: solid $accent;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit", priority=True),
            Binding("f", "filter", "Filter", priority=True),
            Binding("e", "edit", "Edit"),
            Binding("d", "delete", "Delete"),
            Binding("n", "next", "Next"),
            Binding("p", "previous", "Previous"),
            Binding("up", "cursor_up", "Up", show=False),
            Binding("down", "cursor_down", "Down", show=False),
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
            # Collect comments from all files
            for file_stats in self.scan_result.per_file.values():
                if file_stats.comments:
                    self.comments.extend(file_stats.comments)
            self.filtered_comments = self.comments.copy()
            
            # Debug: log if no comments found
            if not self.comments:
                console.print(f"[yellow]Warning: No comments found in {len(self.scan_result.per_file)} files[/yellow]")

        def compose(self) -> ComposeResult:
            """Compose the UI."""
            yield Header(show_clock=True)
            with Horizontal():
                with Vertical(id="comment-list-container"):
                    yield Label(f"[bold]Comments ({len(self.filtered_comments)})[/bold]")
                    yield CommentList(self.filtered_comments, id="comment-list")
                with Vertical(id="comment-detail-container"):
                    yield Label("[bold]Comment Details[/bold]")
                    yield CommentDetail(id="comment-detail")
            yield Footer()

        def on_mount(self) -> None:
            """Setup on mount."""
            comment_list = self.query_one("#comment-list", CommentList)
            if self.filtered_comments:
                comment_list.focus()
                # Select first row
                if len(self.filtered_comments) > 0:
                    try:
                        first_key = f"{self.filtered_comments[0].file_path}:{self.filtered_comments[0].line_number}:0"
                        comment_list.cursor_coordinate = (0, 0)
                        self._show_comment(self.filtered_comments[0])
                    except Exception:
                        pass
            else:
                # Show empty state
                detail = self.query_one("#comment-detail", CommentDetail)
                detail.update("[yellow]No comments found. Try scanning a different directory or adjusting filters.[/yellow]")

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            """Handle row selection."""
            if event.row_key and str(event.row_key.value) != "empty":
                try:
                    # Extract file path and line number from the unique key
                    key_str = str(event.row_key.value)
                    # Key format: "file_path:line_number:index"
                    # Use rsplit to handle file paths with colons (e.g., Windows paths)
                    parts = key_str.rsplit(":", 2)
                    if len(parts) >= 3:
                        # Use index to directly access comment (most reliable)
                        idx = int(parts[2])
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
                except (ValueError, AttributeError, IndexError) as e:
                    pass

        def _show_comment(self, comment: Comment) -> None:
            """Show comment in detail view."""
            detail = self.query_one("#comment-detail", CommentDetail)
            detail.show_comment(comment)

        def action_filter(self) -> None:
            """Filter comments."""
            # TODO: Implement filter dialog
            self.notify("Filter functionality coming soon", severity="information")

        def action_edit(self) -> None:
            """Edit selected comment."""
            # TODO: Implement edit dialog
            self.notify("Edit functionality coming soon", severity="information")

        def action_delete(self) -> None:
            """Delete selected comment."""
            # TODO: Implement delete with confirmation
            self.notify("Delete functionality coming soon", severity="information")

        def action_next(self) -> None:
            """Navigate to next comment."""
            comment_list = self.query_one("#comment-list", CommentList)
            comment_list.action_cursor_down()

        def action_previous(self) -> None:
            """Navigate to previous comment."""
            comment_list = self.query_one("#comment-list", CommentList)
            comment_list.action_cursor_up()

        def action_cursor_up(self) -> None:
            """Move cursor up."""
            comment_list = self.query_one("#comment-list", CommentList)
            comment_list.action_cursor_up()

        def action_cursor_down(self) -> None:
            """Move cursor down."""
            comment_list = self.query_one("#comment-list", CommentList)
            comment_list.action_cursor_down()
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
