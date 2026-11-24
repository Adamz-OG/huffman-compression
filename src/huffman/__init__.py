"""Lossless compression with canonical Huffman codes.

Basic use::

    >>> from huffman import compress, decompress
    >>> blob = compress(b"abracadabra")
    >>> decompress(blob)
    b'abracadabra'
"""

from huffman.codec import compress, decompress
from huffman.fileformat import FormatError

__all__ = ["FormatError", "compress", "decompress"]
__version__ = "1.0.0"
