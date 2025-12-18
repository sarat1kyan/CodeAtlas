"""Security scanner for vulnerability detection and security analysis."""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
        
        # Entropy-based secret detection
        entropy_issues = self._scan_entropy_secrets()
        result.issues.extend(entropy_issues)
        
        # File-based secret detection
        file_secrets = self._scan_file_secrets()
        result.issues.extend(file_secrets)
        
        # Entropy-based secret detection
        entropy_issues = self._scan_entropy_secrets()
        result.issues.extend(entropy_issues)
        
        # File-based secret detection
        file_secrets = self._scan_file_secrets()
        result.issues.extend(file_secrets)

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

    def _find_package_json_files(self) -> List[Path]:
        """Find all package.json files recursively, including subdirectories."""
        package_json_files: List[Path] = []
        
        skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "target", "build", "dist", ".pytest_cache"}
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            if "package.json" in files:
                package_json_files.append(Path(root) / "package.json")
        
        return package_json_files

    def _scan_with_npm_audit(self) -> List[Dict[str, Any]]:
        """Scan Node.js dependencies with npm audit (monorepo support)."""
        vulnerabilities: List[Dict[str, Any]] = []
        package_json_files = self._find_package_json_files()
        
        if not package_json_files:
            return vulnerabilities

        # Scan each directory with package.json
        for package_json in package_json_files:
            package_dir = package_json.parent
            
            # Skip root package.json if it has no dependencies (monorepo root)
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    if not deps and not dev_deps and package_json == self.project_path / "package.json":
                        continue
            except Exception:
                pass

            try:
                # Run npm audit in this directory
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=package_dir,
                )

                if result.returncode in (0, 1):
                    try:
                        data = json.loads(result.stdout)
                        for severity_level in ["critical", "high", "moderate", "low", "info"]:
                            for vuln_id, vuln_data in data.get("vulnerabilities", {}).items():
                                if vuln_data.get("severity") == severity_level:
                                    rel_path = package_dir.relative_to(self.project_path)
                                    vuln = {
                                        "package": vuln_data.get("name", vuln_id),
                                        "severity": severity_level,
                                        "title": vuln_data.get("title", ""),
                                        "cwe": vuln_data.get("cwe", []),
                                        "cve": vuln_id if vuln_id.startswith("CVE-") else None,
                                        "dependency": vuln_data.get("via", [vuln_id])[0] if vuln_data.get("via") else vuln_id,
                                        "location": str(rel_path) if rel_path != Path(".") else "root",
                                    }
                                    vulnerabilities.append(vuln)
                    except (json.JSONDecodeError, TypeError, KeyError):
                        pass
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
                rel_path = package_dir.relative_to(self.project_path)
                console.print(f"[yellow]Warning: npm audit failed in {rel_path}: {e}[/yellow]")

        return vulnerabilities

    def _detect_secret_type(self, line: str, pattern_match: re.Match) -> Tuple[str, str]:
        """Detect the type of secret and determine severity."""
        line_lower = line.lower()
        matched_text = pattern_match.group(0).lower()
        
        # High severity - actual credentials
        if any(keyword in matched_text for keyword in ["password", "pwd", "passwd", "pass"]):
            if len(pattern_match.group(0)) > 10:  # Likely not a placeholder
                return "high", "Hardcoded password detected"
        
        # AWS credentials
        if any(keyword in matched_text for keyword in ["aws_access_key", "aws_secret", "aws_key"]):
            return "critical", "AWS credentials detected"
        
        # API keys and tokens
        if any(keyword in matched_text for keyword in ["api_key", "apikey", "api-key", "token", "bearer"]):
            # Check if it looks like a real key (long alphanumeric)
            value_match = re.search(r"['\"]([^'\"]+)['\"]", line)
            if value_match and len(value_match.group(1)) > 20:
                return "high", "API key or token detected"
        
        # Private keys
        if any(keyword in matched_text for keyword in ["private_key", "privatekey", "rsa_key", "ssh_key"]):
            return "critical", "Private key detected"
        
        # Database credentials
        if any(keyword in matched_text for keyword in ["db_password", "database_password", "db_pass", "db_pwd"]):
            return "high", "Database password detected"
        
        # OAuth and social media keys
        if any(keyword in matched_text for keyword in ["oauth", "client_secret", "consumer_secret", "facebook", "twitter", "google"]):
            return "high", "OAuth or social media credentials detected"
        
        # JWT secrets
        if "jwt" in matched_text and "secret" in matched_text:
            return "high", "JWT secret detected"
        
        # Encryption keys
        if any(keyword in matched_text for keyword in ["encryption_key", "enc_key", "cipher_key"]):
            return "high", "Encryption key detected"
        
        # Generic secrets
        if "secret" in matched_text:
            value_match = re.search(r"['\"]([^'\"]+)['\"]", line)
            if value_match and len(value_match.group(1)) > 10:
                return "medium", "Hardcoded secret detected"
        
        return "medium", "Potential hardcoded credential"

    def _scan_generic_security(self) -> List[SecurityIssue]:
        """Perform comprehensive generic security checks."""
        issues: List[SecurityIssue] = []

        # Comprehensive security patterns with severity classification
        security_patterns = [
            # Passwords and credentials (high priority)
            (r"(?i)(password|pwd|passwd|pass)\s*[=:]\s*['\"]([^'\"]{4,})['\"]", "hardcoded_password"),
            (r"(?i)(password|pwd|passwd)\s*=\s*['\"][^'\"]+['\"]", "hardcoded_password"),
            
            # API Keys and Tokens
            (r"(?i)(api[_-]?key|apikey|api_key)\s*[=:]\s*['\"]([^'\"]{10,})['\"]", "api_key_exposed"),
            (r"(?i)(token|bearer|access_token|refresh_token)\s*[=:]\s*['\"]([^'\"]{10,})['\"]", "token_exposed"),
            
            # AWS Credentials
            (r"(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*['\"]([^'\"]+)['\"]", "aws_credentials"),
            (r"(?i)AKIA[0-9A-Z]{16}", "aws_access_key_id"),  # AWS access key pattern
            
            # Private Keys
            (r"(?i)(private[_-]?key|privatekey|rsa[_-]?key|ssh[_-]?key)\s*[=:]\s*['\"]", "private_key_exposed"),
            (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "private_key_file"),
            
            # Database Credentials
            (r"(?i)(db[_-]?password|database[_-]?password|db[_-]?pass|db[_-]?pwd|db[_-]?user)\s*[=:]\s*['\"]([^'\"]+)['\"]", "database_credentials"),
            (r"(?i)(mongodb|mysql|postgres|postgresql)://[^:]+:([^@]+)@", "database_connection_string"),
            
            # OAuth and Social Media
            (r"(?i)(oauth[_-]?token|client[_-]?secret|consumer[_-]?secret)\s*[=:]\s*['\"]([^'\"]+)['\"]", "oauth_credentials"),
            (r"(?i)(facebook[_-]?app[_-]?secret|twitter[_-]?consumer[_-]?secret|google[_-]?client[_-]?secret)\s*[=:]\s*['\"]([^'\"]+)['\"]", "social_media_credentials"),
            
            # JWT Secrets
            (r"(?i)(jwt[_-]?secret|jwt[_-]?key)\s*[=:]\s*['\"]([^'\"]+)['\"]", "jwt_secret"),
            
            # Encryption Keys
            (r"(?i)(encryption[_-]?key|enc[_-]?key|cipher[_-]?key|secret[_-]?key)\s*[=:]\s*['\"]([^'\"]{10,})['\"]", "encryption_key"),
            
            # Generic Secrets (more specific - avoid matching "keywords", "secretary", etc.)
            (r"(?i)(secret[_-]?key|secretkey)\s*[=:]\s*['\"]([^'\"]{8,})['\"]", "hardcoded_secret"),
            (r"(?i)^\s*secret\s*[=:]\s*['\"]([^'\"]{8,})['\"]", "hardcoded_secret"),  # Only at start of line
            
            # SQL Injection patterns
            (r"(?i)(execute|query|exec)\s*\(\s*['\"].*%[sd].*['\"]", "sql_injection_risk"),
            (r"(?i)(execute|query)\s*\(\s*['\"].*\+.*['\"]", "sql_injection_risk"),
            
            # Command Injection
            (r"(?i)(os\.system|subprocess\.(call|run|Popen)|exec|eval|shell_exec)\s*\([^)]*\+", "command_injection_risk"),
            (r"(?i)(exec|eval)\s*\([^)]*\$", "command_injection_risk"),
            
            # XSS vulnerabilities
            (r"(?i)(innerHTML|outerHTML)\s*=\s*[^;]+(\+|\$)", "xss_risk"),
            (r"(?i)document\.write\s*\([^)]*\+", "xss_risk"),
            
            # Insecure random
            (r"(?i)(Math\.random|random\.randint)\s*\([^)]*\)", "insecure_random"),
            
            # Weak cryptography
            (r"(?i)(md5|sha1)\s*\(", "weak_cryptography"),
            
            # Debug code left in production (more specific - must have assignment or value)
            (r"(?i)(console\.log|print|debugger|var_dump)\s*\([^)]*(password|secret|key)\s*[=:]\s*['\"]", "debug_code_with_secrets"),
            
            # Environment files with secrets
            (r"(?i)\.env.*['\"](password|secret|key|token)", "env_file_secret"),
        ]

        skip_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "venv", "target", 
            "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            "vendor", "bower_components", ".next", ".nuxt"
        }
        
        skip_extensions = (".pyc", ".pyo", ".class", ".jar", ".war", ".ear", ".so", ".dll", ".dylib")

        for root, dirs, files in os.walk(self.project_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            for file in files:
                # Skip binary files and common non-code files
                if file.endswith(skip_extensions):
                    continue
                
                # Check code files and config files
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".rb", ".php", ".go", ".rs", ".cpp", ".c", ".h", ".hpp", ".cs", ".swift", ".kt", ".scala", ".clj", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".env", ".config", ".conf", ".ini", ".yaml", ".yml", ".toml", ".json")):
                    file_path = Path(root) / file
                    
                    # Skip if file is too large (>1MB)
                    try:
                        if file_path.stat().st_size > 1024 * 1024:
                            continue
                    except Exception:
                        continue
                    
                    # Skip package.json and similar files for certain patterns (they have too many false positives)
                    is_json_config = file.lower() in ["package.json", "package-lock.json", "tsconfig.json", "jsconfig.json", "composer.json", "pom.xml"]
                    
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            lines = content.split("\n")
                            
                            for line_num, line in enumerate(lines, 1):
                                # Skip comments that are clearly documentation
                                stripped = line.strip()
                                if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("*"):
                                    # Check if it's a real secret in a comment
                                    if any(keyword in line.lower() for keyword in ["password", "secret", "key", "token"]) and len(line) > 20:
                                        # Might be a real secret, check it
                                        pass
                                    else:
                                        continue
                                
                                # Skip common JSON patterns that cause false positives
                                if is_json_config:
                                    # Skip lines that are clearly not secrets (like "keywords", "description", etc.)
                                    json_key_pattern = r'^\s*"(keywords|description|name|version|author|license|homepage|repository|main|scripts|dependencies|devDependencies|engines|bin|files|directories)"\s*:'
                                    if re.match(json_key_pattern, line, re.IGNORECASE):
                                        continue
                                    # Skip array/list items that are just strings
                                    if re.match(r'^\s*"[^"]+",?\s*$', line):
                                        continue
                                
                                for pattern, rule_id in security_patterns:
                                    match = re.search(pattern, line)
                                    if match:
                                        # Additional filtering for JSON files to reduce false positives
                                        if is_json_config:
                                            # Skip if it's just a JSON key like "keywords", "private", etc.
                                            if re.match(r'^\s*"[^"]*(key|secret|token|password)[^"]*"\s*:\s*\[', line, re.IGNORECASE):
                                                continue
                                            # Skip if it's a JSON key without a value that looks like a secret
                                            if rule_id == "debug_code_with_secrets":
                                                # Only match if it's actually debug code, not just a JSON key
                                                if not re.search(r'(console\.log|print|debugger|var_dump)', line, re.IGNORECASE):
                                                    continue
                                            # Skip generic "secret" pattern if it's just a JSON key name
                                            if rule_id == "hardcoded_secret" and re.match(r'^\s*"[^"]*secret[^"]*"\s*:\s*\[', line, re.IGNORECASE):
                                                continue
                                        # Determine severity and description
                                        if rule_id in ["hardcoded_password", "aws_credentials", "private_key_exposed", "private_key_file"]:
                                            severity = "critical"
                                            description = f"Critical: {rule_id.replace('_', ' ').title()}"
                                        elif rule_id in ["api_key_exposed", "token_exposed", "database_credentials", "oauth_credentials", "jwt_secret", "encryption_key"]:
                                            severity = "high"
                                            description = f"High: {rule_id.replace('_', ' ').title()}"
                                        elif rule_id in ["sql_injection_risk", "command_injection_risk", "xss_risk"]:
                                            severity = "high"
                                            description = f"High: {rule_id.replace('_', ' ').title()}"
                                        else:
                                            severity, desc = self._detect_secret_type(line, match)
                                            description = f"{severity.title()}: {desc}"
                                        
                                        # Extract code snippet (mask sensitive parts)
                                        code_snippet = line.strip()[:150]
                                        # Mask potential secrets in display
                                        if match.groups():
                                            for group in match.groups():
                                                if group and len(group) > 8:
                                                    code_snippet = code_snippet.replace(group, "***MASKED***")
                                        
                                        issues.append(
                                            SecurityIssue(
                                                severity=severity,
                                                rule_id=rule_id,
                                                description=description,
                                                file_path=str(file_path.relative_to(self.project_path)),
                                                line_number=line_num,
                                                code_snippet=code_snippet,
                                                confidence="high" if severity in ["critical", "high"] else "medium",
                                            )
                                        )
                                        break  # Only report first match per line
                    except (UnicodeDecodeError, PermissionError, Exception):
                        pass

        return issues

    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0
        
        import math
        text = text.strip()
        if not text:
            return 0.0
        
        # Count character frequencies
        char_counts = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Calculate entropy
        length = len(text)
        entropy = 0.0
        for count in char_counts.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy

    def _scan_entropy_secrets(self) -> List[SecurityIssue]:
        """Scan for high-entropy strings that might be secrets."""
        issues: List[SecurityIssue] = []
        
        # High entropy threshold (random-looking strings)
        entropy_threshold = 4.0
        
        skip_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "venv", "target",
            "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            "vendor", "bower_components", ".next", ".nuxt", "bin", "obj"
        }
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".rb", ".php", ".go", ".rs", ".env", ".config", ".conf")):
                    file_path = Path(root) / file
                    
                    try:
                        if file_path.stat().st_size > 1024 * 1024:  # Skip > 1MB
                            continue
                        
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line_num, line in enumerate(f, 1):
                                # Look for string literals
                                string_pattern = r"['\"]([^'\"]{20,})['\"]"
                                matches = re.finditer(string_pattern, line)
                                
                                for match in matches:
                                    value = match.group(1)
                                    entropy = self._calculate_entropy(value)
                                    
                                    # High entropy suggests it might be a secret
                                    if entropy >= entropy_threshold and len(value) >= 20:
                                        # Check if it's not a URL or other common high-entropy pattern
                                        if not re.match(r"^https?://", value) and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
                                            issues.append(
                                                SecurityIssue(
                                                    severity="medium",
                                                    rule_id="high_entropy_string",
                                                    description=f"High entropy string detected (entropy: {entropy:.2f}) - possible secret",
                                                    file_path=str(file_path.relative_to(self.project_path)),
                                                    line_number=line_num,
                                                    code_snippet=line.strip()[:100].replace(value, "***MASKED***"),
                                                    confidence="medium",
                                                )
                                            )
                    except Exception:
                        pass
        
        return issues

    def _scan_file_secrets(self) -> List[SecurityIssue]:
        """Scan for secret files and sensitive file patterns."""
        issues: List[SecurityIssue] = []
        
        # Patterns for secret files
        secret_file_patterns = [
            (r"\.env$", "Environment file with potential secrets"),
            (r"\.env\.(local|dev|prod|staging)", "Environment-specific config file"),
            (r"secrets?\.(json|yaml|yml|toml)", "Secrets configuration file"),
            (r"\.(pem|key|p12|pfx|jks)$", "Private key or certificate file"),
            (r"id_rsa|id_dsa|id_ecdsa|id_ed25519", "SSH private key file"),
            (r"\.(sqlite|db)$", "Database file in repository"),
            (r"credentials?\.(json|yaml|yml)", "Credentials file"),
        ]
        
        skip_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "venv", "target",
            "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        }
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
            
            for file in files:
                for pattern, description in secret_file_patterns:
                    if re.search(pattern, file, re.IGNORECASE):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(self.project_path)
                        
                        # Check if file is in .gitignore (should be)
                        is_gitignored = False
                        try:
                            from codeatlas.git_integration import GitIntegration
                            git = GitIntegration(self.project_path)
                            is_gitignored = git.is_gitignored(file_path)
                        except Exception:
                            pass
                        
                        severity = "high" if not is_gitignored else "medium"
                        reason = description
                        if not is_gitignored:
                            reason += " - NOT in .gitignore!"
                        
                        issues.append(
                            SecurityIssue(
                                severity=severity,
                                rule_id="secret_file_detected",
                                description=reason,
                                file_path=str(rel_path),
                                line_number=None,
                                code_snippet=None,
                                confidence="high",
                            )
                        )
                        break
        
        return issues

