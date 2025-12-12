"""Tests for comment parsing."""

import pytest

from codeatlas.comment_parser import CommentParser, LanguageDetector


class TestCommentParser:
    """Test comment parsing."""

    def test_parse_python_comments(self):
        """Test parsing Python comments."""
        parser = CommentParser()
        content = "# This is a comment\ndef hello():\n    pass"
        comments = parser.parse_comments("test.py", content, "Python")
        assert len(comments) == 1
        assert comments[0].content == "This is a comment"

    def test_parse_javascript_comments(self):
        """Test parsing JavaScript comments."""
        parser = CommentParser()
        content = "// This is a comment\nfunction hello() {\n    return;\n}"
        comments = parser.parse_comments("test.js", content, "JavaScript")
        assert len(comments) == 1
        assert comments[0].content == "This is a comment"

    def test_parse_block_comments(self):
        """Test parsing block comments."""
        parser = CommentParser()
        content = "/* This is a\n   block comment */\nfunction test() {}"
        comments = parser.parse_comments("test.js", content, "JavaScript")
        assert len(comments) >= 1

