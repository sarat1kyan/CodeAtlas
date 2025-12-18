"""Security scanner for vulnerability detection and security analysis."""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class SecurityIssue:
    """Represents a security issue found in the codebase."""

    severity: str  # critical, high, medium, low, info
    rule_id: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None
    confidence: Optional[str] = None


@dataclass
class SecurityScanResult:
    """Results from security scanning."""

    total_issues: int
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues: List[SecurityIssue] = field(default_factory=list)
    dependency_vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    scan_tools: List[str] = field(default_factory=list)


class SecurityScanner:
    """Scans codebase for security vulnerabilities and issues."""

    def __init__(self, project_path: Path):
        """Initialize security scanner."""
        self.project_path = project_path.resolve()

    def scan(self) -> SecurityScanResult:
        """Run all security scans."""
        result = SecurityScanResult(total_issues=0)
        result.scan_tools = []

        # Python-specific scans
        if self._is_python_project():
            # Bandit scan (Python security linter)
            bandit_issues = self._scan_with_bandit()
            result.issues.extend(bandit_issues)
            if bandit_issues:
                result.scan_tools.append("bandit")

            # Safety scan (dependency vulnerabilities)
            safety_issues = self._scan_with_safety()
            result.dependency_vulnerabilities.extend(safety_issues)
            if safety_issues:
                result.scan_tools.append("safety")

            # pip-audit (alternative dependency scanner)
            pip_audit_issues = self._scan_with_pip_audit()
            result.dependency_vulnerabilities.extend(pip_audit_issues)
            if pip_audit_issues:
                result.scan_tools.append("pip-audit")

        # Node.js scans
        if self._is_nodejs_project():
            npm_audit_issues = self._scan_with_npm_audit()
            result.dependency_vulnerabilities.extend(npm_audit_issues)
            if npm_audit_issues:
                result.scan_tools.append("npm-audit")

        # Generic security checks
        generic_issues = self._scan_generic_security()
        result.issues.extend(generic_issues)

        # Calculate totals
        result.total_issues = len(result.issues) + len(result.dependency_vulnerabilities)
        for issue in result.issues:
            severity = issue.severity.lower()
            result.issues_by_severity[severity] = result.issues_by_severity.get(severity, 0) + 1

        for vuln in result.dependency_vulnerabilities:
            severity = vuln.get("severity", "unknown").lower()
            result.issues_by_severity[severity] = result.issues_by_severity.get(severity, 0) + 1

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
        return (
            (self.project_path / "package.json").exists()
            or (self.project_path / "package-lock.json").exists()
            or (self.project_path / "yarn.lock").exists()
        )

    def _scan_with_bandit(self) -> List[SecurityIssue]:
        """Scan Python code with Bandit."""
        issues: List[SecurityIssue] = []
        try:
            # Check if bandit is available
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return issues
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return issues

        try:
            # Run bandit scan
            result = subprocess.run(
                [
                    "bandit",
                    "-r",
                    str(self.project_path),
                    "-f",
                    "json",
                    "-ll",  # Low confidence, low severity (show all)
                ],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path,
            )

            if result.returncode in (0, 1):  # 1 means issues found
                try:
                    data = json.loads(result.stdout)
                    for item in data.get("results", []):
                        issue = SecurityIssue(
                            severity=item.get("issue_severity", "medium").lower(),
                            rule_id=item.get("test_id", "unknown"),
                            description=item.get("issue_text", "Security issue"),
                            file_path=item.get("filename", ""),
                            line_number=item.get("line_number"),
                            code_snippet=item.get("code"),
                            cwe_id=item.get("issue_cwe", {}).get("id") if item.get("issue_cwe") else None,
                            confidence=item.get("issue_confidence", "medium").lower(),
                        )
                        issues.append(issue)
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, Exception) as e:
            console.print(f"[yellow]Warning: Bandit scan failed: {e}[/yellow]")

        return issues

    def _scan_with_safety(self) -> List[Dict[str, Any]]:
        """Scan Python dependencies with Safety."""
        vulnerabilities: List[Dict[str, Any]] = []
        try:
            # Check if safety is available
            result = subprocess.run(
                ["safety", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return vulnerabilities
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return vulnerabilities

        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path,
            )

            if result.returncode == 255:  # Safety returns 255 when vulnerabilities found
                try:
                    data = json.loads(result.stdout)
                    for item in data:
                        vuln = {
                            "package": item.get("package", "unknown"),
                            "installed_version": item.get("installed_version", ""),
                            "vulnerable_spec": item.get("vulnerable_spec", ""),
                            "advisory": item.get("advisory", ""),
                            "severity": item.get("severity", "medium").lower(),
                        }
                        vulnerabilities.append(vuln)
                except (json.JSONDecodeError, TypeError):
                    # Safety might output non-JSON, try parsing text
                    pass
        except (subprocess.TimeoutExpired, Exception) as e:
            console.print(f"[yellow]Warning: Safety scan failed: {e}[/yellow]")

        return vulnerabilities

    def _scan_with_pip_audit(self) -> List[Dict[str, Any]]:
        """Scan Python dependencies with pip-audit."""
        vulnerabilities: List[Dict[str, Any]] = []
        try:
            # Check if pip-audit is available
            result = subprocess.run(
                ["pip-audit", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return vulnerabilities
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return vulnerabilities

        try:
            # Run pip-audit
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path,
            )

            if result.returncode in (0, 1):
                try:
                    data = json.loads(result.stdout)
                    for vuln_data in data.get("vulnerabilities", []):
                        vuln = {
                            "package": vuln_data.get("name", "unknown"),
                            "installed_version": vuln_data.get("installed_version", ""),
                            "vulnerable_spec": vuln_data.get("vulnerable_spec", ""),
                            "advisory": vuln_data.get("advisory", ""),
                            "severity": vuln_data.get("severity", "medium").lower(),
                            "cve": vuln_data.get("id", ""),
                        }
                        vulnerabilities.append(vuln)
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
        except (subprocess.TimeoutExpired, Exception) as e:
            console.print(f"[yellow]Warning: pip-audit scan failed: {e}[/yellow]")

        return vulnerabilities

    def _scan_with_npm_audit(self) -> List[Dict[str, Any]]:
        """Scan Node.js dependencies with npm audit."""
        vulnerabilities: List[Dict[str, Any]] = []
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return vulnerabilities

        try:
            # Run npm audit
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.project_path,
            )

            if result.returncode in (0, 1):
                try:
                    data = json.loads(result.stdout)
                    for severity_level in ["critical", "high", "moderate", "low", "info"]:
                        for vuln_id, vuln_data in data.get("vulnerabilities", {}).items():
                            if vuln_data.get("severity") == severity_level:
                                vuln = {
                                    "package": vuln_data.get("name", vuln_id),
                                    "severity": severity_level,
                                    "title": vuln_data.get("title", ""),
                                    "cwe": vuln_data.get("cwe", []),
                                    "cve": vuln_id if vuln_id.startswith("CVE-") else None,
                                    "dependency": vuln_data.get("via", [vuln_id])[0] if vuln_data.get("via") else vuln_id,
                                }
                                vulnerabilities.append(vuln)
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
            console.print(f"[yellow]Warning: npm audit failed: {e}[/yellow]")

        return vulnerabilities

    def _scan_generic_security(self) -> List[SecurityIssue]:
        """Perform generic security checks."""
        issues: List[SecurityIssue] = []

        # Check for common security issues
        security_patterns = [
            # Hardcoded secrets
            (r"(?i)(password|secret|api[_-]?key|private[_-]?key)\s*=\s*['\"][^'\"]+['\"]", "hardcoded_secret"),
            # SQL injection patterns
            (r"(?i)(execute|query)\s*\(\s*['\"].*%.*['\"]", "sql_injection_risk"),
            # Command injection
            (r"(?i)(os\.system|subprocess\.call|exec|eval)\s*\([^)]*\+", "command_injection_risk"),
        ]

        for root, dirs, files in os.walk(self.project_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv", "venv"}]

            for file in files:
                if file.endswith((".py", ".js", ".ts", ".java", ".rb", ".php")):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_num, line in enumerate(f, 1):
                                for pattern, rule_id in security_patterns:
                                    if re.search(pattern, line):
                                        issues.append(
                                            SecurityIssue(
                                                severity="medium",
                                                rule_id=rule_id,
                                                description=f"Potential security issue: {rule_id}",
                                                file_path=str(file_path.relative_to(self.project_path)),
                                                line_number=line_num,
                                                code_snippet=line.strip()[:100],
                                            )
                                        )
                    except Exception:
                        pass

        return issues

