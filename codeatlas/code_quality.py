"""Code quality analyzer for complexity, maintainability, and code metrics."""

import ast
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


@dataclass
class CodeQualityMetrics:
    """Code quality metrics for a file or codebase."""

    complexity: int = 0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    technical_debt: Optional[str] = None


@dataclass
class CodeQualityResult:
    """Results from code quality analysis."""

    total_files_analyzed: int
    average_complexity: float = 0.0
    average_maintainability: float = 0.0
    files_by_complexity: Dict[str, List[str]] = field(default_factory=dict)
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    per_file_metrics: Dict[str, CodeQualityMetrics] = field(default_factory=dict)


class CodeQualityAnalyzer:
    """Analyzes code quality, complexity, and maintainability."""

    def __init__(self, project_path: Path):
        """Initialize code quality analyzer."""
        self.project_path = project_path.resolve()

    def analyze(self, file_paths: Optional[List[Path]] = None) -> CodeQualityResult:
        """Analyze code quality for files in the project."""
        result = CodeQualityResult(total_files_analyzed=0)

        if file_paths is None:
            file_paths = self._collect_code_files()

        for file_path in file_paths:
            if file_path.suffix == ".py":
                metrics = self._analyze_python_file(file_path)
                if metrics:
                    result.per_file_metrics[str(file_path.relative_to(self.project_path))] = metrics
                    result.total_files_analyzed += 1

        # Calculate averages
        if result.per_file_metrics:
            complexities = [m.complexity for m in result.per_file_metrics.values() if m.complexity > 0]
            maintainabilities = [
                m.maintainability_index for m in result.per_file_metrics.values() if m.maintainability_index > 0
            ]

            if complexities:
                result.average_complexity = sum(complexities) / len(complexities)
            if maintainabilities:
                result.average_maintainability = sum(maintainabilities) / len(maintainabilities)

            # Categorize files by complexity
            for file_path, metrics in result.per_file_metrics.items():
                if metrics.complexity <= 5:
                    category = "low"
                elif metrics.complexity <= 10:
                    category = "medium"
                elif metrics.complexity <= 20:
                    category = "high"
                else:
                    category = "very_high"

                if category not in result.files_by_complexity:
                    result.files_by_complexity[category] = []
                result.files_by_complexity[category].append(file_path)

        return result

    def _collect_code_files(self) -> List[Path]:
        """Collect all code files to analyze."""
        code_files: List[Path] = []
        extensions = {".py", ".js", ".ts", ".java", ".rb", ".go", ".rs", ".cpp", ".c", ".h"}

        for root, dirs, files in os.walk(self.project_path):
            # Skip common directories
            dirs[:] = [
                d
                for d in dirs
                if d not in {".git", "__pycache__", "node_modules", ".venv", "venv", "target", "build", "dist"}
            ]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in extensions:
                    code_files.append(file_path)

        return code_files

    def _analyze_python_file(self, file_path: Path) -> Optional[CodeQualityMetrics]:
        """Analyze a Python file for quality metrics."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return None

            # Calculate metrics
            metrics = CodeQualityMetrics()

            # Count lines
            metrics.lines_of_code = len([line for line in content.split("\n") if line.strip() and not line.strip().startswith("#")])

            # Calculate cyclomatic complexity
            metrics.cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)

            # Calculate cognitive complexity (simplified)
            metrics.cognitive_complexity = self._calculate_cognitive_complexity(tree)

            # Overall complexity
            metrics.complexity = max(metrics.cyclomatic_complexity, metrics.cognitive_complexity)

            # Calculate maintainability index (simplified formula)
            # MI = 171 - 5.2 * ln(avg_halstead_volume) - 0.23 * avg_cyclomatic_complexity - 16.2 * ln(avg_lines_of_code)
            # Simplified version:
            halstead_volume = self._estimate_halstead_volume(tree)
            if halstead_volume > 0:
                mi = 171 - 5.2 * self._safe_ln(halstead_volume) - 0.23 * metrics.cyclomatic_complexity - 16.2 * self._safe_ln(metrics.lines_of_code)
                metrics.maintainability_index = max(0, min(100, mi))
            else:
                metrics.maintainability_index = 100.0

            # Technical debt estimation
            if metrics.complexity > 20:
                metrics.technical_debt = "high"
            elif metrics.complexity > 10:
                metrics.technical_debt = "medium"
            else:
                metrics.technical_debt = "low"

            return metrics

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to analyze {file_path}: {e}[/yellow]")
            return None

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity from AST."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1

        return complexity

    def _calculate_cognitive_complexity(self, tree: ast.AST) -> int:
        """Calculate cognitive complexity (simplified)."""
        complexity = 0
        nesting = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + nesting
                nesting += 1
            elif isinstance(node, (ast.With, ast.AsyncWith, ast.Try)):
                nesting += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if nesting > 0:
                    nesting -= 1

        return complexity

    def _estimate_halstead_volume(self, tree: ast.AST) -> float:
        """Estimate Halstead volume (simplified)."""
        operators = set()
        operands = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.operator):
                operators.add(type(node).__name__)
            elif isinstance(node, ast.Name):
                operands.add(node.id)
            elif isinstance(node, (ast.Constant, ast.Num, ast.Str)):
                operands.add(str(node.value))

        n1 = len(operators)  # Distinct operators
        n2 = len(operands)  # Distinct operands
        N1 = sum(1 for node in ast.walk(tree) if isinstance(node, ast.operator))  # Total operators
        N2 = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Name, ast.Constant)))  # Total operands

        if n1 == 0 or n2 == 0:
            return 0.0

        # Halstead Volume = (N1 + N2) * log2(n1 + n2)
        return (N1 + N2) * math.log2(n1 + n2)

    @staticmethod
    def _safe_ln(value: float) -> float:
        """Safe natural logarithm."""
        if value <= 0:
            return 0.0
        return math.log(value)

