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
from difflib import SequenceMatcher
from typing import List, Tuple

import jieba
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
        Split text into word tokens using jieba for Chinese and
        whitespace-based splitting for other scripts.
        Preserves whitespace as separate tokens.
        E.g. "今天天气很好" → ["今天", "天气", "很", "好"]
             "Hello world!" → ["Hello", " ", "world", "!"]
        """
        if not text:
            return []
        tokens = []
        for segment in self._word_pattern.findall(text):
            if segment.isspace():
                tokens.append(segment)
            else:
                # Use jieba for segments containing Chinese characters
                if re.search(r'[一-鿿]', segment):
                    cut = jieba.lcut(segment)
                    tokens.extend(cut)
                else:
                    tokens.append(segment)
        return tokens

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

        # Merge consecutive delete-insert pairs for natural reading
        result = self._merge_consecutive_changes(result)

        return result

    def _merge_consecutive_changes(
        self, diffs: List[Tuple[int, str]]
    ) -> List[Tuple[int, str]]:
        """
        Merge consecutive delete-insert pairs so that all contiguous
        old content is shown as one deleted block followed by all
        contiguous new content as one inserted block.

        Example:
          [(-1,"今"),(1,"明"),(-1,"天"),(1,"日"),(0,"天气")]
          → [(-1,"今天"),(1,"明日"),(0,"天气")]
        """
        if len(diffs) < 3:
            return diffs

        merged: List[Tuple[int, str]] = []
        i = 0
        while i < len(diffs):
            op, text = diffs[i]

            if op == 0:  # equal — pass through unchanged
                merged.append((op, text))
                i += 1
                continue

            # Collect consecutive alternating non-equal tokens
            del_parts: List[str] = []
            ins_parts: List[str] = []
            j = i

            while j < len(diffs) and diffs[j][0] != 0:
                cur_op, cur_text = diffs[j]
                if cur_op == -1:
                    del_parts.append(cur_text)
                elif cur_op == 1:
                    ins_parts.append(cur_text)
                j += 1

            if del_parts:
                merged.append((-1, "".join(del_parts)))
            if ins_parts:
                merged.append((1, "".join(ins_parts)))
            i = j

        return merged

    # ---- Block-level diff ----

    # Similarity threshold for treating a "replace" as a word-level diff
    # (rather than showing the whole block as deleted + inserted).
    _SIMILARITY_THRESHOLD = 0.4

    def _make_segments(self, raw_diffs: List[Tuple[int, str]]) -> List[DiffSegment]:
        """Convert (op, text) tuples into DiffSegment objects."""
        op_map = {0: "equal", -1: "delete", 1: "insert"}
        return [DiffSegment(operation=op_map[op], text=text) for op, text in raw_diffs]

    def diff_blocks(self, blocks1: List[Block],
                    blocks2: List[Block]) -> List[BlockDiff]:
        """
        Align blocks by content similarity (LCS via SequenceMatcher), then
        compute word-level diffs for each matched pair.

        This avoids the "wrong pairing" problem of naive index-based alignment
        when paragraphs are inserted or deleted in the middle of a document.
        """
        block_diffs: List[BlockDiff] = []

        # Treat block texts as sequence elements for alignment
        texts1 = [b.text for b in blocks1]
        texts2 = [b.text for b in blocks2]
        sm = SequenceMatcher(None, texts1, texts2)

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                # Blocks match — check for word-level changes
                for old_i, new_j in zip(range(i1, i2), range(j1, j2)):
                    b1, b2 = blocks1[old_i], blocks2[new_j]
                    raw = self.word_level_diff(b1.text, b2.text)
                    segments = self._make_segments(raw)
                    if any(s.operation != "equal" for s in segments):
                        block_diffs.append(BlockDiff(
                            block_index=old_i,
                            block_type=b1.type if b1.type == b2.type else f"{b1.type}→{b2.type}",
                            segments=segments,
                        ))

            elif tag == "replace":
                # Two dissimilar spans — align element by element when lengths
                # match; show remaining elements as delete / insert.
                common = min(i2 - i1, j2 - j1)
                for k in range(common):
                    b1, b2 = blocks1[i1 + k], blocks2[j1 + k]
                    if SequenceMatcher(None, b1.text, b2.text).ratio() >= self._SIMILARITY_THRESHOLD:
                        raw = self.word_level_diff(b1.text, b2.text)
                        segments = self._make_segments(raw)
                        block_diffs.append(BlockDiff(
                            block_index=i1 + k,
                            block_type=b1.type if b1.type == b2.type else f"{b1.type}→{b2.type}",
                            segments=segments,
                        ))
                    else:
                        block_diffs.append(BlockDiff(
                            block_index=i1 + k, block_type=b1.type,
                            segments=[DiffSegment(operation="delete", text=b1.text)],
                        ))
                        block_diffs.append(BlockDiff(
                            block_index=j1 + k, block_type=b2.type,
                            segments=[DiffSegment(operation="insert", text=b2.text)],
                        ))
                # Surplus in old version
                for k in range(common, i2 - i1):
                    b = blocks1[i1 + k]
                    block_diffs.append(BlockDiff(
                        block_index=i1 + k, block_type=b.type,
                        segments=[DiffSegment(operation="delete", text=b.text)],
                    ))
                # Surplus in new version
                for k in range(common, j2 - j1):
                    b = blocks2[j1 + k]
                    block_diffs.append(BlockDiff(
                        block_index=j1 + k, block_type=b.type,
                        segments=[DiffSegment(operation="insert", text=b.text)],
                    ))

            elif tag == "delete":
                for k in range(i1, i2):
                    b = blocks1[k]
                    block_diffs.append(BlockDiff(
                        block_index=k, block_type=b.type,
                        segments=[DiffSegment(operation="delete", text=b.text)],
                    ))

            elif tag == "insert":
                for k in range(j1, j2):
                    b = blocks2[k]
                    block_diffs.append(BlockDiff(
                        block_index=k, block_type=b.type,
                        segments=[DiffSegment(operation="insert", text=b.text)],
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
