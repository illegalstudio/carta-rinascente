"""Build a character repertoire from original path modules, under SIL OFL 1.1."""

from ..config import Style
from ..geometry import GlyphBuilder, Shape
from . import italic, latin, roman, symbols


def build_glyphs(style: Style) -> dict[str, Shape]:
    # Import composition here because it uses the accent path module.
    from ..composition import extend_alphabet

    builder = GlyphBuilder(style)
    latin.draw(builder)
    (italic if style.italic else roman).draw(builder)
    symbols.draw(builder)
    extend_alphabet(builder)
    return builder.glyphs
