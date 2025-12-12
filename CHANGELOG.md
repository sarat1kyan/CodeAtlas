# Changelog

All notable changes to CodeAtlas will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-XX

### Added
- Initial release of CodeAtlas
- Language detection by extension, shebang, and content analysis
- Codebase scanning with parallel processing and caching
- Comment parsing for multiple languages
- Interactive TUI for comment review and editing
- Project tree generation (ASCII, Rich, Markdown)
- Git integration (status, gitignore support)
- Export to JSON, YAML, Markdown, CSV
- Code cleanup operations (trailing spaces, indentation, etc.)
- Plugin system with sandboxed execution
- Backup and undo system for file modifications
- Configuration system (global and local)
- Comprehensive CLI with rich output
- Dry-run support for all destructive operations

### Features
- Support for 50+ programming languages
- Parallel file scanning for performance
- File-based caching with mtime/sha1 keys
- Safety features (backups, diffs, dry-run)
- Beautiful terminal output with Rich
- Textual-based TUI for interactive editing

[0.1.0]: https://github.com/sarat1kyan/CodeAtlas/releases/tag/v0.1.0

