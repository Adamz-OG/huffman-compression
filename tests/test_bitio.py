import random

import pytest

from huffman.bitio import BitWriter, iter_bits


def test_bits_are_packed_msb_first() -> None:
    writer = BitWriter()
    writer.write(0b101, 3)
    writer.write(0b11110, 5)
    assert writer.to_bytes() == bytes([0b10111110])
    assert writer.bit_length == 8


def test_last_byte_is_zero_padded() -> None:
    writer = BitWriter()
    writer.write(1, 1)
    assert writer.to_bytes() == b"\x80"
    assert writer.bit_length == 1


def test_empty_writer() -> None:
    assert BitWriter().to_bytes() == b""


def test_zero_length_write_is_a_no_op() -> None:
    writer = BitWriter()
    writer.write(0, 0)
    assert writer.bit_length == 0
    assert writer.to_bytes() == b""


def test_long_values_span_several_bytes() -> None:
    writer = BitWriter()
    writer.write(0xABCDE, 20)
    assert writer.to_bytes() == bytes([0xAB, 0xCD, 0xE0])


@pytest.mark.parametrize("value, length", [(4, 2), (-1, 3), (0, -1)])
def test_invalid_writes_are_rejected(value: int, length: int) -> None:
    with pytest.raises(ValueError):
        BitWriter().write(value, length)


def test_iter_bits_order() -> None:
    assert list(iter_bits(b"\xa5")) == [1, 0, 1, 0, 0, 1, 0, 1]


def test_iter_bits_empty() -> None:
    assert list(iter_bits(b"")) == []


def test_round_trip_random_values() -> None:
    rng = random.Random(0)
    chunks = []
    for _ in range(500):
        length = rng.randint(1, 30)
        chunks.append((rng.getrandbits(length), length))
    writer = BitWriter()
    for value, length in chunks:
        writer.write(value, length)
    expected = "".join(format(value, f"0{length}b") for value, length in chunks)
    read = "".join(map(str, iter_bits(writer.to_bytes())))
    assert read[: len(expected)] == expected
    assert set(read[len(expected) :]) <= {"0"}
    assert len(read) - len(expected) < 8
