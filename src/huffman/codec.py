"""High-level compression and decompression of byte strings."""

from __future__ import annotations

from collections.abc import Mapping

from huffman.bitio import BYTE_BITS, BitWriter
from huffman.codes import Code, build_decoding_tree, canonical_codes
from huffman.fileformat import FormatError, Header, pack_header, unpack_header
from huffman.tree import Node, count_frequencies, huffman_code_lengths


def compress(data: bytes) -> bytes:
    """Compress ``data`` and return a self-contained ``.huf`` stream."""
    if not data:
        return pack_header(Header(original_size=0))
    lengths = huffman_code_lengths(count_frequencies(data))
    codes = canonical_codes(lengths)
    header = Header(original_size=len(data), lengths=lengths)
    return pack_header(header) + encode_payload(data, codes)


def decompress(blob: bytes) -> bytes:
    """Restore the original bytes from a ``.huf`` stream.

    Raises:
        FormatError: if the stream is invalid, corrupted or truncated.

    """
    header = unpack_header(blob)
    if header.original_size == 0:
        return b""
    root = build_decoding_tree(canonical_codes(header.lengths))
    return decode_payload(blob[header.size :], root, header.original_size)


def encode_payload(data: bytes, codes: Mapping[int, Code]) -> bytes:
    """Replace every byte of ``data`` by its code word and pack the bits.

    Raises:
        KeyError: if a byte of ``data`` has no code.

    """
    writer = BitWriter()
    for byte in data:
        code = codes[byte]
        writer.write(code.value, code.length)
    return writer.to_bytes()


def decode_payload(payload: bytes, root: Node, size: int) -> bytes:
    """Walk the decoding tree bit by bit until ``size`` bytes are restored.

    Knowing the original size tells the decoder where to stop, so the
    zero padding of the last byte is simply never read.

    Raises:
        FormatError: if a bit leads outside the tree or the payload ends
            before ``size`` bytes were decoded.

    """
    output = bytearray()
    if size == 0:
        return bytes(output)
    node = root
    for byte in payload:
        for bit in BYTE_BITS[byte]:
            child = node.right if bit else node.left
            if child is None:
                raise FormatError("invalid bit sequence in payload")
            if child.symbol is None:
                node = child
                continue
            output.append(child.symbol)
            if len(output) == size:
                return bytes(output)
            node = root
    raise FormatError(f"truncated payload: {len(output)} of {size} bytes decoded")
