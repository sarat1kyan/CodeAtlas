"""Export scan results to various formats."""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from codeatlas.scanner import ScanResult

from codeatlas.scanner import FileStats


class Exporter:
    """Exports scan results to various formats."""

    def __init__(self):
        """Initialize exporter."""
        pass

    def export_json(self, scan_result: ScanResult, output_path: Path, pretty: bool = True) -> None:
        """Export scan result to JSON."""
        data = self._scan_result_to_dict(scan_result)

        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

    def export_yaml(self, scan_result: ScanResult, output_path: Path) -> None:
        """Export scan result to YAML."""
        data = self._scan_result_to_dict(scan_result)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    def export_markdown(self, scan_result: ScanResult, output_path: Path) -> None:
        """Export scan result to Markdown."""
        lines: List[str] = []

        lines.append("# CodeAtlas Scan Report\n")
        lines.append(f"**Base Path:** `{scan_result.base_path}`\n")
        lines.append(f"**Generated:** {self._get_timestamp()}\n")

        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Total Files:** {scan_result.total_files:,}")
        lines.append(f"- **Total Directories:** {scan_result.total_dirs:,}")
        lines.append(f"- **Total Size:** {self._format_size(scan_result.total_size_bytes)}")
        lines.append(f"- **Total Lines:** {scan_result.total_lines:,}")
        lines.append(f"- **Blank Lines:** {scan_result.total_blank:,}")
        lines.append(f"- **Comment Lines:** {scan_result.total_comments:,}")
        lines.append(f"- **Code Lines:** {scan_result.total_code:,}\n")

        # Per-language statistics
        lines.append("## Per-Language Statistics\n")
        lines.append("| Language | Files | Lines | Code | Comments | Blank | Size |")
        lines.append("|----------|-------|-------|------|----------|-------|------|")

        for lang, stats in sorted(scan_result.per_language.items(), key=lambda x: x[1]["code"], reverse=True):
            lines.append(
                f"| {lang} | {stats['files']:,} | {stats['lines']:,} | "
                f"{stats['code']:,} | {stats['comments']:,} | {stats['blank']:,} | "
                f"{self._format_size(stats['bytes'])} |"
            )

        lines.append("")

        # Git info
        if scan_result.git_info:
            lines.append("## Git Information\n")
            git = scan_result.git_info
            if git.get("branch"):
                lines.append(f"- **Branch:** {git['branch']}")
            if git.get("commit"):
                lines.append(f"- **Commit:** {git['commit']}")
            if git.get("status"):
                status = git["status"]
                lines.append(f"- **Modified:** {len(status.get('modified', []))}")
                lines.append(f"- **Untracked:** {len(status.get('untracked', []))}")
            lines.append("")

        # Top files by size
        lines.append("## Top 20 Largest Files\n")
        lines.append("| File | Size | Lines | Language |")
        lines.append("|------|------|-------|----------|")

        sorted_files = sorted(
            scan_result.per_file.items(), key=lambda x: x[1].size_bytes, reverse=True
        )[:20]
        for path, stats in sorted_files:
            lines.append(
                f"| `{path}` | {self._format_size(stats.size_bytes)} | "
                f"{stats.total_lines:,} | {stats.language or 'Unknown'} |"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def export_csv(self, scan_result: ScanResult, output_path: Path) -> None:
        """Export per-file statistics to CSV."""
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Path",
                    "Size (bytes)",
                    "Total Lines",
                    "Blank Lines",
                    "Comment Lines",
                    "Code Lines",
                    "Language",
                ]
            )

            for path, stats in sorted(scan_result.per_file.items()):
                writer.writerow(
                    [
                        path,
                        stats.size_bytes,
                        stats.total_lines,
                        stats.blank_lines,
                        stats.comment_lines,
                        stats.code_lines,
                        stats.language or "Unknown",
                    ]
                )

    def _scan_result_to_dict(self, scan_result: ScanResult) -> Dict[str, Any]:
        """Convert ScanResult to dictionary."""
        return {
            "base": str(scan_result.base_path),
            "total_files": scan_result.total_files,
            "total_dirs": scan_result.total_dirs,
            "total_size_bytes": scan_result.total_size_bytes,
            "human_size": self._format_size(scan_result.total_size_bytes),
            "total_lines": scan_result.total_lines,
            "total_blank": scan_result.total_blank,
            "total_comments": scan_result.total_comments,
            "total_code": scan_result.total_code,
            "per_language": scan_result.per_language,
            "per_file": {
                path: {
                    "size_bytes": stats.size_bytes,
                    "lines": stats.total_lines,
                    "blank": stats.blank_lines,
                    "comment": stats.comment_lines,
                    "code": stats.code_lines,
                    "language": stats.language,
                }
                for path, stats in scan_result.per_file.items()
            },
            "git": scan_result.git_info if scan_result.git_info else None,
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp as string."""
        from datetime import datetime

        return datetime.now().isoformat()

