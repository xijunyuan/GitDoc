"""
Tests for Diff Engine Module
=============================
Tests the word-level diff algorithm using diff-match-patch.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diff_engine import DiffEngine
from docx_parser import Block, DocumentContent
from models import DiffSegment, BlockDiff, DiffStats


class TestDiffEngine(unittest.TestCase):
    """Test suite for DiffEngine class."""

    def setUp(self):
        self.engine = DiffEngine()

    # --- Tokenize Tests ---

    def test_tokenize_simple(self):
        """Should split text into words and whitespace."""
        tokens = self.engine.tokenize("Hello world")
        self.assertEqual(tokens, ["Hello", " ", "world"])

    def test_tokenize_punctuation(self):
        """Punctuation stays attached to adjacent words in word-level tokenizing."""
        tokens = self.engine.tokenize("Hello, world!")
        # The regex splits into non-whitespace/whitespace runs:
        # "Hello," as one run, " " as whitespace, "world!" as one run
        self.assertIn("Hello,", tokens)
        self.assertIn(" ", tokens)
        self.assertIn("world!", tokens)

    def test_tokenize_empty(self):
        """Empty string should return empty list."""
        tokens = self.engine.tokenize("")
        self.assertEqual(tokens, [])

    def test_tokenize_chinese(self):
        """Chinese characters should be individual tokens."""
        tokens = self.engine.tokenize("你好世界")
        # Chinese chars have no whitespace, so each char is a non-whitespace run
        self.assertEqual(tokens, ["你好世界"])

    # --- Word-Level Diff Tests ---

    def test_diff_identical_texts(self):
        """Identical texts should produce a single 'equal' segment."""
        result = self.engine.word_level_diff("hello world", "hello world")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 0)  # equal

    def test_diff_single_word_change(self):
        """Single word change: one delete, one insert."""
        result = self.engine.word_level_diff(
            "The quick brown fox",
            "The quick red fox"
        )
        # Should have: equal("The quick "), delete("brown"), insert("red"), equal(" fox")
        operations = [r[0] for r in result]
        self.assertIn(-1, operations)  # delete
        self.assertIn(1, operations)   # insert

    def test_diff_complete_rewrite(self):
        """Complete rewrite: all delete for old, all insert for new."""
        result = self.engine.word_level_diff("old text", "completely new content")
        self.assertGreater(len(result), 0)

    def test_diff_empty_to_text(self):
        """Empty old text → all insert."""
        result = self.engine.word_level_diff("", "new content")
        self.assertTrue(all(r[0] == 1 for r in result))

    def test_diff_text_to_empty(self):
        """Old text → empty new: all delete."""
        result = self.engine.word_level_diff("old content", "")
        self.assertTrue(all(r[0] == -1 for r in result))

    def test_diff_both_empty(self):
        """Both empty → single equal empty."""
        result = self.engine.word_level_diff("", "")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 0)

    def test_diff_preserves_whitespace(self):
        """Whitespace should be preserved in diff output."""
        result = self.engine.word_level_diff("hello  world", "hello world")
        # Should show the double-space being deleted and single-space inserted
        operations = [r[0] for r in result]
        self.assertTrue(len(result) > 1)

    # --- Block-Level Diff Tests ---

    def test_diff_blocks_identical(self):
        """Identical blocks should produce empty result."""
        b1 = [Block("paragraph", "Same text", 0)]
        b2 = [Block("paragraph", "Same text", 0)]

        result = self.engine.diff_blocks(b1, b2)
        # No differences → empty list
        self.assertEqual(len(result), 0)

    def test_diff_blocks_changed(self):
        """Changed block should produce diff segments."""
        b1 = [Block("paragraph", "Old text here", 0)]
        b2 = [Block("paragraph", "New text here", 0)]

        result = self.engine.diff_blocks(b1, b2)
        self.assertEqual(len(result), 1)
        self.assertGreater(len(result[0].segments), 0)

    def test_diff_blocks_inserted(self):
        """New block in version 2 should be marked as insert."""
        b1 = [Block("paragraph", "Only block", 0)]
        b2 = [
            Block("paragraph", "Only block", 0),
            Block("paragraph", "New second block", 1)
        ]

        result = self.engine.diff_blocks(b1, b2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].block_index, 1)
        self.assertEqual(result[0].segments[0].operation, "insert")

    def test_diff_blocks_deleted(self):
        """Removed block in version 2 should be marked as delete."""
        b1 = [
            Block("paragraph", "First block", 0),
            Block("paragraph", "Second block", 1)
        ]
        b2 = [Block("paragraph", "First block", 0)]

        result = self.engine.diff_blocks(b1, b2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].block_index, 1)
        self.assertEqual(result[0].segments[0].operation, "delete")

    # --- Stats Tests ---

    def test_compute_stats(self):
        """Stats should correctly count insertions/deletions/equals."""
        segments = [
            DiffSegment(operation="equal", text="Hello"),
            DiffSegment(operation="delete", text=" world"),
            DiffSegment(operation="insert", text=" there")
        ]
        block_diff = BlockDiff(
            block_index=0,
            block_type="paragraph",
            segments=segments
        )
        stats = self.engine.compute_stats([block_diff])
        self.assertEqual(stats.equal, 5)       # "Hello"
        self.assertEqual(stats.deletions, 6)    # " world"
        self.assertEqual(stats.insertions, 6)   # " there"

    # --- Structured Diff Tests ---

    def test_compute_structured_diff(self):
        """Full structured diff should produce complete output."""
        content1 = DocumentContent([
            Block("paragraph", "Line one old", 0),
            Block("paragraph", "Line two", 1)
        ])
        content2 = DocumentContent([
            Block("paragraph", "Line one new", 0),
            Block("paragraph", "Line two", 1)
        ])

        result = self.engine.compute_structured_diff(content1, content2)
        self.assertIn("blocks", result)
        self.assertIn("stats", result)

    # --- Simple Text Diff Tests ---

    def test_simple_text_diff(self):
        """simple_text_diff should work with raw strings."""
        result = self.engine.simple_text_diff("abc", "adc")
        self.assertIn("blocks", result)
        self.assertIn("stats", result)
        self.assertEqual(len(result["blocks"]), 1)
        self.assertEqual(result["blocks"][0]["block_type"], "full_text")

    def test_large_text_diff_performance(self):
        """Diff of 1000+ words should complete within reasonable time."""
        text1 = "The quick brown fox jumps over the lazy dog. " * 100
        text2 = "The quick red fox jumps under the lazy cat. " * 100

        import time
        start = time.time()
        result = self.engine.simple_text_diff(text1, text2)
        elapsed = time.time() - start

        # Should complete in under 5 seconds
        self.assertLess(elapsed, 5.0)
        self.assertIn("blocks", result)


if __name__ == "__main__":
    unittest.main()
