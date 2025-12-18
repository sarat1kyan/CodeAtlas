# 🗺️ CodeAtlas

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://github.com/python/mypy)

**The Ultimate Codebase Analysis & Management Tool**

*Comprehensive security scanning, dependency analysis, code quality metrics, and comment management in one powerful CLI tool.*

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Examples](#-examples)

</div>

---

## 🌟 What is CodeAtlas?

**CodeAtlas** is a production-ready, feature-rich CLI tool that provides comprehensive codebase analysis, security scanning, dependency management, code quality metrics, and interactive comment editing. Built with Python 3.10+ and designed to scale to repositories with 100k+ files.

### Why CodeAtlas?

- 🔒 **Security First**: Built-in vulnerability scanning with Bandit, Safety, npm audit, and more
- 📦 **Dependency Intelligence**: Multi-language dependency analysis with update detection
- 📊 **Quality Metrics**: Advanced complexity analysis and maintainability scoring
- 📜 **License Compliance**: Automatic license detection and compatibility checking
- 💬 **Comment Management**: Interactive TUI for reviewing and editing comments
- ⚡ **Blazing Fast**: Parallel processing with intelligent caching
- 🎨 **Beautiful Output**: Rich terminal UI with color-coded tables and progress indicators
- 🔌 **Extensible**: Plugin system for custom analysis

---

## ✨ Features

### 🔒 Security & Vulnerability Scanning

- **Bandit Integration**: Scans Python code for security issues
- **Dependency Vulnerability Checks**: Safety, pip-audit, npm audit support
- **Generic Security Patterns**: Detects hardcoded secrets, SQL injection risks, command injection
- **Severity Classification**: Categorizes issues by criticality (critical, high, medium, low)
- **Detailed Reporting**: File locations, line numbers, and code snippets

### 📦 Dependency Management

- **Multi-Language Support**: Python (pip, poetry, pipenv), Node.js (npm), Go, Rust
- **Update Detection**: Identifies outdated packages automatically
- **License Information**: Shows dependency licenses and compatibility
- **Lock File Detection**: Validates presence of lock files for reproducible builds
- **Package Manager Detection**: Auto-detects package managers in use

### 📊 Code Quality Analysis

- **Cyclomatic Complexity**: Measures code complexity and branching
- **Cognitive Complexity**: Analyzes code understandability
- **Maintainability Index**: Calculates code maintainability score (0-100)
- **Halstead Volume**: Estimates code complexity metrics
- **Technical Debt Assessment**: Categorizes files by complexity level
- **Top Issues Identification**: Highlights most complex files

### 📜 License Compliance

- **Project License Detection**: Finds licenses from multiple sources (LICENSE, package.json, pyproject.toml, setup.py)
- **Dependency License Analysis**: Checks all dependency licenses
- **Compatibility Checking**: Detects incompatible license combinations
- **OSI/FSF Approval**: Validates licenses against OSI/FSF standards
- **Risk Assessment**: Categorizes licenses by risk level

### 💬 Comment Management

- **Interactive TUI**: Beautiful Textual-based interface for comment review
- **Context-Aware Editing**: See code context when editing comments
- **Batch Operations**: Edit multiple comments efficiently
- **Safety Features**: Automatic backups with undo support
- **Filtering**: Filter by file, language, or text pattern

### 🌳 Project Analysis

- **Language Detection**: Detects 50+ languages by extension, shebang, and content
- **Comprehensive Statistics**: Per-file and per-language metrics
- **Project Tree Generation**: ASCII, Rich (colors + icons), and Markdown formats
- **Git Integration**: Auto-detects repos, respects .gitignore, shows git status
- **Export Formats**: JSON, YAML, Markdown, CSV with stable schemas

### 🧹 Code Cleanup

- **Trailing Spaces**: Remove trailing whitespace
- **Indentation Normalization**: Standardize indentation
- **Duplicate Blank Lines**: Remove excessive blank lines
- **Commented Code Detection**: Find and optionally remove commented-out code
- **Dry-Run Mode**: Preview changes before applying

### 🔌 Extensibility

- **Plugin System**: Extensible architecture with sandboxed execution
- **Custom Hooks**: on_scan, on_export, on_edit hooks
- **Easy Integration**: Simple plugin API

### 🔄 Code Duplication Detection

- **Duplicate Block Detection**: Finds repeated code blocks
- **Similarity Analysis**: Calculates similarity percentage
- **Multiple Occurrences**: Tracks all locations of duplicates
- **Refactoring Suggestions**: Identifies code that should be extracted

### 💀 Dead Code Detection

- **Unused Functions**: Detects functions that are never called
- **Unused Classes**: Finds classes that are never instantiated
- **Unused Imports**: Identifies imports that are never used
- **Unreachable Code**: Finds code that can never be executed

### 🔍 Advanced Security Features

- **Entropy Detection**: Finds high-entropy strings (likely secrets)
- **File Secret Detection**: Identifies secret files (.env, keys, etc.)
- **Git Ignore Validation**: Checks if secrets are properly ignored
- **Pattern Matching**: 30+ security patterns for comprehensive scanning

---

## 🚀 Installation

### 🎨 Interactive Installation (Recommended)

We provide beautiful, interactive installation scripts that handle everything automatically:

**Python Script (Cross-platform, Recommended):**
```bash
# Clone the repository
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas

# Run interactive installer
python install.py
```

**Bash Script (Linux/Mac):**
```bash
# Make executable and run
chmod +x install.sh
./install.sh
```

**Windows Batch Script:**
```cmd
# Run in Command Prompt
install.bat
```

**What the installer does:**
- ✅ Checks Python version (3.10+)
- ✅ Detects available package manager (pip, pip3, poetry, pipenv)
- ✅ Creates virtual environment (with option to customize location)
- ✅ Installs all dependencies automatically
- ✅ Optionally installs security tools (bandit, safety, pip-audit)
- ✅ Verifies installation
- ✅ Shows beautiful usage instructions with next steps
- ✅ Beautiful Rich UI with progress bars and colored output
- ✅ Graceful fallback if Rich is not available

### Uninstall

To remove CodeAtlas and its virtual environment:

**Python Script:**
```bash
python install.py --uninstall
python install.py --uninstall --remove-config  # Also remove config files
```

**Bash Script:**
```bash
./install.sh --uninstall
./install.sh --uninstall --remove-config  # Also remove config files
```

**Windows Batch:**
```cmd
install.bat --uninstall
install.bat --uninstall --remove-config  # Also remove config files
```

The uninstaller will:
- ✅ Find virtual environments automatically
- ✅ Let you select which venv to remove (if multiple)
- ✅ Ask for confirmation before removal
- ✅ Optionally remove configuration files
- ✅ Show beautiful confirmation messages

### Manual Installation

If you prefer manual installation:

```bash
# Clone the repository
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Manual Uninstall

To manually uninstall:

```bash
# Remove virtual environment
rm -rf venv  # Linux/Mac
rmdir /s /q venv  # Windows

# Optionally remove config files
rm -rf .codeatlas  # Local config
rm -rf ~/.config/CodeAtlas  # Global config (Linux/Mac)
```

### Requirements

- **Python 3.10+** (3.11+ recommended)
- **pip** or **pip3** (automatically detected)
- Dependencies are automatically installed by the installer

### Installation Options

The interactive installer supports:

- **Virtual Environment**: Automatically creates and manages venv
- **Package Manager Detection**: Auto-detects pip, pip3, poetry, pipenv
- **Development Mode**: Option to install dev dependencies
- **Optional Tools**: Option to install security scanning tools
- **Custom Location**: Choose where to create virtual environment
- **Verification**: Automatically verifies installation success

### Optional External Tools

For enhanced functionality, you can optionally install:

```bash
# Python security tools
pip install bandit safety pip-audit pip-licenses

# Node.js tools (if working with Node.js projects)
# Option 1: Install globally (requires sudo on Linux/Mac)
sudo npm install -g license-checker

# Option 2: Install locally in your project (recommended - no sudo needed)
npm install --save-dev license-checker
# Then use: npx license-checker

# Option 3: Use npm's built-in audit (no installation needed)
# npm audit is built into npm, no additional installation required
```

> **Note**: 
> - CodeAtlas works without these tools, but they enable additional features like security scanning and license checking.
> - For npm tools, if you get `EACCES: permission denied` errors, use `sudo` or install locally in your project (Option 2).
> - `npm audit` is built into npm and works without any additional installation.
> - Most features work without external tools - they're optional enhancements.

---

## ⚡ Quick Start

### 1. Scan Your Codebase

```bash
# Basic scan
codeatlas scan /path/to/your/project

# Comprehensive scan with all features
codeatlas scan . --security --dependencies --quality --licenses
```

### 2. Security Audit

```bash
# Check for security vulnerabilities
codeatlas security /path/to/project

# Export security report
codeatlas security . --output security-report.json
```

### 3. Check Dependencies

```bash
# Check for outdated dependencies
codeatlas dependencies /path/to/project

# Check with update detection
codeatlas dependencies . --check-updates
```

### 4. Analyze Code Quality

```bash
# Analyze code complexity and maintainability
codeatlas quality /path/to/project

# Export quality metrics
codeatlas quality . --output quality-report.json
```

### 5. Review Comments

```bash
# List all comments
codeatlas comments /path/to/project

# Interactive TUI
codeatlas comments /path/to/project --tui

# Filter comments
codeatlas comments . --language Python --text "TODO"
```

### 6. Detect Code Duplication

```bash
# Find duplicate code blocks
codeatlas duplicates /path/to/project

# Custom thresholds
codeatlas duplicates . --min-lines 10 --min-similarity 90
```

### 7. Find Dead Code

```bash
# Detect unused code
codeatlas deadcode /path/to/project
```

### 8. Comprehensive Summary

```bash
# Get complete codebase overview
codeatlas summary /path/to/project

# With export
codeatlas summary . --output summary.json
```

---

## 📖 Command Reference

### `scan` - Comprehensive Codebase Scanning

Scan your codebase with optional security, dependency, quality, and license checks.

```bash
codeatlas scan <path> [OPTIONS]
```

**Options:**
- `--skip-gitignored`: Skip files listed in `.gitignore`
- `--output, -o`: Output file for JSON report
- `--format, -f`: Output format (`table`, `json`, `yaml`)
- `--security`: Include security vulnerability scan
- `--dependencies`: Include dependency analysis
- `--quality`: Include code quality analysis
- `--licenses`: Include license compliance check
- `--duplicates`: Include code duplication detection
- `--deadcode`: Include dead code detection
- `--all`: Run all analysis (comprehensive scan)

**Examples:**
```bash
# Basic scan
codeatlas scan .

# Full comprehensive analysis
codeatlas scan . --all --output report.json

# Selective analysis
codeatlas scan . --security --quality --duplicates
```

---

### `security` - Security Vulnerability Scanning

Scan for security vulnerabilities and dependency issues.

```bash
codeatlas security <path> [--output OUTPUT]
```

**Features:**
- Python code security (Bandit)
- Dependency vulnerabilities (Safety, pip-audit)
- Node.js vulnerabilities (npm audit)
- Generic security pattern detection

**Example:**
```bash
codeatlas security . --output security-report.json
```

---

### `dependencies` - Dependency Analysis

Check dependencies for updates, licenses, and issues.

```bash
codeatlas dependencies <path> [--check-updates] [--output OUTPUT]
```

**Features:**
- Multi-language support (Python, Node.js, Go, Rust)
- Outdated package detection
- License information
- Lock file validation

**Example:**
```bash
codeatlas dependencies . --check-updates
```

---

### `quality` - Code Quality Analysis

Analyze code complexity, maintainability, and quality metrics.

```bash
codeatlas quality <path> [--output OUTPUT]
```

**Metrics:**
- Cyclomatic complexity
- Cognitive complexity
- Maintainability index
- Technical debt assessment

**Example:**
```bash
codeatlas quality . --output quality-report.json
```

---

### `licenses` - License Compliance

Check project and dependency licenses for compliance.

```bash
codeatlas licenses <path> [--output OUTPUT]
```

**Features:**
- Project license detection
- Dependency license analysis
- Compatibility checking
- Risk assessment

**Example:**
```bash
codeatlas licenses . --output licenses.json
```

---

### `comments` - Comment Management

List, review, and manage comments in your codebase.

```bash
codeatlas comments <path> [OPTIONS]
```

**Options:**
- `--file PATTERN`: Filter by file path pattern
- `--language LANG`: Filter by language
- `--text REGEX`: Filter by text regex
- `--tui`: Launch interactive TUI
- `--output, -o`: Export comments to JSON

**Examples:**
```bash
# List all comments
codeatlas comments .

# Interactive TUI
codeatlas comments . --tui

# Filter Python TODOs
codeatlas comments . --language Python --text "TODO"
```

---

### `edit` - Edit Comments

Edit or delete comments in files.

```bash
codeatlas edit <file:line> [OPTIONS]
```

**Options:**
- `--replace TEXT`: New comment text
- `--delete`: Delete comment
- `--dry-run`: Show diff without applying
- `--apply`: Apply changes (required for non-dry-run)

**Example:**
```bash
codeatlas edit src/main.py:42 --replace "Updated comment" --apply
```

---

### `tree` - Project Tree Generation

Generate beautiful project tree visualizations.

```bash
codeatlas tree <path> [OPTIONS]
```

**Options:**
- `--format, -f`: Format (`ascii`, `rich`, `markdown`)
- `--max-depth, -d`: Maximum depth
- `--files/--no-files`: Include/exclude files
- `--size`: Include file sizes
- `--output, -o`: Output file

**Examples:**
```bash
# Rich tree with colors
codeatlas tree . --format rich

# Markdown export
codeatlas tree . --format markdown --output tree.md
```

---

### `cleanup` - Code Cleanup

Clean up code files with various options.

```bash
codeatlas cleanup <path> [OPTIONS]
```

**Options:**
- `--remove-trailing-spaces`: Remove trailing whitespace
- `--normalize-indentation`: Normalize indentation
- `--tab-width WIDTH`: Tab width for indentation (default: 4)
- `--remove-duplicate-blanks`: Remove duplicate blank lines
- `--max-blanks N`: Max consecutive blank lines (default: 2)
- `--remove-commented-code`: Remove commented-out code
- `--dry-run`: Preview changes without applying

**Example:**
```bash
codeatlas cleanup . --remove-trailing-spaces --dry-run
```

---

### `export` - Export Reports

Export scan results to various formats.

```bash
codeatlas export <path> <output> [OPTIONS]
```

**Options:**
- `--format, -f`: Format (`json`, `yaml`, `markdown`, `csv`)
- `--skip-gitignored`: Skip gitignored files

**Example:**
```bash
codeatlas export . report.json --format json
```

---

### `duplicates` - Code Duplication Detection

Detect duplicate code blocks in your codebase.

```bash
codeatlas duplicates <path> [--min-lines LINES] [--min-similarity PERCENT] [--output OUTPUT]
```

**Options:**
- `--min-lines`: Minimum lines for duplicate block (default: 5)
- `--min-similarity`: Minimum similarity percentage (default: 80.0)
- `--output, -o`: Export results to JSON

**Example:**
```bash
codeatlas duplicates . --min-lines 10 --output duplicates.json
```

---

### `deadcode` - Dead Code Detection

Find unused functions, classes, and imports.

```bash
codeatlas deadcode <path> [--output OUTPUT]
```

**Example:**
```bash
codeatlas deadcode . --output deadcode.json
```

---

### `summary` - Comprehensive Summary

Generate a complete codebase overview with all metrics.

```bash
codeatlas summary <path> [--output OUTPUT]
```

**Features:**
- Health score calculation
- All metrics in one view
- Quick overview of codebase status

**Example:**
```bash
codeatlas summary . --output summary.json
```

---

### `plugins` - Plugin Management

Manage CodeAtlas plugins.

```bash
codeatlas plugins [--list] [--load PLUGIN]
```

**Example:**
```bash
codeatlas plugins --list
```

---

## 🎯 Use Cases

### CI/CD Integration

```bash
# In your CI pipeline
codeatlas scan . --security --dependencies --quality --licenses --output report.json

# Check for critical security issues
codeatlas security . --output security.json
if grep -q '"severity": "critical"' security.json; then
    echo "Critical security issues found!"
    exit 1
fi
```

### Pre-Commit Checks

```bash
# Check code quality before committing
codeatlas quality . --output quality.json
codeatlas security . --output security.json
```

### Dependency Maintenance

```bash
# Weekly dependency check
codeatlas dependencies . --check-updates --output deps.json
```

### License Compliance

```bash
# Before releasing
codeatlas licenses . --output licenses.json
```

---

## ⚙️ Configuration

CodeAtlas supports both global and local configuration:

- **Global**: `~/.config/CodeAtlas/config.yml`
- **Local**: `.codeatlas/config.yml` (project-specific)

### Example Configuration

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

---

## 📊 Export Schema

### JSON Export Format

```json
{
  "base": "/path/to/repo",
  "total_files": 1234,
  "total_dirs": 56,
  "total_size_bytes": 12345678,
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
  "security": {
    "total_issues": 5,
    "issues_by_severity": {
      "critical": 0,
      "high": 2,
      "medium": 3
    }
  },
  "dependencies": {
    "total_dependencies": 45,
    "outdated_count": 3
  },
  "quality": {
    "average_complexity": 8.5,
    "average_maintainability": 72.3
  },
  "licenses": {
    "project_license": "MIT",
    "incompatible_count": 0
  }
}
```

---

## 🔌 Plugin System

Create custom plugins in the `codeatlas_plugins/` directory.

### Plugin Structure

```python
def plugin_info():
    return {
        "name": "my_plugin",
        "version": "1.0.0",
        "author": "Your Name"
    }

def on_scan(scan_result):
    # Process scan result
    return None

def on_export(scan_result, export_type):
    # Process before export
    pass

def on_edit(pre_edit_state, planned_changes):
    # Validate or modify edits
    return planned_changes
```

---

## 🛠️ Development

### Setup Development Environment

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
ruff check codeatlas
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage
- 🔌 Plugin development
- 🌍 Language support

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**sarat1kyan**

- GitHub: [@sarat1kyan](https://github.com/sarat1kyan)
- Repository: [CodeAtlas](https://github.com/sarat1kyan/CodeAtlas)
- Issues: [Report a bug](https://github.com/sarat1kyan/CodeAtlas/issues)

---

## 🔧 Troubleshooting

### npm Permission Errors

If you encounter `EACCES: permission denied` when installing npm packages globally:

**Solution 1: Use sudo (Linux/Mac)**
```bash
sudo npm install -g license-checker
```

**Solution 2: Install locally (Recommended)**
```bash
# Install in your project
npm install --save-dev license-checker

# Use with npx (no global install needed)
npx license-checker
```

**Solution 3: Fix npm permissions (Linux/Mac)**
```bash
# Create a directory for global packages
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'

# Add to your ~/.bashrc or ~/.zshrc
export PATH=~/.npm-global/bin:$PATH
```

### No Dependencies Found

If `codeatlas dependencies` shows 0 dependencies:

- **Python projects**: Make sure `requirements.txt`, `pyproject.toml`, or `setup.py` exists
- **Node.js projects**: Ensure `package.json` exists and has dependencies listed
- **Empty projects**: Projects without dependencies will correctly show 0

### Security Scanner Shows No Issues

If `codeatlas security` shows 0 issues:

- This is normal! It means no vulnerabilities were detected
- External tools (bandit, safety) are optional - install them for more comprehensive scanning
- Generic security checks still run without external tools

### Code Quality Analysis Limited to Python

Currently, code quality analysis focuses on Python files. Support for other languages is planned. The tool still provides:
- Language detection for all files
- File statistics for all languages
- Security scanning for multiple languages

---

## 🙏 Acknowledgments

Built with amazing open-source tools:

- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
- [Typer](https://github.com/tiangolo/typer) - Modern CLI framework
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [PyYAML](https://github.com/yaml/pyyaml) - YAML parsing
- [Bandit](https://github.com/PyCQA/bandit) - Security linter
- [Safety](https://github.com/pyupio/safety) - Dependency vulnerability checker

---

## 📈 Roadmap

- [ ] Code duplication detection
- [ ] Dead code analysis
- [ ] Performance profiling
- [ ] Documentation coverage analysis
- [ ] Test coverage integration
- [ ] Architecture analysis
- [ ] Dependency graph visualization
- [ ] More language support

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

**CodeAtlas v0.1.0** - Production-ready codebase analysis and management.

Made with ❤️ by the CodeAtlas team

</div>
