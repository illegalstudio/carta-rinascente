"""Original combining-mark pen paths.

Copyright (c) 2026, Carta Rinascente contributors.
SPDX-License-Identifier: OFL-1.1
"""

from ..geometry import dot

# These conventional forms use an independent comma-shaped mark. Compile the
# corresponding decomposed sequence to its precomposed glyph in ccmp as well.
CONTEXTUAL_ACCENTS = {
    ('d', '\u030c'): 'ď',
    ('l', '\u030c'): 'ľ',
    ('t', '\u030c'): 'ť',
    ('g', '\u0327'): 'ģ',
}

SIDE_COMMA = [dot(8, 97, 0.65), ('M 8 95 Q 12 26 -34 -12', 0.54)]
TURNED_COMMA = [dot(0, 45, 0.62), ('M -10 57 Q -17 106 34 139', 0.5)]

ACCENTS = {
    '\u0300': [('M -68 107 L 23 17', 0.84)],
    '\u0301': [('M -31 15 L 64 109', 0.84)],
    '\u0302': [('M -100 18 L 0 118 L 89 19', 0.74)],
    '\u0303': [('M -103 42 C -46 142 22 -3 100 91', 0.69)],
    '\u0304': [('M -93 59 L 96 62', 0.68)],
    '\u0306': [('M -91 100 Q -3 -24 88 100', 0.67)],
    '\u0307': [dot(0, 57, 0.79)],
    '\u0308': [dot(-64, 60, 0.7), dot(64, 60, 0.7)],
    '\u030a': [('M 5 121 C -80 121 -80 0 0 0 C 85 0 85 121 5 121 Z', 0.57)],
    '\u030b': [('M -87 14 L -12 112', 0.66), ('M 25 14 L 100 112', 0.66)],
    '\u030c': [('M -95 117 L 0 17 L 89 117', 0.74)],
    '\u0327': [('M 16 -13 L -7 -68 C 106 -88 44 -181 -38 -145', 0.62)],
    '\u0328': [('M 33 6 C -52 -88 -35 -169 62 -117', 0.65)],
}
