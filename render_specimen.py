"""Render specimens using only the generated font and Pillow's built-in labels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = ROOT / 'dist/CartaRinascente-Regular.ttf'
OUT = ROOT / 'dist'
PAPER = '#f5f0e6'
INK = '#273731'
ACCENT = '#946045'
MUTED = '#766e62'


def font(size):
    return ImageFont.truetype(str(FONT), size=size)


def label(size=20):
    return ImageFont.load_default(size=size)


def specimen():
    im = Image.new('RGB', (1600, 1960), PAPER)
    d = ImageDraw.Draw(im)
    d.text((100, 75), 'STUDIO TIPOGRAFICO  /  PRIMA EDIZIONE  /  2026', font=label(20), fill=MUTED)
    d.line((100, 120, 1500, 120), fill='#cfc5b3', width=2)
    d.text((87, 165), 'Carta Rinascente', font=font(143), fill=INK, anchor='lt')
    d.text((100, 339), 'Un carattere nuovo, un gesto antico.', font=font(66), fill=ACCENT, anchor='lt')
    d.text((100, 466), 'IL DISEGNO', font=label(18), fill=MUTED)
    for y, text in [(510, 'La luce entra nella bottega. Sulla carta,'),
                    (588, 'una linea prende forma e diventa parola.'),
                    (666, 'Ogni idea ha bisogno del proprio segno.')]:
        d.text((100, y), text, font=font(65), fill=INK, anchor='lt')
    d.line((100, 789, 1500, 789), fill='#cfc5b3', width=2)
    d.text((100, 831), 'ALFABETO E NUMERI', font=label(18), fill=MUTED)
    for y, text in [(885, 'A B C D E F G H I J K L M'),
                    (990, 'N O P Q R S T U V W X Y Z'),
                    (1095, 'a b c d e f g h i j k l m'),
                    (1200, 'n o p q r s t u v w x y z'),
                    (1305, '0 1 2 3 4 5 6 7 8 9')]:
        d.text((100, y), text, font=font(73), fill=INK, anchor='lt')
    d.line((100, 1430, 1500, 1430), fill='#cfc5b3', width=2)
    d.text((100, 1472), 'ACCENTI, SEGNI, PAROLE', font=label(18), fill=MUTED)
    d.text((100, 1525), 'à è é ì ò ù  À È É Ì Ò Ù  € & @', font=font(68), fill=ACCENT, anchor='lt')
    d.text((100, 1635), 'Perché l’idea è già qui. «Sì, verrà!»', font=font(58), fill=INK, anchor='lt')
    d.text((100, 1750), 'Regular 0.1  /  TTF + WOFF2  /  SIL Open Font License 1.1', font=label(22), fill=MUTED)
    d.text((100, 1794), 'Disegno originale generato da tracciati indipendenti. Pensato per titoli e brevi testi.', font=label(20), fill=MUTED)
    d.text((100, 1874), 'CARTA RINASCENTE', font=label(17), fill=ACCENT)
    im.save(OUT / 'anteprima.png')


def character_sheet():
    from fontTools.ttLib import TTFont
    chars = [chr(cp) for cp in TTFont(FONT).getBestCmap()
             if cp > 32 and cp not in range(0x300, 0x370) and cp not in (0xAD, 0xA0, 0x2002, 0x2003, 0x2009, 0x200B, 0x202F)]
    cols, cell = 12, 140
    rows = (len(chars) + cols - 1) // cols
    im = Image.new('RGB', (cols*cell+80, rows*cell+140), PAPER)
    d = ImageDraw.Draw(im)
    d.text((40, 32), f'CARTA RINASCENTE  /  {len(chars)} CARATTERI VISIBILI', font=label(23), fill=INK)
    for index, c in enumerate(chars):
        x, y = 40+(index % cols)*cell, 100+(index // cols)*cell
        d.rectangle((x, y, x+cell, y+cell), outline='#ded4c4')
        d.text((x+cell/2, y+92), c, font=font(84), fill=INK, anchor='ms')
        d.text((x+12, y+118), f'U+{ord(c):04X}', font=label(13), fill=MUTED)
    im.save(OUT / 'caratteri.png')


def size_sheet():
    im = Image.new('RGB', (1600, 1300), 'white')
    d = ImageDraw.Draw(im)
    d.text((60, 42), 'CARTA RINASCENTE / PROVE DI LETTURA E SPAZIATURA', font=label(22), fill=INK)
    y = 125
    for size in (18, 22, 28, 36, 48, 64):
        d.text((60, y), f'{size} px', font=label(16), fill=MUTED)
        d.text((150, y), 'Arte, natura e ingegno. Perché la città è già più bella?', font=font(size), fill=INK, anchor='lt')
        y += max(80, size*1.65)
    for text in ('AVATAR WA VA To Ta Te Yo Wo fi fl ffi ffl',
                 'minimum illimitato fili foglie qui quattro',
                 'Il viaggio: € 125,90. 09/10/2026 (ore 14:30)',
                 'È À É Ì Ò Ù à è é ì ò ù ñ ç ö ü ÿ'):
        d.text((60, y), text, font=font(46), fill=INK, anchor='lt')
        y += 105
    im.save(OUT / 'prove-lettura.png')


if __name__ == '__main__':
    specimen()
    character_sheet()
    size_sheet()
    print('Rendered anteprima.png, caratteri.png, prove-lettura.png')
