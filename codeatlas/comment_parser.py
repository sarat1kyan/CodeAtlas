"""Comment parsing for various programming languages."""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from codeatlas.language_detector import LanguageDetector


@dataclass
class Comment:
    """Represents a comment in source code."""

    file_path: str
    line_number: int
    content: str
    language: str
    context_before: List[str]
    context_after: List[str]
    is_block: bool = False
    block_start: Optional[int] = None
    block_end: Optional[int] = None


class CommentParser:
    """Parses comments from source code files."""

    def __init__(self, language_detector: Optional[LanguageDetector] = None):
        """Initialize comment parser."""
        self.language_detector = language_detector or LanguageDetector()

        # Comment patterns by language
        self.comment_patterns: dict[str, dict[str, re.Pattern]] = {
            "Python": {
                "single": re.compile(r"^\s*#\s*(.*)$"),
                "block": re.compile(r'^\s*"""(.*?)"""\s*$', re.DOTALL | re.MULTILINE),
            },
            "JavaScript": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "TypeScript": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "Java": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "C": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "C++": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "C#": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "Go": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "Rust": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "Ruby": {
                "single": re.compile(r"^\s*#\s*(.*)$"),
                "block": re.compile(r"^\s*=begin\s*\n(.*?)\n=end\s*$", re.DOTALL | re.MULTILINE),
            },
            "PHP": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "Shell": {
                "single": re.compile(r"^\s*#\s*(.*)$"),
            },
            "SQL": {
                "single": re.compile(r"^\s*--\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "HTML": {
                "block": re.compile(r"<!--(.*?)-->", re.DOTALL | re.MULTILINE),
            },
            "CSS": {
                "single": re.compile(r"^\s*//\s*(.*)$"),
                "block": re.compile(r"^\s*/\*(.*?)\*/\s*$", re.DOTALL | re.MULTILINE),
            },
            "Lua": {
                "single": re.compile(r"^\s*--\s*(.*)$"),
                "block": re.compile(r"^\s*--\[\[(.*?)\]\]\s*$", re.DOTALL | re.MULTILINE),
            },
            "Perl": {
                "single": re.compile(r"^\s*#\s*(.*)$"),
            },
            "Haskell": {
                "single": re.compile(r"^\s*--\s*(.*)$"),
                "block": re.compile(r"^\s*\{-(.*?)-\}\s*$", re.DOTALL | re.MULTILINE),
            },
        }

    def parse_comments(
        self, file_path: str, content: str, language: Optional[str] = None, context_lines: int = 2
    ) -> List[Comment]:
        """
        Parse comments from file content.

        Args:
            file_path: Path to the file
            content: File content
            language: Detected language (auto-detected if None)
            context_lines: Number of context lines to include

        Returns:
            List of Comment objects
        """
        if not language:
            from pathlib import Path

            lang = self.language_detector.detect(Path(file_path), content)
            language = lang or "Unknown"

        lines = content.split("\n")
        comments: List[Comment] = []
        patterns = self.comment_patterns.get(language, {})

        # Track block comments
        in_block_comment = False
        block_start = None
        block_content: List[str] = []

        for i, line in enumerate(lines, 1):
            # Check for block comment start/end
            if "/*" in line and language in ["C", "C++", "Java", "JavaScript", "TypeScript", "C#", "Go", "Rust", "PHP", "SQL", "CSS"]:
                if not in_block_comment:
                    in_block_comment = True
                    block_start = i
                    block_content = []
                # Check if block ends on same line
                if "*/" in line:
                    comment_text = line[line.find("/*") + 2 : line.find("*/")]
                    comments.append(
                        Comment(
                            file_path=file_path,
                            line_number=i,
                            content=comment_text.strip(),
                            language=language,
                            context_before=lines[max(0, i - context_lines - 1) : i - 1],
                            context_after=lines[i : min(len(lines), i + context_lines)],
                            is_block=True,
                            block_start=block_start,
                            block_end=i,
                        )
                    )
                    in_block_comment = False
                    block_start = None
                    block_content = []
                else:
                    block_content.append(line[line.find("/*") + 2 :])
            elif in_block_comment:
                if "*/" in line:
                    block_content.append(line[: line.find("*/")])
                    comment_text = "\n".join(block_content).strip()
                    comments.append(
                        Comment(
                            file_path=file_path,
                            line_number=block_start or i,
                            content=comment_text,
                            language=language,
                            context_before=lines[max(0, (block_start or i) - context_lines - 1) : (block_start or i) - 1],
                            context_after=lines[i : min(len(lines), i + context_lines)],
                            is_block=True,
                            block_start=block_start,
                            block_end=i,
                        )
                    )
                    in_block_comment = False
                    block_start = None
                    block_content = []
                else:
                    block_content.append(line)
            else:
                # Check for single-line comments
                if "single" in patterns:
                    match = patterns["single"].match(line)
                    if match:
                        comment_text = match.group(1).strip()
                        comments.append(
                            Comment(
                                file_path=file_path,
                                line_number=i,
                                content=comment_text,
                                language=language,
                                context_before=lines[max(0, i - context_lines - 1) : i - 1],
                                context_after=lines[i : min(len(lines), i + context_lines)],
                            )
                        )

                # HTML comments
                if language == "HTML" and "<!--" in line:
                    start_idx = line.find("<!--")
                    end_idx = line.find("-->", start_idx)
                    if end_idx != -1:
                        comment_text = line[start_idx + 4 : end_idx].strip()
                        comments.append(
                            Comment(
                                file_path=file_path,
                                line_number=i,
                                content=comment_text,
                                language=language,
                                context_before=lines[max(0, i - context_lines - 1) : i - 1],
                                context_after=lines[i : min(len(lines), i + context_lines)],
                                is_block=True,
                            )
                        )

        return comments

    def is_commented_code(self, comment: Comment) -> bool:
        """
        Heuristically detect if a comment contains commented-out code.

        Args:
            comment: Comment object to analyze

        Returns:
            True if likely commented code
        """
        content = comment.content.strip()

        # Check for code-like patterns
        code_indicators = [
            r"\b(def|function|class|if|for|while|return|import|from|const|let|var)\b",
            r"[{}();=]",
            r"^\s*\w+\s*\(.*\)\s*\{?$",  # Function-like
            r"^\s*\w+\s*=\s*[^#]+$",  # Assignment
        ]

        code_score = 0
        for pattern in code_indicators:
            if re.search(pattern, content, re.MULTILINE):
                code_score += 1

        # If multiple indicators, likely code
        return code_score >= 2

