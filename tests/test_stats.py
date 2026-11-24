import math
import random

import pytest

from huffman.stats import analyze, average_code_length, entropy
from huffman.tree import count_frequencies, huffman_code_lengths


def test_entropy_of_uniform_distribution() -> None:
    assert entropy({1: 10, 2: 10, 3: 10, 4: 10}) == pytest.approx(2.0)


def test_entropy_of_single_symbol_is_zero() -> None:
    assert entropy({7: 42}) == 0.0


def test_entropy_of_empty_input_is_zero() -> None:
    assert entropy({}) == 0.0


def test_average_code_length() -> None:
    assert average_code_length({1: 3, 2: 1}, {1: 1, 2: 3}) == pytest.approx(1.5)
    assert average_code_length({}, {}) == 0.0


@pytest.mark.parametrize("seed", range(10))
def test_huffman_is_within_one_bit_of_entropy(seed: int) -> None:
    rng = random.Random(seed)
    frequencies = {s: rng.randint(1, 10_000) for s in range(rng.randint(2, 200))}
    lengths = huffman_code_lengths(frequencies)
    h = entropy(frequencies)
    average = average_code_length(frequencies, lengths)
    assert h - 1e-9 <= average < h + 1


def test_dyadic_distribution_reaches_entropy() -> None:
    # Probabilities 1/2, 1/4, 1/8, 1/8: Huffman is exactly optimal.
    frequencies = {1: 4, 2: 2, 3: 1, 4: 1}
    lengths = huffman_code_lengths(frequencies)
    assert math.isclose(average_code_length(frequencies, lengths), entropy(frequencies))


def test_analyze_summary() -> None:
    data = b"aaaabbc"
    result = analyze(data)
    assert result.original_size == 7
    assert result.distinct_symbols == 3
    assert result.payload_bits == 4 * 1 + 2 * 2 + 1 * 2  # a=1 bit, b and c=2 bits
    assert result.ratio == result.compressed_size / 7
    assert count_frequencies(data) == {97: 4, 98: 2, 99: 1}


def test_analyze_empty_input() -> None:
    result = analyze(b"")
    assert result.compressed_size == result.header_size
    assert result.ratio == 1.0
