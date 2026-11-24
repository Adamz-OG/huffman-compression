"""Frequency counting, Huffman tree construction and code lengths.

The tree is built with a binary heap: at each step the two lightest
nodes are merged into a new parent node, until a single root remains.
"""

from __future__ import annotations

import heapq
from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from itertools import count


@dataclass(slots=True)
class Node:
    """A node of a Huffman tree.

    A leaf carries a ``symbol`` (a byte value from 0 to 255). An internal
    node has no symbol and two children. ``weight`` is the number of
    occurrences covered by the node (0 for a decoding tree, where the
    weights are not known).
    """

    weight: int = 0
    symbol: int | None = None
    left: Node | None = None
    right: Node | None = None

    @property
    def is_leaf(self) -> bool:
        """Return True if the node carries a symbol."""
        return self.symbol is not None


def count_frequencies(data: bytes) -> dict[int, int]:
    """Count how many times each byte value appears in ``data``."""
    return dict(Counter(data))


def build_tree(frequencies: Mapping[int, int]) -> Node:
    """Build a Huffman tree from a ``{symbol: weight}`` mapping.

    Ties between equal weights are broken by insertion order, which makes
    the construction deterministic: the same input always gives the same
    tree.

    Raises:
        ValueError: if the mapping is empty or contains a weight <= 0.

    """
    if not frequencies:
        raise ValueError("cannot build a Huffman tree without symbols")
    if any(weight <= 0 for weight in frequencies.values()):
        raise ValueError("every weight must be a positive integer")

    order = count()
    heap: list[tuple[int, int, Node]] = [
        (weight, next(order), Node(weight=weight, symbol=symbol))
        for symbol, weight in sorted(frequencies.items())
    ]
    heapq.heapify(heap)

    while len(heap) > 1:
        weight_a, _, node_a = heapq.heappop(heap)
        weight_b, _, node_b = heapq.heappop(heap)
        parent = Node(weight=weight_a + weight_b, left=node_a, right=node_b)
        heapq.heappush(heap, (parent.weight, next(order), parent))

    return heap[0][2]


def iter_leaves(root: Node) -> Iterator[tuple[Node, int]]:
    """Yield every leaf of the tree with its depth.

    The traversal uses an explicit stack, so deep trees cannot hit
    Python's recursion limit.
    """
    stack: list[tuple[Node, int]] = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node.is_leaf:
            yield node, depth
            continue
        if node.right is not None:
            stack.append((node.right, depth + 1))
        if node.left is not None:
            stack.append((node.left, depth + 1))


def code_lengths(root: Node) -> dict[int, int]:
    """Return the code length (leaf depth) of every symbol of the tree.

    A tree made of a single leaf has depth 0. That symbol still needs one
    bit per occurrence, so its length is set to 1.
    """
    lengths: dict[int, int] = {}
    for leaf, depth in iter_leaves(root):
        assert leaf.symbol is not None
        lengths[leaf.symbol] = max(depth, 1)
    return lengths


def huffman_code_lengths(frequencies: Mapping[int, int]) -> dict[int, int]:
    """Shortcut: frequencies to optimal code lengths."""
    return code_lengths(build_tree(frequencies))
