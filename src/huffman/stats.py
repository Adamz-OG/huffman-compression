"""Measurements: entropy, average code length and compression ratio."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from huffman.fileformat import Header
from huffman.tree import count_frequencies, huffman_code_lengths


def entropy(frequencies: Mapping[int, int]) -> float:
    """Shannon entropy in bits per symbol: the lower bound of any code."""
    total = sum(frequencies.values())
    if total == 0:
        return 0.0
    result = 0.0
    for weight in frequencies.values():
        probability = weight / total
        result -= probability * math.log2(probability)
    return result


def average_code_length(
    frequencies: Mapping[int, int], lengths: Mapping[int, int]
) -> float:
    """Average number of bits per symbol for a given code."""
    total = sum(frequencies.values())
    if total == 0:
        return 0.0
    weighted = sum(weight * lengths[symbol] for symbol, weight in frequencies.items())
    return weighted / total


@dataclass(frozen=True, slots=True)
class CompressionStats:
    """Summary of what compressing a given input would produce."""

    original_size: int
    distinct_symbols: int
    entropy: float
    average_length: float
    payload_bits: int
    header_size: int

    @property
    def compressed_size(self) -> int:
        """Size in bytes of the whole ``.huf`` stream."""
        return self.header_size + (self.payload_bits + 7) // 8

    @property
    def ratio(self) -> float:
        """Compressed size divided by original size (lower is better)."""
        if self.original_size == 0:
            return 1.0
        return self.compressed_size / self.original_size


def analyze(data: bytes) -> CompressionStats:
    """Compute the statistics of ``data`` without writing any output."""
    frequencies = count_frequencies(data)
    lengths = huffman_code_lengths(frequencies) if frequencies else {}
    payload_bits = sum(weight * lengths[s] for s, weight in frequencies.items())
    header = Header(original_size=len(data), lengths=lengths)
    return CompressionStats(
        original_size=len(data),
        distinct_symbols=len(frequencies),
        entropy=entropy(frequencies),
        average_length=average_code_length(frequencies, lengths),
        payload_bits=payload_bits,
        header_size=header.size,
    )
