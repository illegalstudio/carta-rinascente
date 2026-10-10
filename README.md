<p align="center">
  <img src="assets/logo-mark.png" alt="Carta Rinascente quill and paper logo" width="130">
</p>

<h1 align="center">Carta Rinascente</h1>

<p align="center">
  <em>A new typeface with an old soul.</em>
</p>

<p align="center">
  <a href="dist/metadata.json"><img src="https://img.shields.io/badge/version-0.5.5-762F3B?style=flat-square&amp;color=762F3B" alt="Version: 0.5.5"></a>
  <a href="OFL.txt"><img src="https://img.shields.io/badge/license-OFL%201.1-762F3B?style=flat-square&amp;color=762F3B" alt="License: SIL OFL 1.1"></a>
  <a href="#get-the-font"><img src="https://img.shields.io/badge/formats-TTF%20%2B%20WOFF2-762F3B?style=flat-square&amp;color=762F3B" alt="Formats: TTF and WOFF2"></a>
</p>

<p align="center">
  <strong>340 characters per style &middot; Four styles &middot; TTF + WOFF2 &middot; Open source</strong>
</p>

<p align="center">
  An original typeface inspired by Renaissance penmanship, created for inclusion among the default fonts in Ariadne, the writing software by illegal studio. A composed upright design and an expressive italic bring the warmth of ink on paper to titles, quotations and short passages.
</p>

<p align="center">
  <a href="https://illegal.studio"><strong>illegal studio</strong></a>
  &middot;
  <a href="https://illegal.studio/en/products/ariadne"><strong>Discover Ariadne</strong></a>
</p>

---

<p align="center">
  <img src="assets/readme-specimen.png" alt="Carta Rinascente specimen showing English text, uppercase and lowercase letters, numerals and accented characters" width="800">
</p>

## Made for Ariadne

Carta Rinascente was created to join the default font selection in [Ariadne](https://illegal.studio/en/products/ariadne), the writing software by [illegal studio](https://illegal.studio). The goal is to give writers a distinctive typographic voice for titles, quotations and short passages, with a design that recalls the movement of a pen.

The font is also available on its own, ready to use in your documents, websites and applications.

## Get the font

The ready-to-use files are included in this repository. No build is required. Packaged editions are published on [GitHub Releases](https://github.com/illegalstudio/carta-rinascente/releases).

| Style | Desktop / native | Web |
| --- | --- | --- |
| Regular | [TTF](dist/CartaRinascente-Regular.ttf) | [WOFF2](dist/CartaRinascente-Regular.woff2) |
| Italic | [TTF](dist/CartaRinascente-Italic.ttf) | [WOFF2](dist/CartaRinascente-Italic.woff2) |
| Bold | [TTF](dist/CartaRinascente-Bold.ttf) | [WOFF2](dist/CartaRinascente-Bold.woff2) |
| Bold Italic | [TTF](dist/CartaRinascente-BoldItalic.ttf) | [WOFF2](dist/CartaRinascente-BoldItalic.woff2) |

Install all four TTF files with your operating system's font manager, then select **Carta Rinascente**. The fonts share a family name and carry the style flags used by applications for bold and italic selection. Include [`OFL.txt`](OFL.txt) when redistributing them; a copy is also supplied in `dist/`.

For native app bundles, register all four TTF files through the platform's font asset system. Their PostScript names follow `CartaRinascente-Regular`, `CartaRinascente-Italic`, `CartaRinascente-Bold` and `CartaRinascente-BoldItalic`.

To try the interactive preview, download or clone the repository and open `index.html` locally, keeping `dist/` beside it.

## Use on the web

Copy all four WOFF2 files and `OFL.txt` into your project, then adjust the URLs:

```css
@font-face {
  font-family: "Carta Rinascente";
  src: url("/fonts/CartaRinascente-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Carta Rinascente";
  src: url("/fonts/CartaRinascente-Italic.woff2") format("woff2");
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}

@font-face {
  font-family: "Carta Rinascente";
  src: url("/fonts/CartaRinascente-Bold.woff2") format("woff2");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Carta Rinascente";
  src: url("/fonts/CartaRinascente-BoldItalic.woff2") format("woff2");
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}

.writing {
  font-family: "Carta Rinascente", serif;
  font-synthesis: none;
  line-height: 1.4;
}
```

Use normal CSS `font-weight` and `font-style` to select a face. Regular and Bold are upright, with open proportions, bracketed serifs and steady strokes. Italic and Bold Italic use a 13-degree design slant, curved ascenders, sweeping descenders and tapered exit strokes. Their broader letterforms occupy approximately the same horizontal space as their upright companions. Optical spacing lets flourishes extend beyond the lowercase body without separating the words. Shared vertical metrics keep line spacing consistent when styles are mixed.

## Character and coverage

- **340 encoded characters and 341 glyphs per style**, including the missing-character glyph.
- **Complete printable Basic Latin and Latin-1 coverage**, Italian accents, many Latin Extended-A characters, combining marks, the euro symbol and typographic punctuation.
- **Proportional spacing and numerals**, with style-specific kerning, combining-mark positioning, contextual dot removal for accented i and j, and conventional comma forms in ď, ľ, ť and ģ.
- **Four linked styles**, version 0.5.5: Regular, Italic, Bold and Bold Italic, each supplied as TTF and WOFF2.

This experimental family is intended for headings and short passages. The reading proof shows all four styles at exactly 18, 24, 36 and 48 px, using “The art of a quiet page.” without automatic resizing. Inspect it at 100% zoom and check the result in your target application. Dedicated ligatures, stacked-mark positioning and manual TrueType hinting are not included. Greek, Cyrillic and emoji are outside the current character set.

Browse the [full character metadata](dist/metadata.json), [character sheet](dist/character-sheet-Regular.png), [reading and spacing tests](dist/reading-proof.png), [letterform details](dist/letterform-proof.png), [stroke balance](dist/stroke-balance-proof.png), [dots and punctuation](dist/punctuation-proof.png) or [four-style family specimen](dist/family-specimen.png).

## Inspiration and originality

Carta Rinascente was inspired by **Michelangelus**, the typeface introduced by Microsoft and inspired by Michelangelo's work and handwritten manuscripts. Commissioned by the Fabbrica di San Pietro and designed by Studiogusto, the project explores how Renaissance letterforms can inform contemporary typography. Read the official [Microsoft Design story, *Designing Michelangelus*](https://microsoft.design/articles/designing-michelangelus/), or visit the [Microsoft Michelangelus download page](https://www.microsoft.com/en-us/download/details.aspx?id=108856).

That idea prompted our own experiment with the rhythm of a pen on paper. Carta Rinascente's glyphs are built from independent pen paths and closed contours in [`src/design/`](src/design). No outlines, metrics or traced letterforms from Michelangelus or other proprietary fonts are copied into the design, and no external font files are required to build it. It is an independent project, unaffiliated with Microsoft, Studiogusto or the Fabbrica di San Pietro, and does not claim to reconstruct Michelangelo's handwriting.

## License and credits

The font, source and documentation are distributed under the **SIL Open Font License 1.1**, with no Reserved Font Names. See [`OFL.txt`](OFL.txt) for the complete terms.

The license permits use, modification and embedding in commercial applications. Keep the copyright notice and license with redistributed font files. Modified font versions remain under the OFL, and the font may not be sold by itself. Build dependencies retain their respective licenses.

Created by nahime at [illegal studio](https://illegal.studio), with assistance from OpenAI Codex. First edition: October 2026.
