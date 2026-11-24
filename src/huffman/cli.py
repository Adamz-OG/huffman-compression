"""Command line interface: ``huffman compress|decompress|stats FILE``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from huffman.codec import compress, decompress
from huffman.codes import canonical_codes
from huffman.fileformat import FormatError
from huffman.stats import analyze
from huffman.tree import count_frequencies, huffman_code_lengths

SUFFIX = ".huf"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return the exit code."""
    args = _build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (OSError, FormatError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="huffman", description="Lossless file compression with Huffman coding."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    for name, handler, help_text in (
        ("compress", _run_compress, "compress a file into FILE.huf"),
        ("decompress", _run_decompress, "restore a .huf file"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("input", type=Path, help="file to read")
        command.add_argument("-o", "--output", type=Path, help="file to write")
        command.add_argument(
            "-f", "--force", action="store_true", help="overwrite the output file"
        )
        command.set_defaults(handler=handler)

    stats = commands.add_parser("stats", help="show entropy, code lengths and ratio")
    stats.add_argument("input", type=Path, help="file to analyze")
    stats.add_argument(
        "--table",
        type=int,
        default=0,
        metavar="N",
        help="also print the codes of the N most frequent bytes",
    )
    stats.set_defaults(handler=_run_stats)
    return parser


def _run_compress(args: argparse.Namespace) -> int:
    data = args.input.read_bytes()
    output = args.output or args.input.with_name(args.input.name + SUFFIX)
    blob = compress(data)
    _write(output, blob, args.force)
    ratio = len(blob) / len(data) if data else 1.0
    print(f"{args.input} -> {output}: {len(data)} -> {len(blob)} bytes ({ratio:.1%})")
    return 0


def _run_decompress(args: argparse.Namespace) -> int:
    blob = args.input.read_bytes()
    output = args.output or _default_decompressed_path(args.input)
    data = decompress(blob)
    _write(output, data, args.force)
    print(f"{args.input} -> {output}: {len(data)} bytes restored")
    return 0


def _run_stats(args: argparse.Namespace) -> int:
    data = args.input.read_bytes()
    result = analyze(data)
    print(f"file             : {args.input}")
    print(f"original size    : {result.original_size} bytes")
    print(f"distinct symbols : {result.distinct_symbols}")
    print(f"entropy          : {result.entropy:.3f} bits/symbol")
    print(f"average length   : {result.average_length:.3f} bits/symbol")
    print(
        f"compressed size  : {result.compressed_size} bytes "
        f"(header {result.header_size} bytes)"
    )
    print(f"ratio            : {result.ratio:.2%}")
    if args.table > 0 and data:
        _print_table(data, args.table)
    return 0


def _print_table(data: bytes, limit: int) -> None:
    frequencies = count_frequencies(data)
    codes = canonical_codes(huffman_code_lengths(frequencies))
    ranked = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))
    print()
    print(f"{'byte':>6}  {'count':>8}  code")
    for symbol, weight in ranked[:limit]:
        print(f"{_label(symbol):>6}  {weight:>8}  {codes[symbol]}")


def _label(symbol: int) -> str:
    """Printable label for a byte: the character itself or its hex value."""
    character = chr(symbol)
    if character == " ":
        return "' '"
    if character.isprintable() and symbol < 128:
        return character
    return f"0x{symbol:02x}"


def _default_decompressed_path(path: Path) -> Path:
    if path.suffix == SUFFIX:
        return path.with_suffix("")
    return path.with_name(path.name + ".out")


def _write(path: Path, content: bytes, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists (use --force to overwrite)")
    path.write_bytes(content)
