# 🚀 CodeAtlas Installation Guide

## 🎨 Interactive Installation (Recommended)

CodeAtlas comes with beautiful, interactive installation scripts that handle everything automatically!

### Python Script (Cross-platform, Best Experience)

**Works on:** Windows, Linux, macOS

```bash
# Clone the repository
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas

# Run interactive installer
python install.py
```

**Features:**
- ✅ Beautiful Rich UI with progress bars and colors
- ✅ Automatic Python version checking (3.10+)
- ✅ Package manager detection (pip, pip3, poetry, pipenv)
- ✅ Virtual environment creation with custom location
- ✅ Automatic dependency installation
- ✅ Optional security tools installation
- ✅ Installation verification
- ✅ Graceful fallback if Rich is not available

### Bash Script (Linux/Mac)

```bash
# Make executable
chmod +x install.sh

# Run installer
./install.sh
```

### Windows Batch Script

```cmd
# Run in Command Prompt
install.bat
```

---

## 📋 What the Installer Does

### 1. **System Checks**
   - ✅ Verifies Python 3.10+ is installed
   - ✅ Detects available package manager
   - ✅ Checks system compatibility

### 2. **Virtual Environment**
   - ✅ Creates isolated Python environment
   - ✅ Allows custom location selection
   - ✅ Handles existing venv gracefully

### 3. **Dependency Installation**
   - ✅ Upgrades pip, wheel, setuptools
   - ✅ Installs CodeAtlas in development mode
   - ✅ Option to install dev dependencies
   - ✅ Shows progress with beautiful UI

### 4. **Optional Tools**
   - ✅ Optionally installs security tools:
     - `bandit` - Python security linter
     - `safety` - Dependency vulnerability checker
     - `pip-audit` - Alternative dependency scanner
     - `pip-licenses` - License checker

### 5. **Verification**
   - ✅ Tests installation by running `codeatlas version`
   - ✅ Shows version information
   - ✅ Confirms successful installation

### 6. **Usage Instructions**
   - ✅ Shows activation commands
   - ✅ Provides usage examples
   - ✅ Suggests next steps

---

## 🎯 Installation Options

### Interactive Prompts

The installer will ask you:

1. **Virtual Environment Location**
   - Default: `venv` in project directory
   - You can specify any custom path

2. **Development Dependencies**
   - Install dev tools? (pytest, black, mypy, etc.)
   - Default: No

3. **Optional Security Tools**
   - Install bandit, safety, pip-audit?
   - Default: No

4. **Existing Virtual Environment**
   - If venv exists, option to recreate
   - Default: Keep existing

---

## 💻 Manual Installation

If you prefer manual installation:

```bash
# 1. Clone repository
git clone https://github.com/sarat1kyan/CodeAtlas.git
cd CodeAtlas

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install CodeAtlas
pip install -e .

# 5. (Optional) Install dev dependencies
pip install -e ".[dev]"

# 6. (Optional) Install security tools
pip install bandit safety pip-audit pip-licenses
```

---

## ✅ Verification

After installation, verify it works:

```bash
# Activate virtual environment first
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Check version
codeatlas version

# Run a scan
codeatlas scan .

# Get help
codeatlas --help
```

---

## 🔧 Troubleshooting

### Python Version Error

**Error:** `Python 3.10+ is required!`

**Solution:**
- Install Python 3.10 or higher
- Download from [python.org](https://www.python.org/downloads/)

### pip Not Found

**Error:** `No package manager found!`

**Solution:**
```bash
# Install pip
python -m ensurepip --upgrade

# Or on Linux/Mac
sudo apt-get install python3-pip  # Debian/Ubuntu
brew install python3              # macOS
```

### Virtual Environment Creation Fails

**Error:** `Failed to create virtual environment`

**Solution:**
- Ensure you have write permissions in the directory
- Try a different location
- Check Python venv module is available: `python -m venv --help`

### Installation Fails

**Error:** `Failed to install dependencies`

**Solution:**
- Check internet connection
- Try upgrading pip: `python -m pip install --upgrade pip`
- Check if you're in the correct directory
- Try installing without dev dependencies first

### Rich Not Available

**Note:** The installer works without Rich, but with less beautiful output. To get the full experience:

```bash
pip install rich
```

---

## 🎨 Installation Experience

### With Rich (Beautiful UI)

- 🎨 Color-coded output
- 📊 Progress bars and spinners
- 🎯 Interactive prompts
- 📋 Beautiful panels and tables
- ✅ Clear success/error indicators

### Without Rich (Fallback)

- ✅ Still fully functional
- ✅ Plain text output
- ✅ All features work
- ✅ Clear messages

---

## 🚀 Quick Start After Installation

```bash
# 1. Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Run comprehensive analysis
codeatlas scan . --all

# 3. Or get a quick summary
codeatlas summary .

# 4. Check security
codeatlas security .

# 5. View all commands
codeatlas --help
```

---

## 📝 Notes

- The installer creates an isolated virtual environment
- All dependencies are installed in the venv
- CodeAtlas is installed in editable mode (`-e`)
- You can customize the venv location
- Optional tools enhance security scanning
- Installation is verified automatically

---

## 🎉 Success!

Once installation completes, you'll see:

- ✅ Installation verified
- ✅ Usage instructions
- ✅ Next steps suggestions
- ✅ Activation commands

**You're ready to use CodeAtlas!** 🚀

