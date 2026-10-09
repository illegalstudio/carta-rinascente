"""Render English proofs for the complete font family.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import sys

from src.cli import main

if __name__ == "__main__":
    main(["specimen", *sys.argv[1:]])
