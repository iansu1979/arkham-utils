# Arkham Horror LCG utilities

A simple set of utilities to read from [ArkhamDB](https://arkhamdb.com/) and [OCTGN files](https://github.com/GeckoTH/arkham-horror) mainly used to generate printable proxies in PDF format.

```sh
pip install arkham-utils
```

## Using ArkhamDB images

Note the images from ArkhamDB have an FFG watermark on them.

```py
from arkham_utils.arkhamdb import db
from arkham_utils.pdf.builder import PDFBuilder

cards = [db.search(name) for name in [
  'Blackjack',
  'Guts',
  'Emergency Cache',
  'Elder Sign',
  'Shrivelling',
  'Daisy Walker'
]]
pdf = PDFBuilder(cards)
pdf.write('proxies.pdf')
```

## Using OCTGN images

You will need to first download the image packs from <https://ahlcgoctgn.wordpress.com/image-packs/> into a subfolder named `o8c` in your application support directory (`Library/Application Support/arkham_utils/o8c` on MacOS).

```py
from arkham_utils.octgn import db
from arkham_utils.pdf.builder import PDFBuilder

cards = [db.find(name) for name in [
  'Blackjack',
  'Guts',
  'Emergency Cache',
  'Elder Sign',
  'Shrivelling',
  'Daisy Walker'
]]
pdf = PDFBuilder(cards)
pdf.write('proxies.pdf')
```

### Proxying an entire set

```py
from arkham_utils.octgn import db
from arkham_utils.pdf.builder import PDFBuilder, PDFBuilderConfig

# write all the non-mini cards as a PDF
barkham = db.find_set('Meowlathotep')
PDFBuilder([c for c in barkham.cards if c.type != 'Mini']).write('barkham.pdf')

# write the mini investigator cards
mini_cfg = PDFBuilderConfig()
mini_cfg.cards_per_row = 4
mini_cfg.rows_per_page = 4
mini_cfg.card_height = 2.5
mini_cfg.card_width = 1.625
PDFBuilder([c for c in barkham.cards if c.type == 'Mini'], mini_cfg).write('barkham_minis.pdf')
```

### Proxying a deck

Download the taboo PDF from https://www.fantasyflightgames.com/en/products/arkham-horror-the-card-game/ FAQ section.

Download the Scarlet Keys Investigator upgrade sheets from the Player Resources section.

```py
from arkham_utils.arkhamdb.public_deck import ArkhamDBPublicDeck
from arkham_utils.pdf.builder import PDFBuilder

deck = ArkhamDBPublicDeck(ARKHAMDB_DECK_ID, 
  taboo_pdf='chapter_one_taboo_cards_v25_web.pdf', 
  customizable_pdf='ahc69_upgrades_v5.pdf', 
  include_investigator=True, 
  include_signature_cards=True,
  use_octgn=True)

pdf = PDFBuilder(deck.cards)
pdf.write('deck.pdf')
```