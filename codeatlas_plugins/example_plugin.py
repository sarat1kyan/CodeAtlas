"""Example plugin for CodeAtlas."""

from typing import Any, Dict, Optional


def plugin_info() -> Dict[str, str]:
    """Return plugin information."""
    return {
        "name": "example_plugin",
        "version": "1.0.0",
        "author": "CodeAtlas Team",
    }


def on_scan(scan_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook called after scanning.

    Args:
        scan_result: Scan result dictionary

    Returns:
        Additional data to attach to scan result, or None
    """
    # Example: Count total comments
    total_comments = scan_result.get("total_comments", 0)
    print(f"[Plugin] Total comments found: {total_comments}")
    return None


def on_export(scan_result: Dict[str, Any], export_type: str) -> None:
    """
    Hook called before export.

    Args:
        scan_result: Scan result dictionary
        export_type: Type of export (json, yaml, markdown, csv)
    """
    print(f"[Plugin] Exporting as {export_type}")


def on_edit(pre_edit_state: Dict[str, Any], planned_changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook called before editing.

    Args:
        pre_edit_state: State before edit
        planned_changes: Planned changes

    Returns:
        Modified planned changes, or None
    """
    print(f"[Plugin] Editing file: {planned_changes.get('file', 'unknown')}")
    return None

