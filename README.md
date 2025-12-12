# CodeAtlas

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**CodeAtlas** is a production-ready CLI + TUI tool for scanning, analyzing, cleaning, and interactively editing comments in codebases. Built with Python 3.11+ and designed to scale to repositories with 100k+ files.

## Features

### Core Features

- **🔍 Project Language Detection**: Detects languages by file extension, shebang, and content analysis. Reports per-language percentages based on logical lines and bytes.
- **📊 Codebase Statistics**: Comprehensive statistics for whole project and per-language (lines, comments, blanks, code, files, directories, size).
- **💬 Comment Review & Editing**: Interactive CLI and TUI for reviewing and editing comments with context-aware editing, batch operations, and safety features.
- **🌳 Project Tree Generation**: Pretty-printed tree with ASCII, Rich (colors + icons), and Markdown export options.
- **🎨 Beautiful CLI/TUI**: Rich terminal output with optional Textual-based TUI for keyboard-driven navigation.
- **⚡ Performance**: Parallel scanning with caching, scales to 100k+ files.

### Additional Features

- **🔧 Git Integration**: Auto-detect git repos, skip gitignored files, show git status summary.
- **📤 Exportable Reports**: JSON, YAML, Markdown, CSV exports with stable schemas.
- **🧹 Cleanup Mode**: Remove trailing spaces, normalize indentation, remove duplicate blanks, detect commented-out code.
- **🔌 Plugin System**: Extensible plugin architecture with sandboxed execution.
- **🔄 Dry-run Support**: All destructive operations support `--dry-run` with unified diff preview.
- **💾 Backup & Undo**: Automatic backups with undo support for all file modifications.

## Installation

### From Source

```bash
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas
pip install -e .
```

### Requirements

- Python 3.10+
- Dependencies are automatically installed via `pip install -e .`

## Quick Start

### Scan a Codebase

```bash
codeatlas scan /path/to/repo
```

### View Comments

```bash
codeatlas comments /path/to/repo
```

### Interactive TUI

```bash
codeatlas comments /path/to/repo --tui
```

### Generate Project Tree

```bash
codeatlas tree /path/to/repo --format rich
```

### Export Report

```bash
codeatlas export /path/to/repo --format json --output report.json
```

### Clean Up Code

```bash
codeatlas cleanup /path/to/repo --remove-trailing-spaces --dry-run
```

## Command Reference

### `scan`

Scan a codebase and display statistics.

```bash
codeatlas scan <path> [--skip-gitignored] [--output OUTPUT] [--format FORMAT]
```

Options:
- `--skip-gitignored`: Skip files listed in `.gitignore`
- `--output, -o`: Output file for JSON report
- `--format, -f`: Output format (`table`, `json`, `yaml`)

### `tree`

Generate project tree.

```bash
codeatlas tree <path> [--format FORMAT] [--max-depth DEPTH] [--files/--no-files] [--size] [--output OUTPUT]
```

Options:
- `--format, -f`: Format (`ascii`, `rich`, `markdown`)
- `--max-depth, -d`: Maximum depth
- `--files/--no-files`: Include/exclude files
- `--size`: Include file sizes
- `--output, -o`: Output file

### `comments`

List and review comments.

```bash
codeatlas comments <path> [--file PATTERN] [--language LANG] [--text REGEX] [--tui] [--output OUTPUT]
```

Options:
- `--file`: Filter by file path pattern
- `--language`: Filter by language
- `--text`: Filter by text regex
- `--tui`: Launch interactive TUI
- `--output, -o`: Export comments to JSON

### `edit`

Edit comments in files.

```bash
codeatlas edit <file:line> [--replace TEXT] [--delete] [--dry-run] [--apply]
```

Options:
- `--replace`: New comment text
- `--delete`: Delete comment
- `--dry-run`: Show diff without applying
- `--apply`: Apply changes (required for non-dry-run)

### `cleanup`

Clean up code files.

```bash
codeatlas cleanup <path> [--remove-trailing-spaces] [--normalize-indentation] [--tab-width WIDTH] [--remove-duplicate-blanks] [--max-blanks N] [--remove-commented-code] [--dry-run]
```

### `export`

Export scan results.

```bash
codeatlas export <path> [--format FORMAT] <output> [--skip-gitignored]
```

Formats: `json`, `yaml`, `markdown`, `csv`

### `plugins`

Manage plugins.

```bash
codeatlas plugins [--list] [--load PLUGIN]
```

## Configuration

CodeAtlas supports both global and local configuration:

- **Global**: `~/.config/CodeAtlas/config.yml`
- **Local**: `.codeatlas/config.yml` (project-specific)

Example configuration:

```yaml
theme: default
cache:
  enabled: true
  directory: .codeatlas/cache
backup:
  enabled: true
  directory: .codeatlas/backups
  max_backups: 10
scan:
  parallel_workers: null  # Auto-detect
  skip_binary: true
  skip_gitignored: false
  max_file_size_mb: 10
cleanup:
  remove_trailing_spaces: false
  normalize_indentation: false
  tab_width: 4
  max_consecutive_blanks: 2
  remove_commented_code: false
```

## Export Schema

### JSON Export Format

```json
{
  "base": "/path/to/repo",
  "total_files": 1234,
  "total_dirs": 56,
  "total_size_bytes": 12345678,
  "human_size": "11.8 MB",
  "total_lines": 50000,
  "total_blank": 5000,
  "total_comments": 3000,
  "total_code": 42000,
  "per_language": {
    "Python": {
      "files": 100,
      "lines": 10000,
      "code": 8000,
      "comments": 1000,
      "blank": 1000,
      "bytes": 500000
    }
  },
  "per_file": {
    "src/main.py": {
      "size_bytes": 1024,
      "lines": 50,
      "blank": 5,
      "comment": 10,
      "code": 35,
      "language": "Python"
    }
  },
  "git": {
    "is_git_repo": true,
    "branch": "main",
    "commit": "abc123",
    "status": {
      "modified": [],
      "untracked": [],
      "added": [],
      "deleted": []
    }
  }
}
```

## Plugin System

Plugins can be created in the `codeatlas_plugins/` directory. Each plugin must export:

- `plugin_info() -> dict`: Returns `{"name": "", "version": "", "author": ""}`
- `on_scan(scan_result: dict) -> dict | None`: Hook called after scanning
- `on_export(scan_result: dict, export_type: str) -> None`: Hook called before export
- `on_edit(pre_edit_state: dict, planned_changes: dict) -> dict | None`: Hook called before editing

Example plugin:

```python
def plugin_info():
    return {
        "name": "example_plugin",
        "version": "1.0.0",
        "author": "Your Name"
    }

def on_scan(scan_result):
    # Process scan result
    return None
```

## Development

### Setup

```bash
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Style

```bash
black codeatlas tests
isort codeatlas tests
mypy codeatlas
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**sarat1kyan**

- GitHub: [@sarat1kyan](https://github.com/sarat1kyan)
- Repository: [CodeAtlas](https://github.com/sarat1kyan/CodeAtlas)

## Acknowledgments

Built with:
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [Typer](https://github.com/tiangolo/typer) - Modern CLI framework
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [PyYAML](https://github.com/yaml/pyyaml) - YAML parsing

---

**CodeAtlas v0.1.0** - Production-ready codebase analysis and comment management.

