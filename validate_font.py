"""Validate all released font styles and their metadata.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

import sys

from src.cli import main

if __name__ == "__main__":
    main(["validate", *sys.argv[1:]])
