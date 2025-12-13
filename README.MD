# 🗺️ CodeAtlas

<p align="center">
  <strong>Explore. Understand. Refine.</strong><br />
  A luxury-grade CLI & TUI for deep codebase analysis and safe refactoring
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-gold.svg" /></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" /></a>
  <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" /></a>
  <img src="https://img.shields.io/badge/status-production--ready-brightgreen" />
</p>

---

## ✨ What is CodeAtlas?

**CodeAtlas** is a **high-performance, production-ready CLI + TUI** designed to *map, analyze, clean, and safely refactor* large codebases.

It is built for engineers who:

* Work with **massive repositories**
* Inherit **legacy or unfamiliar projects**
* Need **precision, safety, and speed**
* Prefer **beautiful terminal tools** over bloated GUIs

> Think of CodeAtlas as **a cartographer, auditor, and craftsman** for your source code.

---

## 💎 Why CodeAtlas Stands Out

| Feature                  | Why It Matters                                         |
| ------------------------ | ------------------------------------------------------ |
| 🧭 Deep Codebase Insight | Understand structure, languages, and metrics instantly |
| 💬 Comment Intelligence  | Review, edit, or remove comments *safely*              |
| 🧹 Precision Cleanup     | Enforce consistency without breaking code              |
| ⚡ Extreme Scalability    | Handles 100k+ files effortlessly                       |
| 🛡️ Safety First         | Dry-runs, diffs, backups, undo                         |
| 🎨 Terminal Elegance     | Rich + Textual powered UI                              |

---

## 🚀 Feature Highlights

### 🔍 Intelligent Code Analysis

* Automatic language detection (extension, shebang, content)
* Accurate metrics per file and per language
* Logical lines vs physical lines
* Binary & large-file protection

### 💬 Comment Review & Editing

* Context-aware comment listing
* Regex, language, and path filtering
* Interactive editing (CLI & TUI)
* Unified diffs before applying changes

### 🌳 Project Tree Generation

* ASCII, Rich, and Markdown trees
* Icons, colors, and sizes
* Depth limiting for massive repos

### 🎨 CLI + Full-Screen TUI

* Rich-rendered CLI output
* Optional Textual-based TUI
* Keyboard-driven workflows
* Designed for long sessions

### 🧹 Cleanup & Normalization

* Trailing whitespace removal
* Indentation normalization
* Duplicate blank-line cleanup
* Commented-out code detection

---

## 📦 Installation

```bash
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas
pip install -e .
```

**Requirements**

* Python **3.11+**

---

## ⚡ Quick Start

```bash
# Scan a repository
codeatlas scan .

# Review comments
codeatlas comments .

# Launch the TUI
codeatlas comments . --tui

# Generate a rich project tree
codeatlas tree . --format rich

# Export a JSON report
codeatlas export . --format json report.json

# Cleanup (safe dry-run)
codeatlas cleanup . --remove-trailing-spaces --dry-run
```

---

## 🧠 Command Map

```text
scan      → Analyze codebase
comments  → Review comments
edit      → Modify comments safely
tree      → Visualize structure
cleanup   → Normalize formatting
export    → Generate reports
plugins   → Extend functionality
```

---

## 🧩 Plugin Architecture

CodeAtlas is **fully extensible** via Python plugins.

Hooks available:

* `on_scan()`
* `on_export()`
* `on_edit()`

Minimal plugin example:

```python
def plugin_info():
    return {
        "name": "example",
        "version": "1.0.0",
        "author": "You"
    }
```

---

## ⚙️ Configuration

Supports **global** and **project-local** configuration.

* `~/.config/CodeAtlas/config.yml`
* `.codeatlas/config.yml`

```yaml
theme: default
cache:
  enabled: true
backup:
  enabled: true
scan:
  parallel_workers: null
cleanup:
  tab_width: 4
```

---

## 🛠️ Development

```bash
pip install -e ".[dev]"
pytest
black codeatlas tests
```

---

## 🤝 Contributing

Contributions are welcome.

If you care about **code quality, tooling, and craftsmanship**, you will feel at home here.

---

## 📜 License

MIT License

---

## 👤 Author

**sarat1kyan**
GitHub: [https://github.com/sarat1kyan](https://github.com/sarat1kyan)

---

<p align="center">
  <strong>CodeAtlas v0.1.0</strong><br />
  <em>Precision tools for serious codebases.</em>
</p>

---

<div align="center">

**Made with ❤️ for the Linux community**

**⭐ Star this repo if you found it helpful!**
[![BuyMeACoffee](https://raw.githubusercontent.com/pachadotdev/buymeacoffee-badges/main/bmc-donate-yellow.svg)](https://www.buymeacoffee.com/saratikyan)
[![Report Bug](https://img.shields.io/badge/Report-Bug-red.svg)](https://github.com/sarat1kyan/LX-Z/issues)

</div>

