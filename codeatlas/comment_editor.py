"""Comment editing with backup and undo support."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.syntax import Syntax

from codeatlas.config import Config

console = Console()


class BackupManager:
    """Manages file backups for undo operations."""

    def __init__(self, backup_dir: Path, max_backups: int = 10):
        """Initialize backup manager."""
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of a file.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{file_path.name}.{timestamp}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def list_backups(self, file_path: Path) -> List[Path]:
        """List all backups for a file."""
        backups = sorted(
            self.backup_dir.glob(f"{file_path.name}.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return backups[: self.max_backups]

    def restore_backup(self, backup_path: Path, target_path: Path) -> None:
        """Restore a file from backup."""
        shutil.copy2(backup_path, target_path)

    def cleanup_old_backups(self, file_path: Path) -> None:
        """Remove old backups beyond max_backups limit."""
        backups = self.list_backups(file_path)
        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups :]:
                try:
                    old_backup.unlink()
                except Exception:
                    pass


class CommentEditor:
    """Edits comments in source files with safety features."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize comment editor."""
        self.config = config or Config()
        backup_dir = Path(self.config.get("backup.directory", ".codeatlas/backups"))
        max_backups = self.config.get("backup.max_backups", 10)
        self.backup_manager = BackupManager(backup_dir, max_backups)

    def edit_comment(
        self,
        file_path: Path,
        line_number: int,
        new_content: str,
        dry_run: bool = False,
    ) -> Optional[str]:
        """
        Edit a comment at a specific line.

        Args:
            file_path: Path to file
            line_number: Line number (1-indexed)
            new_content: New comment content
            dry_run: If True, only show diff without applying

        Returns:
            Unified diff string or None
        """
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if line_number < 1 or line_number > len(lines):
                console.print(f"[red]Error: Line number {line_number} out of range[/red]")
                return None

            original_line = lines[line_number - 1]
            # Detect comment prefix
            stripped = original_line.lstrip()
            if stripped.startswith("#"):
                prefix = original_line[: len(original_line) - len(stripped)] + "# "
            elif stripped.startswith("//"):
                prefix = original_line[: len(original_line) - len(stripped)] + "// "
            elif stripped.startswith("--"):
                prefix = original_line[: len(original_line) - len(stripped)] + "-- "
            elif "<!--" in original_line and "-->" in original_line:
                # HTML comment - replace content between markers
                start_idx = original_line.find("<!--")
                end_idx = original_line.find("-->")
                new_line = (
                    original_line[: start_idx + 4]
                    + f" {new_content} "
                    + original_line[end_idx:]
                )
            else:
                prefix = original_line[: len(original_line) - len(stripped)] + "# "

            if "<!--" not in original_line:
                new_line = prefix + new_content + "\n"
            else:
                # Already handled above
                pass

            # Generate diff
            diff = self._generate_unified_diff(file_path, lines, line_number - 1, new_line)

            if not dry_run:
                # Create backup
                self.backup_manager.create_backup(file_path)

                # Apply change
                lines[line_number - 1] = new_line
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                # Cleanup old backups
                self.backup_manager.cleanup_old_backups(file_path)

            return diff
        except Exception as e:
            console.print(f"[red]Error editing comment: {e}[/red]")
            return None

    def replace_comments(
        self,
        file_path: Path,
        old_text: str,
        new_text: str,
        dry_run: bool = False,
    ) -> Optional[str]:
        """
        Replace all occurrences of comment text in a file.

        Args:
            file_path: Path to file
            old_text: Text to replace
            new_text: Replacement text
            dry_run: If True, only show diff

        Returns:
            Unified diff string or None
        """
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines(keepends=True)

            modified_lines = []
            changes = []

            for i, line in enumerate(lines, 1):
                if old_text in line:
                    new_line = line.replace(old_text, new_text)
                    modified_lines.append((i, line, new_line))
                    changes.append(i)

            if not changes:
                console.print("[yellow]No matches found[/yellow]")
                return None

            # Generate diff
            diff_lines = []
            diff_lines.append(f"--- a/{file_path.name}")
            diff_lines.append(f"+++ b/{file_path.name}")
            diff_lines.append("@@ -1,1 +1,1 @@")

            for line_num, old_line, new_line in modified_lines:
                diff_lines.append(f"-{old_line.rstrip()}")
                diff_lines.append(f"+{new_line.rstrip()}")

            diff = "\n".join(diff_lines)

            if not dry_run:
                # Create backup
                self.backup_manager.create_backup(file_path)

                # Apply changes
                for line_num, _, new_line in modified_lines:
                    lines[line_num - 1] = new_line

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                # Cleanup old backups
                self.backup_manager.cleanup_old_backups(file_path)

            return diff
        except Exception as e:
            console.print(f"[red]Error replacing comments: {e}[/red]")
            return None

    def delete_comment(
        self,
        file_path: Path,
        line_number: int,
        dry_run: bool = False,
    ) -> Optional[str]:
        """
        Delete a comment line.

        Args:
            file_path: Path to file
            line_number: Line number to delete
            dry_run: If True, only show diff

        Returns:
            Unified diff string or None
        """
        if not file_path.exists():
            console.print(f"[red]Error: File not found: {file_path}[/red]")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if line_number < 1 or line_number > len(lines):
                console.print(f"[red]Error: Line number {line_number} out of range[/red]")
                return None

            deleted_line = lines[line_number - 1]
            diff = self._generate_unified_diff(file_path, lines, line_number - 1, None, delete=True)

            if not dry_run:
                # Create backup
                self.backup_manager.create_backup(file_path)

                # Delete line
                del lines[line_number - 1]

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                # Cleanup old backups
                self.backup_manager.cleanup_old_backups(file_path)

            return diff
        except Exception as e:
            console.print(f"[red]Error deleting comment: {e}[/red]")
            return None

    def _generate_unified_diff(
        self,
        file_path: Path,
        lines: List[str],
        line_index: int,
        new_line: Optional[str],
        delete: bool = False,
    ) -> str:
        """Generate unified diff for a change."""
        context_lines = 3
        start = max(0, line_index - context_lines)
        end = min(len(lines), line_index + context_lines + 1)

        diff_lines = []
        diff_lines.append(f"--- a/{file_path.name}")
        diff_lines.append(f"+++ b/{file_path.name}")
        diff_lines.append(f"@@ -{start + 1},{end - start} +{start + 1},{end - start} @@")

        for i in range(start, end):
            if i == line_index:
                if delete:
                    diff_lines.append(f"-{lines[i].rstrip()}")
                else:
                    diff_lines.append(f"-{lines[i].rstrip()}")
                    if new_line:
                        diff_lines.append(f"+{new_line.rstrip()}")
            else:
                diff_lines.append(f" {lines[i].rstrip()}")

        return "\n".join(diff_lines)

    def undo_last_change(self, file_path: Path) -> bool:
        """
        Restore file from most recent backup.

        Returns:
            True if successful
        """
        backups = self.backup_manager.list_backups(file_path)
        if not backups:
            console.print(f"[yellow]No backups found for {file_path}[/yellow]")
            return False

        try:
            latest_backup = backups[0]
            self.backup_manager.restore_backup(latest_backup, file_path)
            console.print(f"[green]Restored {file_path} from backup[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error restoring backup: {e}[/red]")
            return False

