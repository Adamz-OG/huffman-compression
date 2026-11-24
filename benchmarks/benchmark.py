"""Benchmark: compression ratio, entropy and speed on reproducible data.

Usage::

    python benchmarks/benchmark.py            # table in the terminal
    python benchmarks/benchmark.py --json out.json

Every corpus is generated from a fixed seed, so the results can be
reproduced. zlib (DEFLATE: LZ77 + Huffman) is shown for comparison only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import zlib
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huffman import compress, decompress  # noqa: E402
from huffman.stats import analyze  # noqa: E402

SIZE = 500_000
WORDS = (
    "le la les un une des et ou mais donc car de du au aux en dans sur sous "
    "pour par avec sans entre vers chez il elle nous vous ils elles on ce cette "
    "qui que quoi dont est sont était avait fait peut doit va vient dit voit "
    "temps jour année monde vie homme femme enfant ville pays maison école "
    "travail projet calcul arbre code fichier donnée mesure moteur avion aile "
    "vitesse pression énergie système réseau étude résultat méthode problème "
    "grand petit nouveau premier dernier long simple rapide léger fort même "
    "très plus moins bien aussi encore déjà toujours souvent ensuite enfin "
    "être avoir faire aller voir savoir pouvoir vouloir prendre donner trouver "
    "après avant pendant depuis comme quand où ainsi alors cependant"
).split()


def french_text(size: int, seed: int = 1) -> bytes:
    """Random French-like sentences built from a small vocabulary."""
    rng = random.Random(seed)
    parts: list[str] = []
    length = 0
    while length < size:
        words = rng.choices(WORDS, k=rng.randint(6, 16))
        sentence = " ".join(words).capitalize()
        sentence += rng.choice([". ", ". ", ", ", " ! ", " ? "])
        if rng.random() < 0.15:
            sentence += "\n"
        parts.append(sentence)
        length += len(sentence.encode())
    return "".join(parts).encode()[:size]


def python_source(size: int) -> bytes:
    """The source code of this project (real text, small file)."""
    files = sorted((ROOT / "src" / "huffman").glob("*.py"))
    return b"".join(path.read_bytes() for path in files)[:size]


def skewed_bytes(size: int, seed: int = 2) -> bytes:
    """Bytes whose probability decreases geometrically (p_i ~ 0.9 ** i)."""
    rng = random.Random(seed)
    weights = [0.9**i for i in range(256)]
    return bytes(rng.choices(range(256), weights=weights, k=size))


def random_bytes(size: int, seed: int = 3) -> bytes:
    """Uniform random bytes: no code can compress them."""
    return random.Random(seed).randbytes(size)


def single_byte(size: int) -> bytes:
    """One byte repeated: Huffman needs 1 bit per byte."""
    return b"A" * size


CORPORA: dict[str, Callable[[int], bytes]] = {
    "texte français": french_text,
    "code source Python": python_source,
    "octets biaisés": skewed_bytes,
    "octets aléatoires": random_bytes,
    "un seul octet": single_byte,
}


def timed(function: Callable[[bytes], bytes], data: bytes, repeat: int) -> float:
    """Best wall-clock time of ``repeat`` runs, in seconds."""
    best = float("inf")
    for _ in range(repeat):
        start = time.perf_counter()
        function(data)
        best = min(best, time.perf_counter() - start)
    return best


def run(size: int, repeat: int) -> list[dict[str, float | int | str]]:
    """Measure every corpus and return one record per corpus."""
    results: list[dict[str, float | int | str]] = []
    for name, make in CORPORA.items():
        data = make(size)
        blob = compress(data)
        assert decompress(blob) == data, f"round trip failed for {name}"
        stats = analyze(data)
        megabytes = len(data) / 1e6
        results.append(
            {
                "corpus": name,
                "size": len(data),
                "huffman_size": len(blob),
                "huffman_ratio": len(blob) / len(data),
                "zlib_ratio": len(zlib.compress(data, 9)) / len(data),
                "entropy": stats.entropy,
                "average_length": stats.average_length,
                "compress_mb_s": megabytes / timed(compress, data, repeat),
                "decompress_mb_s": megabytes / timed(decompress, blob, repeat),
            }
        )
    return results


def print_table(results: list[dict[str, float | int | str]]) -> None:
    """Print the results as a Markdown table."""
    print(
        "| Corpus | Taille | Huffman | zlib -9 | Entropie | Longueur moy. "
        "| Compression | Décompression |"
    )
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in results:
        cells = [
            str(r["corpus"]),
            _fr(f"{r['size']:,}") + " o",
            _fr(f"{r['huffman_ratio']:.1%}"),
            _fr(f"{r['zlib_ratio']:.1%}"),
            _fr(f"{r['entropy']:.3f}") + " bit",
            _fr(f"{r['average_length']:.3f}") + " bit",
            _fr(f"{r['compress_mb_s']:.2f}") + " Mo/s",
            _fr(f"{r['decompress_mb_s']:.2f}") + " Mo/s",
        ]
        print("| " + " | ".join(cells) + " |")


def _fr(number: str) -> str:
    """French number style: space for thousands, comma for decimals."""
    return number.replace(",", " ").replace(".", ",").replace("%", " %")


def main() -> None:
    """Parse arguments, run the benchmark and print or save the results."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--size", type=int, default=SIZE, help="bytes per corpus")
    parser.add_argument("--repeat", type=int, default=3, help="runs per timing")
    parser.add_argument("--json", type=Path, help="also save results as JSON")
    args = parser.parse_args()

    results = run(args.size, args.repeat)
    print_table(results)
    if args.json:
        args.json.write_text(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
