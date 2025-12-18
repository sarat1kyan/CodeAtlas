"""Dead code detector for finding unused code."""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

from rich.console import Console

console = Console()


@dataclass
class DeadCodeItem:
    """Represents a dead code item."""

    name: str
    type: str  # function, class, variable, import
    file_path: str
    line_number: int
    definition: str
    reason: str  # unused, unreachable, etc.


@dataclass
class DeadCodeResult:
    """Results from dead code detection."""

    total_items: int
    dead_functions: List[DeadCodeItem] = field(default_factory=list)
    dead_classes: List[DeadCodeItem] = field(default_factory=list)
    dead_imports: List[DeadCodeItem] = field(default_factory=list)
    unreachable_code: List[DeadCodeItem] = field(default_factory=list)


class DeadCodeDetector:
    """Detects dead code in codebases."""

    def __init__(self, project_path: Path):
        """Initialize dead code detector."""
        self.project_path = project_path.resolve()

    def detect(self) -> DeadCodeResult:
        """Detect dead code."""
        result = DeadCodeResult(total_items=0)

        # For Python files
        python_files = self._collect_python_files()
        
        for file_path in python_files:
            try:
                file_result = self._analyze_python_file(file_path)
                result.dead_functions.extend(file_result.dead_functions)
                result.dead_classes.extend(file_result.dead_classes)
                result.dead_imports.extend(file_result.dead_imports)
                result.unreachable_code.extend(file_result.unreachable_code)
            except Exception as e:
                console.print(f"[dim]Warning: Failed to analyze {file_path}: {e}[/dim]")

        result.total_items = (
            len(result.dead_functions) +
            len(result.dead_classes) +
            len(result.dead_imports) +
            len(result.unreachable_code)
        )

        return result

    def _collect_python_files(self) -> List[Path]:
        """Collect Python files."""
        python_files: List[Path] = []

        skip_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "venv", "target",
            "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache",
        }

        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    def _analyze_python_file(self, file_path: Path) -> DeadCodeResult:
        """Analyze a Python file for dead code."""
        result = DeadCodeResult(total_items=0)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
        except SyntaxError:
            return result
        except Exception:
            return result

        # Find all definitions
        definitions = {
            "functions": {},
            "classes": {},
            "imports": set(),
        }

        # Find all usages
        usages = {
            "functions": set(),
            "classes": set(),
            "imports": set(),
        }

        class DefinitionVisitor(ast.NodeVisitor):
            def __init__(self, definitions):
                self.definitions = definitions

            def visit_FunctionDef(self, node):
                self.definitions["functions"][node.name] = node.lineno
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                self.definitions["classes"][node.name] = node.lineno
                self.generic_visit(node)

            def visit_Import(self, node):
                for alias in node.names:
                    self.definitions["imports"].add(alias.name.split(".")[0])
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    self.definitions["imports"].add(node.module.split(".")[0])
                for alias in node.names:
                    self.definitions["imports"].add(alias.name)
                self.generic_visit(node)

        class UsageVisitor(ast.NodeVisitor):
            def __init__(self, usages):
                self.usages = usages

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    self.usages["functions"].add(node.id)
                    self.usages["classes"].add(node.id)
                    self.usages["imports"].add(node.id)
                self.generic_visit(node)

            def visit_Attribute(self, node):
                if isinstance(node.ctx, ast.Load):
                    if isinstance(node.value, ast.Name):
                        self.usages["classes"].add(node.value.id)
                self.generic_visit(node)

        # Collect definitions
        def_visitor = DefinitionVisitor(definitions)
        def_visitor.visit(tree)

        # Collect usages
        usage_visitor = UsageVisitor(usages)
        usage_visitor.visit(tree)

        # Find dead functions (not called, not main, not test)
        for func_name, line_num in definitions["functions"].items():
            if func_name not in usages["functions"]:
                # Check if it's a special function
                if func_name not in ["__init__", "__main__", "main", "setup", "teardown"] and not func_name.startswith("test_"):
                    result.dead_functions.append(
                        DeadCodeItem(
                            name=func_name,
                            type="function",
                            file_path=str(file_path.relative_to(self.project_path)),
                            line_number=line_num,
                            definition=f"def {func_name}(...)",
                            reason="Function is defined but never called",
                        )
                    )

        # Find dead classes (not used)
        for class_name, line_num in definitions["classes"].items():
            if class_name not in usages["classes"]:
                result.dead_classes.append(
                    DeadCodeItem(
                        name=class_name,
                        type="class",
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=line_num,
                        definition=f"class {class_name}",
                        reason="Class is defined but never used",
                    )
                )

        # Find unused imports
        for import_name in definitions["imports"]:
            if import_name not in usages["imports"]:
                result.dead_imports.append(
                    DeadCodeItem(
                        name=import_name,
                        type="import",
                        file_path=str(file_path.relative_to(self.project_path)),
                        line_number=1,  # Approximate
                        definition=f"import {import_name}",
                        reason="Import is not used",
                    )
                )

        return result

