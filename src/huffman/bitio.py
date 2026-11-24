"""Bit-level writing and reading.

Bits are packed most significant bit first: the first bit written is
bit 7 of the first byte. The last byte is padded with zeros.
"""

from __future__ import annotations

from collections.abc import Iterator

BITS_PER_BYTE = 8

# BYTE_BITS[b] holds the 8 bits of byte b, most significant first.
# Looking them up is faster than shifting each bit in the decoding loop.
BYTE_BITS: tuple[tuple[int, ...], ...] = tuple(
    tuple((byte >> shift) & 1 for shift in range(BITS_PER_BYTE - 1, -1, -1))
    for byte in range(256)
)


class BitWriter:
    """Accumulate bit sequences and pack them into bytes.

    Bits are kept in a small integer buffer and flushed to a ``bytearray``
    as soon as a full byte is available, so the memory used stays close
    to the size of the output.
    """

    def __init__(self) -> None:
        """Create an empty writer."""
        self._output = bytearray()
        self._buffer = 0
        self._pending = 0  # number of bits in the buffer, always < 8
        self._bit_length = 0

    @property
    def bit_length(self) -> int:
        """Total number of bits written so far (without padding)."""
        return self._bit_length

    def write(self, value: int, length: int) -> None:
        """Append the ``length`` low bits of ``value``.

        Raises:
            ValueError: if ``length`` is negative or ``value`` does not
                fit in ``length`` bits.

        """
        if length < 0:
            raise ValueError("length must be >= 0")
        if value < 0 or value >> length:
            raise ValueError(f"value {value} does not fit in {length} bits")
        self._buffer = (self._buffer << length) | value
        self._pending += length
        self._bit_length += length
        while self._pending >= BITS_PER_BYTE:
            self._pending -= BITS_PER_BYTE
            self._output.append((self._buffer >> self._pending) & 0xFF)
        self._buffer &= (1 << self._pending) - 1

    def to_bytes(self) -> bytes:
        """Return the packed bits, the last byte padded with zeros."""
        if self._pending == 0:
            return bytes(self._output)
        last = self._buffer << (BITS_PER_BYTE - self._pending)
        return bytes(self._output) + bytes([last])


def iter_bits(data: bytes) -> Iterator[int]:
    """Yield the bits of ``data`` one by one, most significant first."""
    for byte in data:
        yield from BYTE_BITS[byte]
