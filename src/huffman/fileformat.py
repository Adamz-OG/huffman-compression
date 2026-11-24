"""Binary layout of a compressed ``.huf`` file.

All integers are big-endian::

    offset  size  field
    0       4     magic number b"HUF1"
    4       8     original size in bytes (unsigned 64-bit)
    12      2     number n of distinct symbols (unsigned 16-bit, 0 to 256)
    14      2*n   n pairs (symbol, code length), one byte each,
                  sorted by symbol
    14+2*n  ...   payload: code words packed MSB first, zero padded

Storing the code lengths is enough to rebuild the canonical code, so the
tree itself is never written.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

from huffman.codes import check_lengths

MAGIC = b"HUF1"
_FIXED = struct.Struct(">4sQH")
FIXED_HEADER_SIZE = _FIXED.size  # 14 bytes
MAX_SYMBOLS = 256


class FormatError(ValueError):
    """Raised when a compressed stream is invalid or truncated."""


@dataclass(frozen=True, slots=True)
class Header:
    """Metadata stored in front of the compressed payload."""

    original_size: int
    lengths: dict[int, int] = field(default_factory=dict)

    @property
    def size(self) -> int:
        """Number of bytes taken by the header once packed."""
        return FIXED_HEADER_SIZE + 2 * len(self.lengths)


def pack_header(header: Header) -> bytes:
    """Serialize a header to bytes."""
    parts = [_FIXED.pack(MAGIC, header.original_size, len(header.lengths))]
    for symbol in sorted(header.lengths):
        parts.append(bytes([symbol, header.lengths[symbol]]))
    return b"".join(parts)


def unpack_header(blob: bytes) -> Header:
    """Read and validate the header at the start of ``blob``.

    Raises:
        FormatError: if the magic number, the sizes or the code lengths
            are invalid.

    """
    if len(blob) < FIXED_HEADER_SIZE:
        raise FormatError("stream too short to contain a header")
    magic, original_size, symbol_count = _FIXED.unpack_from(blob)
    if magic != MAGIC:
        raise FormatError("not a .huf stream (bad magic number)")
    if symbol_count > MAX_SYMBOLS:
        raise FormatError(f"too many symbols: {symbol_count}")
    if (original_size == 0) != (symbol_count == 0):
        raise FormatError("original size and symbol table do not match")

    table_end = FIXED_HEADER_SIZE + 2 * symbol_count
    if len(blob) < table_end:
        raise FormatError("truncated symbol table")
    lengths = _read_lengths(blob[FIXED_HEADER_SIZE:table_end])
    return Header(original_size=original_size, lengths=lengths)


def _read_lengths(table: bytes) -> dict[int, int]:
    """Decode the (symbol, length) pairs and check they form a valid code."""
    lengths: dict[int, int] = {}
    previous = -1
    for index in range(0, len(table), 2):
        symbol, length = table[index], table[index + 1]
        if symbol <= previous:
            raise FormatError("symbols must be unique and sorted")
        lengths[symbol] = length
        previous = symbol
    try:
        check_lengths(lengths)
    except ValueError as error:
        raise FormatError(f"invalid code lengths: {error}") from error
    return lengths
