"""Canonical Huffman codes.

Only the code length of each symbol is needed to rebuild a canonical
code: symbols are sorted by (length, symbol) and receive consecutive
binary values. This is the method used by DEFLATE (RFC 1951) and it lets
the file header store lengths instead of the whole tree.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from huffman.tree import Node

MAX_CODE_LENGTH = 255  # fits in one byte of the file header


@dataclass(frozen=True, slots=True)
class Code:
    """A binary code word: ``length`` bits holding ``value``."""

    value: int
    length: int

    def __str__(self) -> str:
        """Return the code as a string of '0' and '1'."""
        return format(self.value, f"0{self.length}b")


def check_lengths(lengths: Mapping[int, int]) -> None:
    """Check that a prefix code with these lengths can exist.

    A prefix code exists if and only if the Kraft inequality holds:
    sum(2 ** -length) <= 1. The sum is computed with integers to stay
    exact.

    Raises:
        ValueError: if a length is out of range or the inequality fails.

    """
    if not lengths:
        return
    for symbol, length in lengths.items():
        if not 1 <= length <= MAX_CODE_LENGTH:
            raise ValueError(f"invalid code length {length} for symbol {symbol}")
    longest = max(lengths.values())
    kraft_sum = sum(1 << (longest - length) for length in lengths.values())
    if kraft_sum > 1 << longest:
        raise ValueError("code lengths violate the Kraft inequality")


def canonical_codes(lengths: Mapping[int, int]) -> dict[int, Code]:
    """Assign canonical code words from a ``{symbol: length}`` mapping."""
    check_lengths(lengths)
    codes: dict[int, Code] = {}
    value = 0
    previous_length = 0
    for symbol, length in sorted(lengths.items(), key=_by_length_then_symbol):
        value <<= length - previous_length
        codes[symbol] = Code(value, length)
        value += 1
        previous_length = length
    return codes


def _by_length_then_symbol(item: tuple[int, int]) -> tuple[int, int]:
    """Sort key for canonical ordering: shorter codes first."""
    symbol, length = item
    return length, symbol


def build_decoding_tree(codes: Mapping[int, Code]) -> Node:
    """Rebuild a binary tree where each leaf sits at the path of its code.

    Raises:
        ValueError: if two codes collide (one is a prefix of another).

    """
    root = Node()
    for symbol, code in codes.items():
        node = root
        for position in range(code.length - 1, -1, -1):
            if node.is_leaf:
                raise ValueError("a code is a prefix of another code")
            bit = (code.value >> position) & 1
            node = _child(node, bit)
        if node.is_leaf or node.left is not None or node.right is not None:
            raise ValueError("a code is a prefix of another code")
        node.symbol = symbol
    return root


def _child(node: Node, bit: int) -> Node:
    """Return the child of ``node`` for ``bit``, creating it if needed."""
    if bit == 0:
        if node.left is None:
            node.left = Node()
        return node.left
    if node.right is None:
        node.right = Node()
    return node.right
