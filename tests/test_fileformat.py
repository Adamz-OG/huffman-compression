import struct

import pytest

from huffman import FormatError, compress, decompress
from huffman.fileformat import (
    FIXED_HEADER_SIZE,
    MAGIC,
    Header,
    pack_header,
    unpack_header,
)


def raw_header(size: int, pairs: list[tuple[int, int]], magic: bytes = MAGIC) -> bytes:
    table = b"".join(bytes(pair) for pair in pairs)
    return struct.pack(">4sQH", magic, size, len(pairs)) + table


def test_header_round_trip() -> None:
    header = Header(original_size=1234, lengths={10: 2, 3: 1, 200: 2})
    packed = pack_header(header)
    assert len(packed) == header.size == FIXED_HEADER_SIZE + 6
    assert unpack_header(packed) == header


def test_pairs_are_written_sorted_by_symbol() -> None:
    packed = pack_header(Header(original_size=3, lengths={9: 1, 2: 1}))
    assert packed[FIXED_HEADER_SIZE:] == bytes([2, 1, 9, 1])


def test_empty_header() -> None:
    assert unpack_header(pack_header(Header(original_size=0))) == Header(0)


@pytest.mark.parametrize(
    "blob",
    [
        b"",
        b"HUF1",
        raw_header(5, [(65, 1)], magic=b"ZIP!"),
        raw_header(5, []),
        raw_header(0, [(65, 1)]),
        raw_header(5, [(65, 1), (66, 1)])[:-1],
        raw_header(5, [(66, 1), (65, 1)]),
        raw_header(5, [(65, 1), (65, 1)]),
        raw_header(5, [(65, 1), (66, 1), (67, 1)]),
        raw_header(5, [(65, 0)]),
        struct.pack(">4sQH", MAGIC, 5, 300),
    ],
    ids=[
        "empty stream",
        "magic only",
        "bad magic",
        "size without symbols",
        "symbols without size",
        "truncated table",
        "unsorted symbols",
        "duplicate symbol",
        "kraft violated",
        "zero length",
        "too many symbols",
    ],
)
def test_invalid_headers_are_rejected(blob: bytes) -> None:
    with pytest.raises(FormatError):
        unpack_header(blob)


def test_truncated_payload_is_detected() -> None:
    blob = compress(b"a fairly long sentence to have several payload bytes")
    with pytest.raises(FormatError, match="truncated"):
        decompress(blob[:-3])


def test_bits_outside_the_code_are_detected() -> None:
    # Lengths 2, 2, 2 give the codes 00, 01, 10: the path 11 leads nowhere.
    blob = raw_header(4, [(65, 2), (66, 2), (67, 2)]) + b"\xff"
    with pytest.raises(FormatError, match="invalid bit sequence"):
        decompress(blob)


def test_format_error_is_a_value_error() -> None:
    assert issubclass(FormatError, ValueError)
