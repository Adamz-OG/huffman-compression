import random

import pytest

from huffman import compress, decompress
from huffman.codec import decode_payload, encode_payload
from huffman.codes import Code
from huffman.fileformat import FIXED_HEADER_SIZE
from huffman.stats import analyze
from huffman.tree import Node

SAMPLES = {
    "empty": b"",
    "one byte": b"a",
    "one distinct byte": b"z" * 1000,
    "two bytes": b"ab",
    "short text": b"abracadabra",
    "utf-8 text": "Élise a vu un ours brun à Compiègne, puis 🚀 !".encode(),
    "all byte values": bytes(range(256)),
    "random bytes": random.Random(1).randbytes(5000),
    "long text": b"un petit texte qui se repete encore et encore. " * 400,
}


@pytest.mark.parametrize("data", SAMPLES.values(), ids=SAMPLES.keys())
def test_round_trip(data: bytes) -> None:
    assert decompress(compress(data)) == data


def test_empty_input_is_header_only() -> None:
    assert len(compress(b"")) == FIXED_HEADER_SIZE


def test_redundant_text_gets_smaller() -> None:
    data = SAMPLES["long text"]
    assert len(compress(data)) < 0.7 * len(data)


def test_one_distinct_byte_uses_one_bit_per_byte() -> None:
    data = SAMPLES["one distinct byte"]
    header_size = FIXED_HEADER_SIZE + 2
    assert len(compress(data)) == header_size + len(data) // 8


def test_compression_is_deterministic() -> None:
    data = SAMPLES["utf-8 text"]
    assert compress(data) == compress(data)


@pytest.mark.parametrize("data", SAMPLES.values(), ids=SAMPLES.keys())
def test_size_matches_statistics(data: bytes) -> None:
    assert len(compress(data)) == analyze(data).compressed_size


def test_encode_payload_requires_a_code_for_every_byte() -> None:
    with pytest.raises(KeyError):
        encode_payload(b"ab", {97: Code(0, 1)})


def test_decode_payload_of_size_zero() -> None:
    assert decode_payload(b"\xff", Node(), 0) == b""
