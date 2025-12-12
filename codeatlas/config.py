"""Configuration management for CodeAtlas."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console

console = Console()


class Config:
    """Manages configuration from global and local sources."""

    def __init__(self, project_path: Optional[Path] = None):
        """Initialize config with optional project path."""
        self.project_path = project_path or Path.cwd()
        self.global_config_path = Path.home() / ".config" / "CodeAtlas" / "config.yml"
        self.local_config_path = self.project_path / ".codeatlas" / "config.yml"
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and merge global and local configs."""
        default_config = {
            "theme": "default",
            "cache": {
                "enabled": True,
                "directory": ".codeatlas/cache",
            },
            "backup": {
                "enabled": True,
                "directory": ".codeatlas/backups",
                "max_backups": 10,
            },
            "scan": {
                "parallel_workers": None,  # Auto-detect
                "skip_binary": True,
                "skip_gitignored": False,
                "max_file_size_mb": 10,
            },
            "cleanup": {
                "remove_trailing_spaces": False,
                "normalize_indentation": False,
                "tab_width": 4,
                "max_consecutive_blanks": 2,
                "remove_commented_code": False,
            },
            "export": {
                "pretty": True,
                "include_git": True,
            },
            "plugins": {
                "enabled": [],
                "auto_load": False,
            },
        }

        # Load global config
        if self.global_config_path.exists():
            try:
                with open(self.global_config_path, "r", encoding="utf-8") as f:
                    global_config = yaml.safe_load(f) or {}
                    default_config = self._merge_dicts(default_config, global_config)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load global config: {e}[/yellow]")

        # Load local config (overrides global)
        if self.local_config_path.exists():
            try:
                with open(self.local_config_path, "r", encoding="utf-8") as f:
                    local_config = yaml.safe_load(f) or {}
                    default_config = self._merge_dicts(default_config, local_config)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load local config: {e}[/yellow]")

        return default_config

    @staticmethod
    def _merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get config value by dot-separated path."""
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set config value by dot-separated path."""
        keys = key_path.split(".")
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    def save_local(self) -> None:
        """Save current config to local config file."""
        self.local_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.local_config_path, "w", encoding="utf-8") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

