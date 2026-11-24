import random

import pytest

from huffman.tree import (
    Node,
    build_tree,
    code_lengths,
    count_frequencies,
    huffman_code_lengths,
    iter_leaves,
)


def reference_cost(weights: list[int]) -> int:
    """Optimal total cost, computed independently with a sorted list.

    The cost of a Huffman code (sum of weight * length) equals the sum of
    the weights of all merged nodes.
    """
    pool = sorted(weights)
    cost = 0
    while len(pool) > 1:
        merged = pool.pop(0) + pool.pop(0)
        cost += merged
        pool.append(merged)
        pool.sort()
    return cost


def internal_nodes(root: Node) -> list[Node]:
    stack, found = [root], []
    while stack:
        node = stack.pop()
        if not node.is_leaf:
            found.append(node)
            stack.extend(child for child in (node.left, node.right) if child)
    return found


def test_count_frequencies() -> None:
    assert count_frequencies(b"abracadabra") == {97: 5, 98: 2, 114: 2, 99: 1, 100: 1}


def test_count_frequencies_empty() -> None:
    assert count_frequencies(b"") == {}


def test_build_tree_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        build_tree({})


def test_build_tree_rejects_non_positive_weight() -> None:
    with pytest.raises(ValueError):
        build_tree({1: 3, 2: 0})


def test_root_weight_is_total_and_nodes_are_consistent() -> None:
    frequencies = count_frequencies(b"the quick brown fox jumps over the lazy dog")
    root = build_tree(frequencies)
    assert root.weight == sum(frequencies.values())
    for node in internal_nodes(root):
        assert node.symbol is None
        assert node.left is not None and node.right is not None
        assert node.weight == node.left.weight + node.right.weight


def test_every_symbol_is_a_leaf() -> None:
    frequencies = count_frequencies(b"mississippi river")
    leaves = {leaf.symbol for leaf, _ in iter_leaves(build_tree(frequencies))}
    assert leaves == set(frequencies)


def test_single_symbol_gets_one_bit() -> None:
    root = build_tree({65: 10})
    assert root.is_leaf
    assert code_lengths(root) == {65: 1}


def test_known_small_example() -> None:
    assert huffman_code_lengths({1: 5, 2: 2, 3: 1, 4: 1}) == {1: 1, 2: 2, 3: 3, 4: 3}


@pytest.mark.parametrize("seed", range(20))
def test_total_cost_is_optimal(seed: int) -> None:
    rng = random.Random(seed)
    frequencies = {s: rng.randint(1, 1000) for s in range(rng.randint(2, 60))}
    lengths = huffman_code_lengths(frequencies)
    cost = sum(weight * lengths[s] for s, weight in frequencies.items())
    assert cost == reference_cost(list(frequencies.values()))


def test_construction_is_deterministic() -> None:
    frequencies = {s: (s * 7) % 5 + 1 for s in range(40)}
    reversed_order = dict(reversed(list(frequencies.items())))
    assert huffman_code_lengths(frequencies) == huffman_code_lengths(reversed_order)


def test_deep_tree_does_not_recurse() -> None:
    fib = [1, 1]
    while len(fib) < 60:
        fib.append(fib[-1] + fib[-2])
    lengths = huffman_code_lengths(dict(enumerate(fib)))
    assert max(lengths.values()) == len(fib) - 1
