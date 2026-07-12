"""
Diff Engine
===========
Word-level diff computation for document version comparison.

Uses Google's diff-match-patch library with a word-tokenization
strategy: split text into words, encode as single Unicode characters,
perform character-level diff, then decode back to words.

This approach gives precise word-level diffs while leveraging the
library's well-tested character-level diffing and cleanup logic.
"""

import re
from typing import List, Tuple

from diff_match_patch import diff_match_patch

from models import DiffSegment, BlockDiff, DiffStats
from docx_parser import Block, DocumentContent


class DiffEngine:
    """
    Computes word-level diffs between two document versions.

    Strategy:
    1. Tokenize each text into individual words (preserving whitespace)
    2. Map each unique word to a Unicode character
    3. Run DMP's character-level diff on the encoded strings
    4. Decode the diff results back to word-level
    """

    def __init__(self):
        self.dmp = diff_match_patch()
        # Regex that matches either a whitespace run or a non-whitespace run
        self._word_pattern = re.compile(r'(\s+|\S+)')

    # ---- Tokenization ----

    def tokenize(self, text: str) -> List[str]:
        """
        Split text into word tokens, preserving whitespace.
        E.g. "Hello world!" → ["Hello", " ", "world", "!"]
        """
        if not text:
            return []
        return self._word_pattern.findall(text)

    def _encode_words(self, words: List[str],
                      word_map: dict, word_list: list) -> str:
        """
        Encode a list of word tokens into a single Unicode string.
        Each unique word maps to a single character via its index in word_list.
        The word_map dict provides the reverse mapping.
        """
        chars = []
        for word in words:
            if word not in word_map:
                word_map[word] = len(word_list)
                word_list.append(word)
            chars.append(chr(word_map[word]))
        return ''.join(chars)

    # ---- Core diff algorithm ----

    def word_level_diff(self, text1: str, text2: str) -> List[Tuple[int, str]]:
        """
        Compute a word-level diff between two texts.

        Args:
            text1: The "old" text (from an earlier version).
            text2: The "new" text (from a later version).

        Returns:
            List of (operation, word_text) tuples.
            operation: -1 = delete, 0 = equal, 1 = insert
        """
        words1 = self.tokenize(text1)
        words2 = self.tokenize(text2)

        # Handle empty cases
        if not words1 and not words2:
            return [(0, "")]
        if not words1:
            return [(1, "".join(words2))]  # all insert
        if not words2:
            return [(-1, "".join(words1))]  # all delete

        # Encode words as single Unicode characters for DMP
        word_map = {}
        word_list = [""]  # index 0 is an empty placeholder

        encoded1 = self._encode_words(words1, word_map, word_list)
        encoded2 = self._encode_words(words2, word_map, word_list)

        # Run character-level diff on encoded strings
        diffs = self.dmp.diff_main(encoded1, encoded2)
        self.dmp.diff_cleanupSemantic(diffs)

        # Decode back to word-level
        result = []
        for op, encoded_text in diffs:
            decoded_words = []
            for ch in encoded_text:
                idx = ord(ch)
                if 0 <= idx < len(word_list):
                    decoded_words.append(word_list[idx])
            if decoded_words:
                result.append((op, ''.join(decoded_words)))

        return result

    # ---- Block-level diff ----

    def diff_blocks(self, blocks1: List[Block],
                    blocks2: List[Block]) -> List[BlockDiff]:
        """
        Align blocks by index and compute word-level diffs for each pair.
        Handles insertions/deletions of entire blocks.

        Args:
            blocks1: Blocks from the old version.
            blocks2: Blocks from the new version.

        Returns:
            List of BlockDiff objects (only blocks with changes are included).
        """
        block_diffs = []
        max_len = max(len(blocks1), len(blocks2))

        for i in range(max_len):
            if i >= len(blocks1):
                # Entire block was inserted in version 2
                b2 = blocks2[i]
                segments = [DiffSegment(operation="insert", text=b2.text)]
                block_diffs.append(BlockDiff(
                    block_index=i,
                    block_type=b2.type,
                    segments=segments
                ))
            elif i >= len(blocks2):
                # Entire block was deleted from version 2
                b1 = blocks1[i]
                segments = [DiffSegment(operation="delete", text=b1.text)]
                block_diffs.append(BlockDiff(
                    block_index=i,
                    block_type=b1.type,
                    segments=segments
                ))
            else:
                # Both exist — compute word-level diff
                b1, b2 = blocks1[i], blocks2[i]
                raw_diffs = self.word_level_diff(b1.text, b2.text)
                segments = []
                for op, text in raw_diffs:
                    op_map = {0: "equal", -1: "delete", 1: "insert"}
                    segments.append(DiffSegment(
                        operation=op_map[op],
                        text=text
                    ))
                # Only include if there are actual changes
                has_changes = any(s.operation != "equal" for s in segments)
                if has_changes:
                    block_diffs.append(BlockDiff(
                        block_index=i,
                        block_type=b1.type if b1.type == b2.type else f"{b1.type}→{b2.type}",
                        segments=segments
                    ))

        return block_diffs

    # ---- Statistics ----

    @staticmethod
    def compute_stats(block_diffs: List[BlockDiff]) -> DiffStats:
        """Compute character-level insert/delete/equal counts from block diffs."""
        insertions = 0
        deletions = 0
        equal = 0
        for bd in block_diffs:
            for seg in bd.segments:
                length = len(seg.text)
                if seg.operation == "insert":
                    insertions += length
                elif seg.operation == "delete":
                    deletions += length
                else:
                    equal += length
        return DiffStats(insertions=insertions, deletions=deletions, equal=equal)

    # ---- Structured diff (block-aligned) ----

    def compute_structured_diff(self, content1: DocumentContent,
                                content2: DocumentContent) -> dict:
        """
        High-level diff between two DocumentContent objects.
        Returns a dictionary of diff results suitable for JSON serialization.
        """
        block_diffs = self.diff_blocks(content1.blocks, content2.blocks)
        stats = self.compute_stats(block_diffs)
        return {
            "blocks": [bd.model_dump() for bd in block_diffs],
            "stats": stats.model_dump()
        }

    # ---- Simple text diff (for fallback / preview) ----

    def simple_text_diff(self, text1: str, text2: str) -> dict:
        """
        Compute a diff treating the entire text as a single block.
        Useful as a fallback when block-level caching is unavailable.
        """
        raw_diffs = self.word_level_diff(text1, text2)
        segments = []
        for op, text in raw_diffs:
            op_map = {0: "equal", -1: "delete", 1: "insert"}
            segments.append(DiffSegment(operation=op_map[op], text=text))

        stats = DiffStats(
            insertions=sum(len(s.text) for s in segments if s.operation == "insert"),
            deletions=sum(len(s.text) for s in segments if s.operation == "delete"),
            equal=sum(len(s.text) for s in segments if s.operation == "equal")
        )

        return {
            "blocks": [BlockDiff(
                block_index=0,
                block_type="full_text",
                segments=segments
            ).model_dump()],
            "stats": stats.model_dump()
        }
