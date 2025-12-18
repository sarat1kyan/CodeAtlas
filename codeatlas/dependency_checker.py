"""Dependency checker for analyzing project dependencies."""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class Dependency:
    """Represents a project dependency."""

    name: str
    version: str
    latest_version: Optional[str] = None
    is_outdated: bool = False
    license: Optional[str] = None
    homepage: Optional[str] = None
    description: Optional[str] = None


@dataclass
class DependencyCheckResult:
    """Results from dependency checking."""

    total_dependencies: int
    outdated_count: int
    dependencies: List[Dependency] = field(default_factory=list)
    package_manager: Optional[str] = None
    lock_file_exists: bool = False


class DependencyChecker:
    """Checks project dependencies for updates, licenses, and issues."""

    def __init__(self, project_path: Path):
        """Initialize dependency checker."""
        self.project_path = project_path.resolve()

    def check(self) -> DependencyCheckResult:
        """Check all dependencies in the project."""
        result = DependencyCheckResult(total_dependencies=0, outdated_count=0)

        # Python dependencies
        if self._is_python_project():
            python_deps = self._check_python_dependencies()
            result.dependencies.extend(python_deps)
            result.package_manager = "pip"
            if (self.project_path / "poetry.lock").exists():
                result.package_manager = "poetry"
                result.lock_file_exists = True
            elif (self.project_path / "Pipfile.lock").exists():
                result.package_manager = "pipenv"
                result.lock_file_exists = True
            elif (self.project_path / "requirements.txt").exists():
                result.lock_file_exists = False

        # Node.js dependencies
        if self._is_nodejs_project():
            node_deps = self._check_nodejs_dependencies()
            result.dependencies.extend(node_deps)
            if result.package_manager:
                result.package_manager += " + npm"
            else:
                result.package_manager = "npm"
            # Check for lock files in root and subdirectories
            lock_files = list(self.project_path.glob("**/package-lock.json")) + list(self.project_path.glob("**/yarn.lock"))
            # Filter out node_modules
            lock_files = [f for f in lock_files if "node_modules" not in str(f)]
            if lock_files:
                result.lock_file_exists = True

        # Go dependencies
        if self._is_go_project():
            go_deps = self._check_go_dependencies()
            result.dependencies.extend(go_deps)
            if result.package_manager:
                result.package_manager += " + go"
            else:
                result.package_manager = "go"
            if (self.project_path / "go.sum").exists():
                result.lock_file_exists = True

        # Rust dependencies
        if self._is_rust_project():
            rust_deps = self._check_rust_dependencies()
            result.dependencies.extend(rust_deps)
            if result.package_manager:
                result.package_manager += " + cargo"
            else:
                result.package_manager = "cargo"
            if (self.project_path / "Cargo.lock").exists():
                result.lock_file_exists = True

        result.total_dependencies = len(result.dependencies)
        result.outdated_count = sum(1 for dep in result.dependencies if dep.is_outdated)

        return result

    def _is_python_project(self) -> bool:
        """Check if this is a Python project."""
        return (
            (self.project_path / "setup.py").exists()
            or (self.project_path / "pyproject.toml").exists()
            or (self.project_path / "requirements.txt").exists()
            or (self.project_path / "Pipfile").exists()
            or (self.project_path / "poetry.lock").exists()
        )

    def _is_nodejs_project(self) -> bool:
        """Check if this is a Node.js project."""
        return (self.project_path / "package.json").exists()

    def _is_go_project(self) -> bool:
        """Check if this is a Go project."""
        return (self.project_path / "go.mod").exists() or (self.project_path / "Gopkg.toml").exists()

    def _is_rust_project(self) -> bool:
        """Check if this is a Rust project."""
        return (self.project_path / "Cargo.toml").exists()

    def _find_requirements_files(self) -> List[Path]:
        """Find all requirements.txt files recursively."""
        requirements_files: List[Path] = []
        
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "target", "build", "dist", ".pytest_cache"}
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            if "requirements.txt" in files:
                requirements_files.append(Path(root) / "requirements.txt")
        
        return requirements_files

    def _check_python_dependencies(self) -> List[Dependency]:
        """Check Python dependencies from all requirements files (monorepo support)."""
        dependencies: List[Dependency] = []
        deps_by_name: Dict[str, Dependency] = {}

        # Try to get installed packages
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path,
            )
            if result.returncode == 0:
                try:
                    packages = json.loads(result.stdout)
                    for pkg in packages:
                        name = pkg.get("name", "")
                        version = pkg.get("version", "")
                        if name:
                            deps_by_name[name.lower()] = Dependency(name=name, version=version)
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        # Parse all requirements.txt files
        requirements_files = self._find_requirements_files()
        for requirements_file in requirements_files:
            try:
                with open(requirements_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Parse requirement line (e.g., "package==1.0.0" or "package>=1.0.0")
                            parts = line.split("==")
                            if len(parts) == 2:
                                name = parts[0].strip()
                                version = parts[1].strip()
                                # Check if already in dependencies
                                if name.lower() not in deps_by_name:
                                    deps_by_name[name.lower()] = Dependency(name=name, version=version)
            except Exception:
                pass

        dependencies = list(deps_by_name.values())

        # Check for outdated packages
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path,
            )
            if result.returncode == 0:
                try:
                    outdated = json.loads(result.stdout)
                    outdated_names = {pkg.get("name", "").lower(): pkg.get("version", "") for pkg in outdated}
                    for dep in dependencies:
                        if dep.name.lower() in outdated_names:
                            dep.is_outdated = True
                            dep.latest_version = outdated_names[dep.name.lower()]
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        return dependencies

    def _find_package_json_files(self) -> List[Path]:
        """Find all package.json files recursively, including subdirectories."""
        package_json_files: List[Path] = []
        
        # Skip common directories
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "target", "build", "dist", ".pytest_cache"}
        
        for root, dirs, files in os.walk(self.project_path):
            # Filter out skipped directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            if "package.json" in files:
                package_json_files.append(Path(root) / "package.json")
        
        return package_json_files

    def _check_nodejs_dependencies(self) -> List[Dependency]:
        """Check Node.js dependencies from all package.json files (monorepo support)."""
        dependencies: List[Dependency] = []
        package_json_files = self._find_package_json_files()

        if not package_json_files:
            return dependencies

        # Track dependencies by name to avoid duplicates, but keep track of locations
        deps_by_name: Dict[str, Dependency] = {}

        for package_json in package_json_files:
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Get dependencies
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}

                # Skip if this is just a root package.json with no dependencies (monorepo root)
                if not all_deps and package_json == self.project_path / "package.json":
                    continue

                for name, version_spec in all_deps.items():
                    # Clean version spec (remove ^, ~, etc.)
                    version = version_spec.replace("^", "").replace("~", "").replace(">=", "").replace("<=", "")
                    
                    # If we've seen this dependency before, keep the first one or merge info
                    if name not in deps_by_name:
                        dep = Dependency(name=name, version=version)
                        deps_by_name[name] = dep
                    else:
                        # Update if we have a more specific version
                        existing = deps_by_name[name]
                        if version and version != "unknown" and existing.version == "unknown":
                            existing.version = version

            except Exception as e:
                rel_path = package_json.relative_to(self.project_path)
                console.print(f"[yellow]Warning: Failed to parse {rel_path}: {e}[/yellow]")

        dependencies = list(deps_by_name.values())

        # Check for outdated packages in each directory with package.json
        for package_json in package_json_files:
            package_dir = package_json.parent
            try:
                result = subprocess.run(
                    ["npm", "outdated", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=package_dir,
                )
                if result.returncode != 0:  # npm outdated returns non-zero when outdated packages exist
                    try:
                        outdated = json.loads(result.stdout)
                        for name, info in outdated.items():
                            existing = next((d for d in dependencies if d.name == name), None)
                            if existing:
                                existing.is_outdated = True
                                if not existing.latest_version:
                                    existing.latest_version = info.get("latest", "")
                    except json.JSONDecodeError:
                        pass
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                pass

        return dependencies

    def _check_go_dependencies(self) -> List[Dependency]:
        """Check Go dependencies."""
        dependencies: List[Dependency] = []

        try:
            result = subprocess.run(
                ["go", "list", "-m", "-json", "all"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_path,
            )
            if result.returncode == 0:
                # Parse go list output (each package is a JSON object)
                current_pkg = {}
                for line in result.stdout.split("\n"):
                    if line.strip() == "}":
                        if current_pkg:
                            name = current_pkg.get("Path", "")
                            version = current_pkg.get("Version", "")
                            if name and version:
                                dependencies.append(Dependency(name=name, version=version))
                            current_pkg = {}
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        current_pkg[key.strip().strip('"')] = value.strip().strip('",')
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        return dependencies

    def _check_rust_dependencies(self) -> List[Dependency]:
        """Check Rust dependencies."""
        dependencies: List[Dependency] = []
        cargo_toml = self.project_path / "Cargo.toml"

        if not cargo_toml.exists():
            return dependencies

        try:
            # Try tomllib (Python 3.11+) first, then tomli
            try:
                import tomllib
                with open(cargo_toml, "rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                import tomli
                with open(cargo_toml, "rb") as f:
                    data = tomli.load(f)

            # Get dependencies
            deps = data.get("dependencies", {})
            dev_deps = data.get("dev-dependencies", {})

            for name, spec in {**deps, **dev_deps}.items():
                if isinstance(spec, dict):
                    version = spec.get("version", "unknown")
                elif isinstance(spec, str):
                    version = spec
                else:
                    version = "unknown"

                dependencies.append(Dependency(name=name, version=version))
        except ImportError:
            # Fallback: try to parse manually
            try:
                with open(cargo_toml, "r", encoding="utf-8") as f:
                    in_deps = False
                    for line in f:
                        if line.strip().startswith("[dependencies]") or line.strip().startswith(
                            "[dev-dependencies]"
                        ):
                            in_deps = True
                            continue
                        if line.strip().startswith("[") and in_deps:
                            break
                        if in_deps and "=" in line and not line.strip().startswith("#"):
                            parts = line.split("=")
                            if len(parts) >= 2:
                                name = parts[0].strip()
                                version_part = parts[1].strip().strip('"').strip("'")
                                dependencies.append(Dependency(name=name, version=version_part))
            except Exception:
                pass
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to parse Cargo.toml: {e}[/yellow]")

        return dependencies

