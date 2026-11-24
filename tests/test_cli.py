import os
import subprocess
import sys
from pathlib import Path

import pytest

from huffman.cli import main

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    path = tmp_path / "notes.txt"
    path.write_text("Compression de Huffman, essai numero un.\n" * 50, encoding="utf-8")
    return path


def test_compress_then_decompress(text_file: Path, tmp_path: Path) -> None:
    packed = tmp_path / "packed.huf"
    restored = tmp_path / "restored.txt"
    assert main(["compress", str(text_file), "-o", str(packed)]) == 0
    assert main(["decompress", str(packed), "-o", str(restored)]) == 0
    assert restored.read_bytes() == text_file.read_bytes()
    assert packed.stat().st_size < text_file.stat().st_size


def test_default_output_names(text_file: Path) -> None:
    assert main(["compress", str(text_file)]) == 0
    packed = text_file.with_name("notes.txt.huf")
    assert packed.exists()
    text_file.unlink()
    assert main(["decompress", str(packed)]) == 0
    assert text_file.exists()


def test_decompress_without_huf_suffix(text_file: Path, tmp_path: Path) -> None:
    packed = tmp_path / "archive.bin"
    main(["compress", str(text_file), "-o", str(packed)])
    assert main(["decompress", str(packed)]) == 0
    assert (tmp_path / "archive.bin.out").read_bytes() == text_file.read_bytes()


def test_existing_output_needs_force(
    text_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "out.huf"
    target.write_bytes(b"keep me")
    assert main(["compress", str(text_file), "-o", str(target)]) == 1
    assert "already exists" in capsys.readouterr().err
    assert target.read_bytes() == b"keep me"
    assert main(["compress", str(text_file), "-o", str(target), "--force"]) == 0


def test_stats_output(text_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["stats", str(text_file), "--table", "3"]) == 0
    output = capsys.readouterr().out
    assert "entropy" in output
    assert "' '" in output  # the space is among the most frequent bytes


def test_stats_labels_non_printable_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    binary = tmp_path / "data.bin"
    binary.write_bytes(bytes([0, 0, 0, 200, 65]))
    assert main(["stats", str(binary), "--table", "3"]) == 0
    output = capsys.readouterr().out
    assert "0x00" in output and "0xc8" in output


def test_stats_on_empty_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.write_bytes(b"")
    assert main(["stats", str(empty), "--table", "5"]) == 0


def test_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["compress", str(tmp_path / "nope.txt")]) == 1
    assert "error" in capsys.readouterr().err


def test_invalid_stream(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bogus = tmp_path / "bogus.huf"
    bogus.write_bytes(b"definitely not compressed")
    assert main(["decompress", str(bogus)]) == 1
    assert "magic" in capsys.readouterr().err


def test_run_as_module(text_file: Path) -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    result = subprocess.run(
        [sys.executable, "-m", "huffman", "stats", str(text_file)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "ratio" in result.stdout
