"""Language detection based on file extension, shebang, and content analysis."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Language extensions mapping
LANGUAGE_EXTENSIONS: Dict[str, List[str]] = {
    "Python": [".py", ".pyw", ".pyi"],
    "JavaScript": [".js", ".mjs", ".cjs"],
    "TypeScript": [".ts", ".tsx"],
    "Java": [".java"],
    "C": [".c", ".h"],
    "C++": [".cpp", ".cc", ".cxx", ".hpp", ".hxx", ".h++"],
    "C#": [".cs"],
    "Go": [".go"],
    "Rust": [".rs"],
    "Ruby": [".rb"],
    "PHP": [".php", ".phtml", ".php3", ".php4", ".php5"],
    "Swift": [".swift"],
    "Kotlin": [".kt", ".kts"],
    "Scala": [".scala"],
    "R": [".r", ".R"],
    "MATLAB": [".m"],
    "Shell": [".sh", ".bash", ".zsh", ".fish"],
    "PowerShell": [".ps1", ".psm1", ".psd1"],
    "Perl": [".pl", ".pm"],
    "Lua": [".lua"],
    "SQL": [".sql"],
    "HTML": [".html", ".htm", ".xhtml"],
    "CSS": [".css", ".scss", ".sass", ".less"],
    "Markdown": [".md", ".markdown"],
    "YAML": [".yml", ".yaml"],
    "JSON": [".json"],
    "XML": [".xml"],
    "TOML": [".toml"],
    "INI": [".ini", ".cfg", ".conf"],
    "Dockerfile": ["Dockerfile", ".dockerfile"],
    "Makefile": ["Makefile", "makefile"],
    "CMake": ["CMakeLists.txt", ".cmake"],
    "Vue": [".vue"],
    "Svelte": [".svelte"],
    "Dart": [".dart"],
    "Elixir": [".ex", ".exs"],
    "Clojure": [".clj", ".cljs", ".cljc"],
    "Haskell": [".hs", ".lhs"],
    "OCaml": [".ml", ".mli"],
    "Erlang": [".erl", ".hrl"],
    "F#": [".fs", ".fsi", ".fsx"],
    "VB.NET": [".vb"],
    "Objective-C": [".m", ".mm", ".h"],
    "Assembly": [".asm", ".s", ".S"],
    "Fortran": [".f", ".f90", ".f95", ".f03"],
    "COBOL": [".cob", ".cbl"],
    "Pascal": [".pas", ".p"],
    "Delphi": [".dpr", ".dpk"],
    "VHDL": [".vhd", ".vhdl"],
    "Verilog": [".v", ".vh"],
    "Tcl": [".tcl", ".tk"],
    "Groovy": [".groovy", ".gvy"],
    "D": [".d"],
    "Nim": [".nim"],
    "Crystal": [".cr"],
    "Zig": [".zig"],
    "V": [".v"],
    "Julia": [".jl"],
    "Nix": [".nix"],
    "Terraform": [".tf", ".tfvars"],
    "HCL": [".hcl"],
    "GraphQL": [".graphql", ".gql"],
    "Protocol Buffers": [".proto"],
    "Thrift": [".thrift"],
    "Avro": [".avdl", ".avpr", ".avsc"],
    "GLSL": [".glsl", ".vert", ".frag", ".geom"],
    "HLSL": [".hlsl", ".fx", ".fxh"],
    "CUDA": [".cu", ".cuh"],
    "OpenCL": [".cl"],
    "WebAssembly": [".wat", ".wasm"],
    "Solidity": [".sol"],
    "Vyper": [".vy"],
    "Move": [".move"],
    "Cadence": [".cdc"],
    "Text": [".txt", ".text"],
    "Log": [".log"],
    "Diff": [".diff", ".patch"],
    "CSV": [".csv"],
    "TSV": [".tsv"],
}

# Shebang patterns
SHEBANG_PATTERNS: Dict[str, List[str]] = {
    "Python": [r"^#!.*python", r"^#!.*python3"],
    "Shell": [r"^#!.*sh", r"^#!.*bash", r"^#!.*zsh", r"^#!.*fish"],
    "Perl": [r"^#!.*perl"],
    "Ruby": [r"^#!.*ruby"],
    "Node.js": [r"^#!.*node"],
    "Lua": [r"^#!.*lua"],
}

# Content-based detection patterns
CONTENT_PATTERNS: Dict[str, List[re.Pattern]] = {
    "Python": [
        re.compile(r"^\s*(def|class|import|from)\s+", re.MULTILINE),
        re.compile(r"^\s*#.*python", re.IGNORECASE),
    ],
    "JavaScript": [
        re.compile(r"(function\s*\w*\s*\(|const\s+\w+\s*=|let\s+\w+\s*=)", re.MULTILINE),
        re.compile(r"^\s*//.*javascript", re.IGNORECASE),
    ],
    "HTML": [
        re.compile(r"<!DOCTYPE\s+html", re.IGNORECASE),
        re.compile(r"<html", re.IGNORECASE),
    ],
    "SQL": [
        re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+", re.IGNORECASE),
    ],
}


class LanguageDetector:
    """Detects programming languages from file paths and content."""

    def __init__(self):
        """Initialize the language detector."""
        self._extension_map: Dict[str, str] = {}
        self._build_extension_map()

    def _build_extension_map(self) -> None:
        """Build reverse mapping from extension to language."""
        for lang, exts in LANGUAGE_EXTENSIONS.items():
            for ext in exts:
                # Handle extensions without dot
                if not ext.startswith("."):
                    self._extension_map[ext.lower()] = lang
                else:
                    self._extension_map[ext.lower()] = lang

    def detect_from_path(self, file_path: Path) -> Optional[str]:
        """Detect language from file path (extension and name)."""
        name = file_path.name.lower()
        suffix = file_path.suffix.lower()

        # Check exact filename matches first (e.g., Dockerfile, Makefile)
        if name in self._extension_map:
            return self._extension_map[name]

        # Check extension
        if suffix in self._extension_map:
            return self._extension_map[suffix]

        # Check multiple extensions (e.g., .tar.gz)
        parts = file_path.name.split(".")
        if len(parts) > 2:
            combined = "." + ".".join(parts[-2:])
            if combined.lower() in self._extension_map:
                return self._extension_map[combined.lower()]

        return None

    def detect_from_shebang(self, content: str) -> Optional[str]:
        """Detect language from shebang line."""
        first_line = content.split("\n")[0] if content else ""
        for lang, patterns in SHEBANG_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, first_line, re.IGNORECASE):
                    return lang
        return None

    def detect_from_content(self, content: str, file_path: Optional[Path] = None) -> Optional[str]:
        """Detect language from file content patterns."""
        # Limit content analysis to first 8KB for performance
        sample = content[:8192] if len(content) > 8192 else content

        for lang, patterns in CONTENT_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(sample):
                    return lang

        return None

    def detect(
        self, file_path: Path, content: Optional[str] = None, analyze_content: bool = True
    ) -> Optional[str]:
        """
        Detect language using multiple strategies.

        Args:
            file_path: Path to the file
            content: Optional file content for analysis
            analyze_content: Whether to analyze content (slower but more accurate)

        Returns:
            Detected language name or None
        """
        # Strategy 1: Extension/name
        lang = self.detect_from_path(file_path)
        if lang:
            return lang

        # Strategy 2: Shebang (if content provided)
        if content:
            lang = self.detect_from_shebang(content)
            if lang:
                return lang

        # Strategy 3: Content patterns (if enabled and content provided)
        if analyze_content and content:
            lang = self.detect_from_content(content, file_path)
            if lang:
                return lang

        return None

    def detect_embedded_languages(self, content: str, primary_lang: str) -> List[Tuple[str, int, int]]:
        """
        Detect embedded languages in content (e.g., JS in HTML, SQL in Python).

        Returns:
            List of (language, start_line, end_line) tuples
        """
        embedded: List[Tuple[str, int, int]] = []

        # HTML with embedded JS/CSS
        if primary_lang == "HTML":
            # Detect <script> blocks
            script_pattern = re.compile(r"<script[^>]*>", re.IGNORECASE)
            script_end_pattern = re.compile(r"</script>", re.IGNORECASE)
            for match in script_pattern.finditer(content):
                end_match = script_end_pattern.search(content, match.end())
                if end_match:
                    start_line = content[: match.start()].count("\n") + 1
                    end_line = content[: end_match.end()].count("\n") + 1
                    embedded.append(("JavaScript", start_line, end_line))

            # Detect <style> blocks
            style_pattern = re.compile(r"<style[^>]*>", re.IGNORECASE)
            style_end_pattern = re.compile(r"</style>", re.IGNORECASE)
            for match in style_pattern.finditer(content):
                end_match = style_end_pattern.search(content, match.end())
                if end_match:
                    start_line = content[: match.start()].count("\n") + 1
                    end_line = content[: end_match.end()].count("\n") + 1
                    embedded.append(("CSS", start_line, end_line))

        # Python with SQL in triple-quoted strings
        if primary_lang == "Python":
            sql_pattern = re.compile(r'("""|\'\'\')(.*?)(\1)', re.DOTALL)
            for match in sql_pattern.finditer(content):
                sql_content = match.group(2)
                if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE)\s+", sql_content, re.IGNORECASE):
                    start_line = content[: match.start()].count("\n") + 1
                    end_line = content[: match.end()].count("\n") + 1
                    embedded.append(("SQL", start_line, end_line))

        # Markdown with fenced code blocks
        if primary_lang == "Markdown":
            code_block_pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL | re.MULTILINE)
            for match in code_block_pattern.finditer(content):
                lang_hint = match.group(1)
                if lang_hint:
                    start_line = content[: match.start()].count("\n") + 1
                    end_line = content[: match.end()].count("\n") + 1
                    embedded.append((lang_hint, start_line, end_line))

        return embedded

