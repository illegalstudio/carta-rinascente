# Carta Rinascente

Prima versione di un carattere originale di stile rinascimentale leggibile, creata su richiesta di nahime con assistenza di OpenAI Codex. Ultima verifica: 9 ottobre 2026, host `Arc`.

Il disegno nasce da percorsi a pennino scritti in `build_font.py`. Non usa file, contorni, metriche o tracciati ricavati da Michelangelus o da altri font. Non è una ricostruzione filologica della scrittura di Michelangelo.

## File pronti

- `dist/CartaRinascente-Regular.ttf`: installazione desktop e inclusione in app native.
- `dist/CartaRinascente-Regular.woff2`: versione web, circa 27 KB.
- `index.html`: anteprima locale con testo modificabile e controllo della dimensione. Conservare la cartella `dist` accanto al file HTML.
- `dist/anteprima.png`: tavola di presentazione.
- `dist/caratteri.png`: repertorio visibile dei caratteri.
- `dist/prove-lettura.png`: prove a diverse dimensioni e sequenze di spaziatura.
- `dist/metadata.json`: repertorio completo e metadati.
- `dist/validation.json`: esito delle verifiche tecniche e impronte SHA-256.
- `OFL.txt`: licenza da mantenere insieme al font.

## Caratteristiche

Un peso Regular, versione 0.100. L'inclinazione di circa 6 gradi fa parte del disegno: usare `font-style: normal`, senza applicare un corsivo sintetico.

340 caratteri codificati e 341 glifi, incluso quello di carattere mancante. Copertura completa dei caratteri stampabili Basic Latin e Latin-1, accenti italiani, numerosi caratteri Latin Extended-A, segni combinanti, euro e punteggiatura tipografica. L'elenco esatto è in `dist/metadata.json`; non comprende alfabeti greco o cirillico né emoji.

Spaziatura proporzionale, 907 coppie di kerning OpenType e posizionamento dei segni combinanti. Numeri proporzionali. Non contiene pesi Bold, varianti aggiuntive, legature dedicate o hinting manuale TrueType.

Pensato per titoli, citazioni e brevi testi. Per l'uso a schermo partire da 24 px e verificare sul dispositivo di destinazione. Per testo minuto o interfacce dense è preferibile affiancarlo a un carattere da lettura. È una prima versione sperimentale da valutare nel proprio prodotto.

## Licenza e distribuzione

Font, sorgenti e documentazione sono distribuiti sotto **SIL Open Font License 1.1**, senza Reserved Font Names. Il testo completo e autorevole è `OFL.txt`.

La licenza permette uso, modifica e inclusione del font in applicazioni anche commerciali. Quando distribuisci i file del font, conserva l'avviso di copyright e la licenza. Le versioni modificate del font rimangono sotto OFL. Il font non può essere venduto da solo.

Fonte del testo: <https://openfontlicense.org/documents/OFL.txt>.

## Uso web

Copia il WOFF2 e `OFL.txt` tra gli asset del progetto. Adatta l'URL alla tua struttura:

```css
@font-face {
  font-family: "Carta Rinascente";
  src: url("/fonts/CartaRinascente-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

.titolo {
  font-family: "Carta Rinascente", serif;
  font-weight: 400;
  font-style: normal;
  font-synthesis: none;
  line-height: 1.35;
}
```

Per un'app nativa, registra il TTF secondo il sistema di asset della piattaforma. Nome famiglia: `Carta Rinascente`. Nome PostScript: `CartaRinascente-Regular`.

## Rigenerazione

Verificata su Python 3.14.7. Le dipendenze sono fissate in `requirements.txt`.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python build_font.py
.venv/bin/python render_specimen.py
.venv/bin/python validate_font.py
```

`build_font.py` disegna i glifi, unisce i tratti del pennino, compone gli accenti e scrive le tabelle OpenType. Le dipendenze non sono incluse nel pacchetto e conservano le proprie licenze. Pillow usa il suo font integrato solo per le etichette delle tavole, mai per creare i glifi di Carta Rinascente.

## Verifiche e limiti

Controllati parsing completo delle tabelle, copertura dei caratteri, ingombri verticali, accenti italiani in forma composta e decomposta, kerning, rasterizzazione FreeType a 24 e 64 px e corrispondenza tra TTF e WOFF2 dopo decodifica. Le tavole PNG sono state ispezionate visivamente.

L'anteprima HTML è stata verificata staticamente. Il controllo nel browser automatizzato non è stato eseguito perché la policy del browser blocca gli URL `file:`. La verifica visiva si basa sui PNG resi con FreeType. Resta da provare l'integrazione nella specifica applicazione che userà il font.

Lo storico di sviluppo è nel progetto Code Journal `carta-rinascente`. La prima versione è stata creata il 9 ottobre 2026 su `Arc`; nello stesso giorno il progetto è stato trasferito nella repository dedicata `~/Developer/illegalstudio/carta-rinascente`.
