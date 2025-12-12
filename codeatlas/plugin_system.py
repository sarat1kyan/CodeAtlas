"""Plugin system for CodeAtlas."""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rich.console import Console

console = Console()


class Plugin:
    """Represents a loaded plugin."""

    def __init__(self, name: str, version: str, author: str, module: Any):
        """Initialize plugin."""
        self.name = name
        self.version = version
        self.author = author
        self.module = module
        self.on_scan: Optional[Callable] = None
        self.on_export: Optional[Callable] = None
        self.on_edit: Optional[Callable] = None

        # Load hook functions
        if hasattr(module, "on_scan"):
            self.on_scan = module.on_scan
        if hasattr(module, "on_export"):
            self.on_export = module.on_export
        if hasattr(module, "on_edit"):
            self.on_edit = module.on_edit


class PluginManager:
    """Manages loading and execution of plugins."""

    def __init__(self, plugin_dir: Optional[Path] = None):
        """Initialize plugin manager."""
        self.plugin_dir = plugin_dir or Path("codeatlas_plugins")
        self.plugins: Dict[str, Plugin] = {}

    def load_plugin(self, plugin_path: Path) -> Optional[Plugin]:
        """
        Load a plugin from a file.

        Args:
            plugin_path: Path to plugin Python file

        Returns:
            Plugin object or None if failed
        """
        try:
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            if spec is None or spec.loader is None:
                console.print(f"[yellow]Warning: Could not load plugin {plugin_path}[/yellow]")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_path.stem] = module
            spec.loader.exec_module(module)

            # Get plugin info
            if not hasattr(module, "plugin_info"):
                console.print(f"[yellow]Warning: Plugin {plugin_path} missing plugin_info()[/yellow]")
                return None

            info = module.plugin_info()
            if not isinstance(info, dict):
                console.print(f"[yellow]Warning: Plugin {plugin_path} plugin_info() must return dict[/yellow]")
                return None

            name = info.get("name", plugin_path.stem)
            version = info.get("version", "0.0.0")
            author = info.get("author", "Unknown")

            plugin = Plugin(name, version, author, module)
            self.plugins[name] = plugin

            console.print(f"[green]Loaded plugin: {name} v{version} by {author}[/green]")
            return plugin
        except Exception as e:
            console.print(f"[red]Error loading plugin {plugin_path}: {e}[/red]")
            return None

    def load_plugins(self, auto_load: bool = False) -> List[Plugin]:
        """
        Load all plugins from plugin directory.

        Args:
            auto_load: Whether to auto-load all plugins (security: should be False by default)

        Returns:
            List of loaded plugins
        """
        if not self.plugin_dir.exists():
            return []

        loaded: List[Plugin] = []
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            if auto_load:
                plugin = self.load_plugin(plugin_file)
                if plugin:
                    loaded.append(plugin)
            else:
                # Only load explicitly enabled plugins
                pass

        return loaded

    def load_enabled_plugins(self, enabled_plugins: List[str]) -> List[Plugin]:
        """Load only explicitly enabled plugins."""
        if not self.plugin_dir.exists():
            return []

        loaded: List[Plugin] = []
        for plugin_name in enabled_plugins:
            plugin_file = self.plugin_dir / f"{plugin_name}.py"
            if plugin_file.exists():
                plugin = self.load_plugin(plugin_file)
                if plugin:
                    loaded.append(plugin)
            else:
                console.print(f"[yellow]Warning: Plugin {plugin_name} not found[/yellow]")

        return loaded

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call a hook on all loaded plugins.

        Args:
            hook_name: Name of hook (on_scan, on_export, on_edit)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            List of return values from plugins
        """
        results: List[Any] = []
        for plugin in self.plugins.values():
            hook_func = getattr(plugin, hook_name, None)
            if hook_func:
                try:
                    result = hook_func(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Plugin {plugin.name} hook {hook_name} failed: {e}[/yellow]"
                    )
        return results

    def list_plugins(self) -> List[Dict[str, str]]:
        """List all available plugins."""
        plugins_info: List[Dict[str, str]] = []
        for plugin in self.plugins.values():
            plugins_info.append(
                {
                    "name": plugin.name,
                    "version": plugin.version,
                    "author": plugin.author,
                }
            )
        return plugins_info

