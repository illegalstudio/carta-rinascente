"""Command-line entry points for building, proving and validating the family.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from .build import build_family
from .config import DEFAULT_OUTPUT, ROOT, STYLES
from .specimens import render_family
from .validation import validate_family


def check_reproducibility(output: Path) -> None:
    with TemporaryDirectory(prefix=".build-repro-", dir=output.resolve().parent) as temporary:
        repeated = Path(temporary)
        build_family(repeated)
        names = [f"{style.filename}.{extension}" for style in STYLES for extension in ("ttf", "woff2")]
        names += ["metadata.json", "validation.json", "OFL.txt"]
        for name in names:
            if (output / name).read_bytes() != (repeated / name).read_bytes():
                raise ValueError(f"Build is not byte reproducible: {name}")
    print("PASS: repeated build is byte-identical.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build the original Carta Rinascente font family.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("build", "specimen", "validate", "all"):
        action = commands.add_parser(command)
        action.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Font distribution directory")
        if command in ("build", "all"):
            action.add_argument("--check-reproducible", action="store_true", help="Compare a second clean build")
        if command in ("specimen", "all"):
            action.add_argument("--readme-output", type=Path, help="Optional path for the README family specimen")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    try:
        if args.command in ("build", "all"):
            build_family(output)
            if args.check_reproducible:
                check_reproducibility(output)
        if args.command in ("specimen", "all"):
            readme = args.readme_output
            if readme is None and output == DEFAULT_OUTPUT:
                readme = ROOT / "assets" / "readme-specimen.png"
            render_family(output, readme)
        if args.command == "validate":
            validate_family(output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"PASS: {args.command} completed for all four styles in {output}")
