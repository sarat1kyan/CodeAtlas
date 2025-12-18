#!/usr/bin/env python3
"""
Installation script for CodeAtlas.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    
    class Confirm:
        @staticmethod
        def ask(prompt, default=False):
            default_text = "Y/n" if default else "y/N"
            response = input(f"{prompt} [{default_text}]: ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes']
    
    class Prompt:
        @staticmethod
        def ask(prompt, default=""):
            if default:
                response = input(f"{prompt} [{default}]: ").strip()
                return response if response else default
            return input(f"{prompt}: ").strip()
    
    class Progress:
        def __init__(self, *args, **kwargs):
            self.console = None
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            pass
        
        def add_task(self, *args, **kwargs):
            return None
        
        def update(self, *args, **kwargs):
            pass
    
    class SpinnerColumn:
        pass
    
    class TextColumn:
        pass
    
    class BarColumn:
        pass
    
    class TaskProgressColumn:
        pass

if RICH_AVAILABLE:
    console = Console()
else:
    console = Console()


def print_header():
    """Print beautiful header."""
    if RICH_AVAILABLE:
        header = Text()
        header.append("🗺️  ", style="bold cyan")
        header.append("CodeAtlas", style="bold white")
        header.append(" Installation", style="bold cyan")
        
        console.print()
        console.print(Panel.fit(
            header,
            border_style="cyan",
            padding=(1, 2),
        ))
        console.print()
    else:
        print("\n🗺️  CodeAtlas Installation\n")


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        if RICH_AVAILABLE:
            console.print("[bold red]❌ Error: Python 3.10+ is required![/bold red]")
            console.print(f"[yellow]Current version: {version.major}.{version.minor}.{version.micro}[/yellow]")
        else:
            print(f"❌ Error: Python 3.10+ is required! Current: {version.major}.{version.minor}.{version.micro}")
        return False
    
    if RICH_AVAILABLE:
        console.print(f"[green]✅ Python {version.major}.{version.minor}.{version.micro} detected[/green]")
    else:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def detect_package_manager() -> Optional[str]:
    """Detect available package manager."""
    managers = {
        "pip": ["pip", "--version"],
        "pip3": ["pip3", "--version"],
        "poetry": ["poetry", "--version"],
        "pipenv": ["pipenv", "--version"],
    }
    
    detected = []
    
    for name, cmd in managers.items():
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                detected.append(name)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    if not detected:
        return None
    
    # Prefer pip or pip3
    if "pip" in detected:
        return "pip"
    if "pip3" in detected:
        return "pip3"
    
    # Fallback to first available
    return detected[0]


def create_venv(venv_path: Path, force: bool = False) -> bool:
    """Create virtual environment."""
    if venv_path.exists():
        if not force:
            if RICH_AVAILABLE:
                if not Confirm.ask(f"[yellow]Virtual environment already exists at {venv_path}. Recreate?[/yellow]"):
                    return True
            else:
                response = input(f"Virtual environment already exists at {venv_path}. Recreate? (y/n): ")
                if response.lower() != 'y':
                    return True
        
        if RICH_AVAILABLE:
            console.print(f"[yellow]Removing existing virtual environment...[/yellow]")
        else:
            print("Removing existing virtual environment...")
        
        try:
            shutil.rmtree(venv_path)
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]❌ Failed to remove existing venv: {e}[/red]")
            else:
                print(f"❌ Failed to remove existing venv: {e}")
            return False
    
    if RICH_AVAILABLE:
        console.print(f"[cyan]Creating virtual environment at {venv_path}...[/cyan]")
    else:
        print(f"Creating virtual environment at {venv_path}...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )
        
        if RICH_AVAILABLE:
            console.print("[green]✅ Virtual environment created successfully[/green]")
        else:
            print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Failed to create virtual environment: {e}[/red]")
        else:
            print(f"❌ Failed to create virtual environment: {e}")
        return False


def get_venv_python(venv_path: Path) -> Path:
    """Get Python executable path in virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip(venv_path: Path) -> Path:
    """Get pip executable path in virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def install_dependencies(venv_path: Path, project_path: Path, use_dev: bool = False) -> bool:
    """Install dependencies."""
    pip_path = get_venv_pip(venv_path)
    
    if not pip_path.exists():
        if RICH_AVAILABLE:
            console.print("[red]❌ pip not found in virtual environment[/red]")
        else:
            print("❌ pip not found in virtual environment")
        return False
    
    if RICH_AVAILABLE:
        console.print("[cyan]Installing dependencies...[/cyan]")
    else:
        print("Installing dependencies...")
    
    # Upgrade pip first
    try:
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Upgrading pip...", total=None)
                subprocess.run(
                    [str(pip_path), "install", "--upgrade", "pip", "wheel", "setuptools"],
                    check=True,
                    capture_output=True,
                )
                progress.update(task, completed=100)
        else:
            print("Upgrading pip...")
            subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip", "wheel", "setuptools"],
                check=True,
                capture_output=True,
            )
    except subprocess.CalledProcessError as e:
        if RICH_AVAILABLE:
            console.print(f"[yellow]⚠️  Warning: Failed to upgrade pip: {e}[/yellow]")
        else:
            print(f"⚠️  Warning: Failed to upgrade pip: {e}")
    
    # Install the package - try multiple strategies
    install_strategies = [
        # Strategy 1: Standard editable install
        {
            "name": "Standard installation",
            "cmd": [str(pip_path), "install", "-e", "."] + ([".[dev]"] if use_dev else []),
        },
        # Strategy 2: With --no-build-isolation (sometimes helps with conflicts)
        {
            "name": "Installation without build isolation",
            "cmd": [str(pip_path), "install", "-e", ".", "--no-build-isolation"] + ([".[dev]"] if use_dev else []),
        },
        # Strategy 3: Install dependencies first, then package
        {
            "name": "Two-step installation",
            "cmd": None,  # Special handling below
        },
        # Strategy 4: Use --use-pep517
        {
            "name": "Installation with PEP 517",
            "cmd": [str(pip_path), "install", "-e", ".", "--use-pep517"] + ([".[dev]"] if use_dev else []),
        },
    ]
    
    for strategy_idx, strategy in enumerate(install_strategies, 1):
        try:
            if RICH_AVAILABLE:
                console.print(f"[cyan]Trying {strategy['name']}...[/cyan]")
            else:
                print(f"Trying {strategy['name']}...")
            
            # Special handling for two-step installation
            if strategy["cmd"] is None:
                # Get dependencies from pyproject.toml and install them first
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib
                    except ImportError:
                        tomllib = None
                
                if tomllib:
                    pyproject_path = project_path / "pyproject.toml"
                    if pyproject_path.exists():
                        with open(pyproject_path, "rb") as f:
                            data = tomllib.load(f)
                            deps = data.get("project", {}).get("dependencies", [])
                            if use_dev:
                                dev_deps = data.get("project", {}).get("optional-dependencies", {}).get("dev", [])
                                deps.extend(dev_deps)
                            
                            # Install dependencies one by one (more lenient)
                            failed_deps = []
                            for dep in deps:
                                # Parse dependency string (e.g., "rich>=13.7.0" or "tomli>=2.0.0; python_version < '3.11'")
                                dep_spec = dep.split(";")[0].strip()
                                if dep_spec:
                                    dep_install_cmd = [str(pip_path), "install", dep_spec]
                                    dep_result = subprocess.run(
                                        dep_install_cmd,
                                        cwd=project_path,
                                        capture_output=True,
                                        text=True,
                                    )
                                    if dep_result.returncode != 0:
                                        failed_deps.append(dep_spec)
                                        if RICH_AVAILABLE:
                                            console.print(f"[dim yellow]⚠️  Could not install {dep_spec.split('>=')[0].split('==')[0].split('<')[0].split('>')[0].strip()}, continuing...[/dim yellow]")
                                        else:
                                            print(f"⚠️  Could not install {dep_spec}, continuing...")
                            
                            # Now install the package (even if some deps failed)
                            install_cmd = [str(pip_path), "install", "-e", "."] + ([".[dev]"] if use_dev else [])
                            result = subprocess.run(
                                install_cmd,
                                cwd=project_path,
                                capture_output=True,
                                text=True,
                            )
                    else:
                        # No pyproject.toml, use standard install
                        install_cmd = [str(pip_path), "install", "-e", "."] + ([".[dev]"] if use_dev else [])
                        result = subprocess.run(
                            install_cmd,
                            cwd=project_path,
                            capture_output=True,
                            text=True,
                        )
                else:
                    # Can't parse, use standard install
                    install_cmd = [str(pip_path), "install", "-e", "."] + ([".[dev]"] if use_dev else [])
                    result = subprocess.run(
                        install_cmd,
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                    )
            else:
                # Standard command execution
                if RICH_AVAILABLE:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TaskProgressColumn(),
                        console=console,
                    ) as progress:
                        task = progress.add_task(f"[green]{strategy['name']}...", total=None)
                        result = subprocess.run(
                            strategy["cmd"],
                            cwd=project_path,
                            capture_output=True,
                            text=True,
                        )
                        progress.update(task, completed=100)
                else:
                    result = subprocess.run(
                        strategy["cmd"],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                    )
            
            if result.returncode == 0:
                if RICH_AVAILABLE:
                    console.print(f"[green]✅ Dependencies installed successfully using {strategy['name']}[/green]")
                else:
                    print(f"✅ Dependencies installed successfully using {strategy['name']}")
                return True
            else:
                # Show error but continue to next strategy
                if strategy_idx < len(install_strategies):
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]⚠️  {strategy['name']} failed, trying next method...[/yellow]")
                        if result.stderr:
                            console.print(f"[dim]{result.stderr[:500]}...[/dim]")
                    else:
                        print(f"⚠️  {strategy['name']} failed, trying next method...")
                        if result.stderr:
                            print(result.stderr[:500])
                else:
                    # Last strategy failed, show full error
                    if RICH_AVAILABLE:
                        console.print("[red]❌ All installation strategies failed[/red]")
                        console.print()
                        console.print(Panel(
                            result.stderr or result.stdout or "Unknown error",
                            title="[bold red]Error Details[/bold red]",
                            border_style="red",
                        ))
                        console.print()
                        console.print("[yellow]💡 Troubleshooting tips:[/yellow]")
                        console.print("  • Try updating pip: pip install --upgrade pip")
                        console.print("  • Check Python version compatibility (requires Python 3.10+)")
                        console.print("  • Try installing without dev dependencies")
                        console.print("  • Check for conflicting packages in your environment")
                    else:
                        print("❌ All installation strategies failed")
                        print("\nError details:")
                        print(result.stderr or result.stdout or "Unknown error")
                        print("\nTroubleshooting tips:")
                        print("  • Try updating pip: pip install --upgrade pip")
                        print("  • Check Python version compatibility (requires Python 3.10+)")
                        print("  • Try installing without dev dependencies")
                        print("  • Check for conflicting packages in your environment")
                    return False
        except Exception as e:
            if strategy_idx < len(install_strategies):
                if RICH_AVAILABLE:
                    console.print(f"[yellow]⚠️  {strategy['name']} encountered an error: {e}[/yellow]")
                else:
                    print(f"⚠️  {strategy['name']} encountered an error: {e}")
                continue
            else:
                if RICH_AVAILABLE:
                    console.print(f"[red]❌ Error installing dependencies: {e}[/red]")
                else:
                    print(f"❌ Error installing dependencies: {e}")
                return False
    
    return False


def install_optional_tools(venv_path: Path) -> bool:
    """Install optional security tools."""
    if RICH_AVAILABLE:
        install_optional = Confirm.ask(
            "[yellow]Install optional security tools? (bandit, safety, pip-audit)[/yellow]",
            default=False,
        )
    else:
        response = input("Install optional security tools? (bandit, safety, pip-audit) (y/n): ")
        install_optional = response.lower() == 'y'
    
    if not install_optional:
        return True
    
    pip_path = get_venv_pip(venv_path)
    optional_tools = ["bandit", "safety", "pip-audit", "pip-licenses"]
    
    if RICH_AVAILABLE:
        console.print("[cyan]Installing optional tools...[/cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[green]Installing tools...", total=len(optional_tools))
            
            for tool in optional_tools:
                try:
                    subprocess.run(
                        [str(pip_path), "install", tool],
                        check=True,
                        capture_output=True,
                    )
                    progress.advance(task)
                except subprocess.CalledProcessError:
                    pass
            
            progress.update(task, completed=len(optional_tools))
    else:
        print("Installing optional tools...")
        for tool in optional_tools:
            try:
                subprocess.run(
                    [str(pip_path), "install", tool],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                pass
    
    if RICH_AVAILABLE:
        console.print("[green]✅ Optional tools installation completed[/green]")
    else:
        print("✅ Optional tools installation completed")
    
    return True


def verify_installation(venv_path: Path) -> bool:
    """Verify installation by running codeatlas --version."""
    python_path = get_venv_python(venv_path)
    
    if platform.system() == "Windows":
        codeatlas_path = venv_path / "Scripts" / "codeatlas.exe"
    else:
        codeatlas_path = venv_path / "bin" / "codeatlas"
    
    if RICH_AVAILABLE:
        console.print("[cyan]Verifying installation...[/cyan]")
    else:
        print("Verifying installation...")
    
    try:
        result = subprocess.run(
            [str(codeatlas_path), "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode == 0:
            if RICH_AVAILABLE:
                console.print("[green]✅ Installation verified successfully![/green]")
                console.print()
                console.print(Panel(
                    result.stdout.strip(),
                    title="[bold green]CodeAtlas Version[/bold green]",
                    border_style="green",
                ))
            else:
                print("✅ Installation verified successfully!")
                print(result.stdout)
            return True
        else:
            if RICH_AVAILABLE:
                console.print("[yellow]⚠️  Installation completed but verification failed[/yellow]")
            else:
                print("⚠️  Installation completed but verification failed")
            return False
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[yellow]⚠️  Could not verify installation: {e}[/yellow]")
        else:
            print(f"⚠️  Could not verify installation: {e}")
        return False


def show_usage_instructions(venv_path: Path):
    """Show usage instructions after installation."""
    if RICH_AVAILABLE:
        console.print()
        
        # Determine activation command
        if platform.system() == "Windows":
            activate_cmd = f"{venv_path}\\Scripts\\activate"
            activate_ps_cmd = f"{venv_path}\\Scripts\\Activate.ps1"
            codeatlas_cmd = f"{venv_path}\\Scripts\\codeatlas.exe"
        else:
            activate_cmd = f"source {venv_path}/bin/activate"
            activate_ps_cmd = None
            codeatlas_cmd = f"{venv_path}/bin/codeatlas"
        
        instructions = f"""
[bold cyan]🚀 Getting Started:[/bold cyan]

1. [bold]Activate the virtual environment:[/bold]
   [dim]{activate_cmd}[/dim]"""
        
        if platform.system() == "Windows":
            instructions += f"""
   [dim]Or in PowerShell: {activate_ps_cmd}[/dim]"""
        
        instructions += f"""

2. [bold]Run CodeAtlas:[/bold]
   [dim]{codeatlas_cmd} --help[/dim]
   or
   [dim]codeatlas scan .[/dim]

3. [bold]Or use directly (without activation):[/bold]
   [dim]{codeatlas_cmd} scan .[/dim]

[bold yellow]💡 Tip:[/bold yellow] Add the venv Scripts/bin directory to your PATH for easier access.

[bold cyan]📚 Next Steps:[/bold cyan]
   • Run [dim]codeatlas summary .[/dim] for a complete overview
   • Try [dim]codeatlas scan . --all[/dim] for comprehensive analysis
   • Check [dim]codeatlas --help[/dim] for all available commands
"""
        
        console.print(Panel(
            instructions,
            title="[bold green]✅ Installation Complete![/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print()
    else:
        print("\n✅ Installation Complete!\n")
        if platform.system() == "Windows":
            print(f"Activate: {venv_path}\\Scripts\\activate")
            print(f"Or PowerShell: {venv_path}\\Scripts\\Activate.ps1")
        else:
            print(f"Activate: source {venv_path}/bin/activate")
        print(f"Run: codeatlas --help")
        print(f"Or: codeatlas scan .")
        print(f"\nNext steps:")
        print(f"  • codeatlas summary .")
        print(f"  • codeatlas scan . --all")
        print()


def find_venv_locations(project_path: Path) -> List[Path]:
    """Find potential virtual environment locations."""
    potential_locations = [
        project_path / "venv",
        project_path / ".venv",
        project_path / "env",
        Path.home() / ".codeatlas" / "venv",
    ]
    
    found = []
    for loc in potential_locations:
        if loc.exists():
            # Check if it's actually a venv
            if platform.system() == "Windows":
                python_exe = loc / "Scripts" / "python.exe"
            else:
                python_exe = loc / "bin" / "python"
            
            if python_exe.exists():
                found.append(loc)
    
    return found


def uninstall_codeatlas(venv_path: Optional[Path] = None, remove_config: bool = False) -> bool:
    """Uninstall CodeAtlas by removing virtual environment and optionally config."""
    project_path = Path(__file__).parent.resolve()
    
    if RICH_AVAILABLE:
        console.print()
        console.print(Panel.fit(
            "[bold red]🗑️  CodeAtlas Uninstall[/bold red]",
            border_style="red"
        ))
        console.print()
    else:
        print("\n🗑️  CodeAtlas Uninstall\n")
    
    # Find venv if not provided
    if venv_path is None:
        found_venvs = find_venv_locations(project_path)
        
        if not found_venvs:
            if RICH_AVAILABLE:
                console.print("[yellow]⚠️  No virtual environment found to uninstall[/yellow]")
            else:
                print("⚠️  No virtual environment found to uninstall")
            return False
        
        if len(found_venvs) == 1:
            venv_path = found_venvs[0]
            if RICH_AVAILABLE:
                console.print(f"[cyan]Found virtual environment: {venv_path}[/cyan]")
            else:
                print(f"Found virtual environment: {venv_path}")
        else:
            if RICH_AVAILABLE:
                console.print("[yellow]Multiple virtual environments found:[/yellow]")
                for idx, venv in enumerate(found_venvs, 1):
                    console.print(f"  {idx}. {venv}")
                
                choice = Prompt.ask(
                    "[cyan]Select virtual environment to remove (number)[/cyan]",
                    default="1",
                )
            else:
                print("Multiple virtual environments found:")
                for idx, venv in enumerate(found_venvs, 1):
                    print(f"  {idx}. {venv}")
                choice = input("Select virtual environment to remove (number) [1]: ").strip() or "1"
            
            try:
                venv_path = found_venvs[int(choice) - 1]
            except (ValueError, IndexError):
                if RICH_AVAILABLE:
                    console.print("[red]❌ Invalid selection[/red]")
                else:
                    print("❌ Invalid selection")
                return False
    
    if not venv_path.exists():
        if RICH_AVAILABLE:
            console.print(f"[red]❌ Virtual environment not found: {venv_path}[/red]")
        else:
            print(f"❌ Virtual environment not found: {venv_path}")
        return False
    
    # Confirm removal
    if RICH_AVAILABLE:
        confirmed = Confirm.ask(
            f"[bold red]⚠️  Remove virtual environment at {venv_path}?[/bold red]",
            default=False,
        )
    else:
        response = input(f"⚠️  Remove virtual environment at {venv_path}? (y/N): ").strip().lower()
        confirmed = response in ['y', 'yes']
    
    if not confirmed:
        if RICH_AVAILABLE:
            console.print("[yellow]Uninstall cancelled[/yellow]")
        else:
            print("Uninstall cancelled")
        return False
    
    # Remove virtual environment
    if RICH_AVAILABLE:
        console.print(f"[cyan]Removing virtual environment...[/cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[red]Removing files...", total=None)
            try:
                shutil.rmtree(venv_path)
                progress.update(task, completed=100)
            except Exception as e:
                progress.update(task, completed=100)
                raise e
    else:
        print("Removing virtual environment...")
        try:
            shutil.rmtree(venv_path)
        except Exception as e:
            raise e
    
    if RICH_AVAILABLE:
        console.print("[green]✅ Virtual environment removed successfully[/green]")
    else:
        print("✅ Virtual environment removed successfully")
    
    # Remove config files if requested
    if remove_config:
        config_paths = [
            project_path / ".codeatlas",
            Path.home() / ".config" / "CodeAtlas",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    if config_path.is_file():
                        config_path.unlink()
                    else:
                        shutil.rmtree(config_path)
                    if RICH_AVAILABLE:
                        console.print(f"[green]✅ Removed config: {config_path}[/green]")
                    else:
                        print(f"✅ Removed config: {config_path}")
                except Exception as e:
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]⚠️  Could not remove {config_path}: {e}[/yellow]")
                    else:
                        print(f"⚠️  Could not remove {config_path}: {e}")
    
    if RICH_AVAILABLE:
        console.print()
        console.print(Panel(
            "[bold green]✅ CodeAtlas has been uninstalled successfully![/bold green]\n\n"
            "[dim]All virtual environment files have been removed.[/dim]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print()
    else:
        print("\n✅ CodeAtlas has been uninstalled successfully!")
        print("All virtual environment files have been removed.\n")
    
    return True


def main():
    """Main installation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CodeAtlas Installation Script")
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall CodeAtlas (remove virtual environment)",
    )
    parser.add_argument(
        "--remove-config",
        action="store_true",
        help="Also remove configuration files (use with --uninstall)",
    )
    parser.add_argument(
        "--venv-path",
        type=str,
        help="Specify virtual environment path (for uninstall)",
    )
    
    args = parser.parse_args()
    
    # Handle uninstall
    if args.uninstall:
        venv_path = Path(args.venv_path).resolve() if args.venv_path else None
        uninstall_codeatlas(venv_path, remove_config=args.remove_config)
        return
    
    # Normal installation flow
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Get project path
    project_path = Path(__file__).parent.resolve()
    
    if RICH_AVAILABLE:
        console.print(f"[dim]Project path: {project_path}[/dim]")
        console.print()
    
    # Detect package manager
    package_manager = detect_package_manager()
    if package_manager:
        if RICH_AVAILABLE:
            console.print(f"[green]✅ Package manager detected: {package_manager}[/green]")
        else:
            print(f"✅ Package manager detected: {package_manager}")
    else:
        if RICH_AVAILABLE:
            console.print("[red]❌ No package manager found! Please install pip.[/red]")
        else:
            print("❌ No package manager found! Please install pip.")
        sys.exit(1)
    
    # Ask for venv location
    if RICH_AVAILABLE:
        default_venv = project_path / "venv"
        venv_location = Prompt.ask(
            "[cyan]Virtual environment location[/cyan]",
            default=str(default_venv),
        )
        venv_path = Path(venv_location).resolve()
        
        use_dev = Confirm.ask(
            "[yellow]Install development dependencies?[/yellow]",
            default=False,
        )
    else:
        default_venv = project_path / "venv"
        venv_location = input(f"Virtual environment location [{default_venv}]: ").strip()
        venv_path = Path(venv_location if venv_location else default_venv).resolve()
        
        response = input("Install development dependencies? (y/n): ")
        use_dev = response.lower() == 'y'
    
    console.print()
    
    # Create virtual environment
    if not create_venv(venv_path):
        sys.exit(1)
    
    console.print()
    
    # Install dependencies
    if not install_dependencies(venv_path, project_path, use_dev=use_dev):
        sys.exit(1)
    
    console.print()
    
    # Install optional tools
    install_optional_tools(venv_path)
    
    console.print()
    
    # Verify installation
    verify_installation(venv_path)
    
    # Show usage instructions
    show_usage_instructions(venv_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]Installation cancelled by user[/yellow]")
        else:
            print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n[red]❌ Installation failed: {e}[/red]")
        else:
            print(f"\n❌ Installation failed: {e}")
        sys.exit(1)

