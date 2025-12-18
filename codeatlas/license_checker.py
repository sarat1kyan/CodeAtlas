"""License checker for analyzing project and dependency licenses."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class LicenseInfo:
    """Information about a license."""

    name: str
    spdx_id: Optional[str] = None
    is_osi_approved: bool = False
    is_fsf_approved: bool = False
    risk_level: str = "unknown"  # low, medium, high, unknown


@dataclass
class LicenseCheckResult:
    """Results from license checking."""

    project_license: Optional[LicenseInfo] = None
    dependency_licenses: Dict[str, LicenseInfo] = field(default_factory=dict)
    incompatible_licenses: List[str] = field(default_factory=list)
    unlicensed_dependencies: List[str] = field(default_factory=list)
    total_dependencies_checked: int = 0


class LicenseChecker:
    """Checks licenses for project and dependencies."""

    # Common license mappings
    LICENSE_MAPPINGS: Dict[str, str] = {
        "MIT": "MIT",
        "Apache-2.0": "Apache-2.0",
        "Apache 2.0": "Apache-2.0",
        "GPL-3.0": "GPL-3.0",
        "GPL-2.0": "GPL-2.0",
        "BSD-3-Clause": "BSD-3-Clause",
        "BSD-2-Clause": "BSD-2-Clause",
        "ISC": "ISC",
        "LGPL-3.0": "LGPL-3.0",
        "LGPL-2.1": "LGPL-2.1",
        "MPL-2.0": "MPL-2.0",
        "Unlicense": "Unlicense",
        "CC0-1.0": "CC0-1.0",
    }

    # OSI approved licenses
    OSI_APPROVED = {
        "MIT",
        "Apache-2.0",
        "GPL-3.0",
        "GPL-2.0",
        "BSD-3-Clause",
        "BSD-2-Clause",
        "ISC",
        "LGPL-3.0",
        "LGPL-2.1",
        "MPL-2.0",
        "Unlicense",
        "CC0-1.0",
    }

    # FSF approved licenses
    FSF_APPROVED = {
        "MIT",
        "Apache-2.0",
        "GPL-3.0",
        "GPL-2.0",
        "BSD-3-Clause",
        "BSD-2-Clause",
        "ISC",
        "LGPL-3.0",
        "LGPL-2.1",
        "MPL-2.0",
    }

    # High-risk licenses (copyleft, restrictive)
    HIGH_RISK_LICENSES = {"GPL-3.0", "GPL-2.0", "AGPL-3.0", "LGPL-3.0", "LGPL-2.1"}

    def __init__(self, project_path: Path):
        """Initialize license checker."""
        self.project_path = project_path.resolve()

    def check(self) -> LicenseCheckResult:
        """Check licenses for project and dependencies."""
        result = LicenseCheckResult()

        # Check project license
        result.project_license = self._check_project_license()

        # Check dependency licenses
        if self._is_python_project():
            deps = self._check_python_licenses()
            result.dependency_licenses.update(deps)

        if self._is_nodejs_project():
            deps = self._check_nodejs_licenses()
            result.dependency_licenses.update(deps)

        result.total_dependencies_checked = len(result.dependency_licenses)

        # Find incompatible licenses
        if result.project_license:
            for dep_name, dep_license in result.dependency_licenses.items():
                if self._are_incompatible(result.project_license, dep_license):
                    result.incompatible_licenses.append(f"{dep_name}: {dep_license.name}")

        # Find unlicensed dependencies
        for dep_name, dep_license in result.dependency_licenses.items():
            if dep_license.name.lower() in ("unknown", "none", "unlicensed", ""):
                result.unlicensed_dependencies.append(dep_name)

        return result

    def _is_python_project(self) -> bool:
        """Check if this is a Python project."""
        return (
            (self.project_path / "setup.py").exists()
            or (self.project_path / "pyproject.toml").exists()
            or (self.project_path / "requirements.txt").exists()
        )

    def _is_nodejs_project(self) -> bool:
        """Check if this is a Node.js project."""
        return (self.project_path / "package.json").exists()

    def _check_project_license(self) -> Optional[LicenseInfo]:
        """Check the project's own license."""
        # Check pyproject.toml
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Simple parsing for license field
                    for line in content.split("\n"):
                        if "license" in line.lower() and "=" in line:
                            license_text = line.split("=")[1].strip().strip('"').strip("'")
                            return self._parse_license(license_text)
            except Exception:
                pass

        # Check setup.py
        setup_py = self.project_path / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Look for license field
                    if "license" in content.lower():
                        # Try to extract license
                        import re
                        match = re.search(r'license\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
                        if match:
                            return self._parse_license(match.group(1))
            except Exception:
                pass

        # Check package.json
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    license_field = data.get("license", "")
                    if license_field:
                        return self._parse_license(license_field)
            except Exception:
                pass

        # Check LICENSE file
        license_files = ["LICENSE", "LICENSE.txt", "LICENCE", "LICENCE.txt"]
        for license_file in license_files:
            license_path = self.project_path / license_file
            if license_path.exists():
                try:
                    with open(license_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()[:500]  # Read first 500 chars
                        # Try to identify license from content
                        if "MIT" in content:
                            return self._parse_license("MIT")
                        elif "Apache" in content:
                            return self._parse_license("Apache-2.0")
                        elif "GPL" in content:
                            return self._parse_license("GPL-3.0")
                except Exception:
                    pass

        return None

    def _check_python_licenses(self) -> Dict[str, LicenseInfo]:
        """Check Python dependency licenses."""
        licenses: Dict[str, LicenseInfo] = {}

        try:
            # Try to use pip-licenses if available
            result = subprocess.run(
                ["pip-licenses", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_path,
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for pkg in data:
                        name = pkg.get("Name", "")
                        license_text = pkg.get("License", "unknown")
                        licenses[name] = self._parse_license(license_text)
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            # Fallback: try to get from package metadata
            try:
                result = subprocess.run(
                    ["pip", "show", "-f"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                # This is a fallback - pip show doesn't easily list all packages
                # In a real implementation, you'd iterate through installed packages
            except Exception:
                pass

        return licenses

    def _check_nodejs_licenses(self) -> Dict[str, LicenseInfo]:
        """Check Node.js dependency licenses."""
        licenses: Dict[str, LicenseInfo] = {}
        package_json = self.project_path / "package.json"

        if not package_json.exists():
            return licenses

        try:
            # Try license-checker if available
            result = subprocess.run(
                ["license-checker", "--json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_path,
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for pkg_name, pkg_data in data.items():
                        license_text = pkg_data.get("licenses", "unknown")
                        if isinstance(license_text, list):
                            license_text = license_text[0] if license_text else "unknown"
                        licenses[pkg_name] = self._parse_license(str(license_text))
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            # Fallback: read package.json and try to infer
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    # Without license-checker, we can't easily get dependency licenses
                    # This would require reading each package's package.json
            except Exception:
                pass

        return licenses

    def _parse_license(self, license_text: str) -> LicenseInfo:
        """Parse license text into LicenseInfo."""
        if not license_text or license_text.lower() in ("unknown", "none", "unlicensed"):
            return LicenseInfo(name="Unknown", risk_level="unknown")

        license_text = license_text.strip()

        # Try to find matching SPDX ID
        spdx_id = None
        for key, value in self.LICENSE_MAPPINGS.items():
            if key.lower() in license_text.lower():
                spdx_id = value
                break

        if not spdx_id:
            # Use the text as-is
            spdx_id = license_text

        is_osi = spdx_id in self.OSI_APPROVED
        is_fsf = spdx_id in self.FSF_APPROVED

        # Determine risk level
        if spdx_id in self.HIGH_RISK_LICENSES:
            risk_level = "high"
        elif is_osi or is_fsf:
            risk_level = "low"
        else:
            risk_level = "medium"

        return LicenseInfo(
            name=license_text,
            spdx_id=spdx_id,
            is_osi_approved=is_osi,
            is_fsf_approved=is_fsf,
            risk_level=risk_level,
        )

    def _are_incompatible(self, license1: LicenseInfo, license2: LicenseInfo) -> bool:
        """Check if two licenses are incompatible."""
        # GPL is incompatible with many proprietary licenses
        if license1.spdx_id in {"GPL-3.0", "GPL-2.0"} and license2.spdx_id not in {
            "GPL-3.0",
            "GPL-2.0",
            "LGPL-3.0",
            "LGPL-2.1",
        }:
            return True

        if license2.spdx_id in {"GPL-3.0", "GPL-2.0"} and license1.spdx_id not in {
            "GPL-3.0",
            "GPL-2.0",
            "LGPL-3.0",
            "LGPL-2.1",
        }:
            return True

        return False

