import random

import pytest

from huffman.codes import Code, build_decoding_tree, canonical_codes, check_lengths
from huffman.tree import Node, huffman_code_lengths


def walk(root: Node, code: Code) -> Node:
    node: Node | None = root
    for bit in str(code):
        assert node is not None
        node = node.right if bit == "1" else node.left
    assert node is not None
    return node


def test_code_as_string_keeps_leading_zeros() -> None:
    assert str(Code(5, 4)) == "0101"
    assert str(Code(0, 3)) == "000"


def test_rfc1951_example() -> None:
    # Example of section 3.2.2 of RFC 1951 (DEFLATE).
    lengths = {
        ord(c): n for c, n in zip("ABCDEFGH", [3, 3, 3, 3, 3, 2, 4, 4], strict=True)
    }
    codes = {chr(s): str(c) for s, c in canonical_codes(lengths).items()}
    assert codes == {
        "A": "010",
        "B": "011",
        "C": "100",
        "D": "101",
        "E": "110",
        "F": "00",
        "G": "1110",
        "H": "1111",
    }


def test_single_symbol_code() -> None:
    assert canonical_codes({65: 1}) == {65: Code(0, 1)}


def test_empty_lengths_give_empty_code() -> None:
    assert canonical_codes({}) == {}


@pytest.mark.parametrize("seed", range(10))
def test_codes_are_prefix_free(seed: int) -> None:
    rng = random.Random(seed)
    frequencies = {s: rng.randint(1, 500) for s in rng.sample(range(256), 50)}
    codes = canonical_codes(huffman_code_lengths(frequencies))
    words = [str(code) for code in codes.values()]
    for i, first in enumerate(words):
        for second in words[i + 1 :]:
            assert not first.startswith(second)
            assert not second.startswith(first)


@pytest.mark.parametrize(
    "lengths",
    [{1: 1, 2: 1, 3: 1}, {1: 0}, {1: 256}, {1: 2, 2: 2, 3: 2, 4: 2, 5: 2}],
)
def test_invalid_lengths_are_rejected(lengths: dict[int, int]) -> None:
    with pytest.raises(ValueError):
        check_lengths(lengths)


def test_decoding_tree_leads_to_each_symbol() -> None:
    frequencies = {s: s + 1 for s in range(30)}
    codes = canonical_codes(huffman_code_lengths(frequencies))
    root = build_decoding_tree(codes)
    for symbol, code in codes.items():
        assert walk(root, code).symbol == symbol


@pytest.mark.parametrize(
    "codes",
    [
        {1: Code(0, 1), 2: Code(0, 2)},  # "0" is a prefix of "00"
        {1: Code(0, 2), 2: Code(0, 1)},  # same, other insertion order
        {1: Code(1, 1), 2: Code(1, 1)},  # same code twice
    ],
)
def test_decoding_tree_rejects_colliding_codes(codes: dict[int, Code]) -> None:
    with pytest.raises(ValueError):
        build_decoding_tree(codes)
