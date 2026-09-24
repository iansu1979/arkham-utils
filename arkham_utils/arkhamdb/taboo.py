import json

import requests
from PIL import Image

from arkham_utils.arkhamdb.constants import API
from arkham_utils.card import ArkhamCard

# Cache for the raw /taboos/ payload so multiple Taboo instances
# (e.g. one per deck) don't each refetch the full list.

_taboos_cache = None


def _load_taboos_data():
    global _taboos_cache
    if _taboos_cache is None:
        r = requests.get(f"{API}/taboos/")
        r.raise_for_status()
        _taboos_cache = r.json()
    return _taboos_cache


class TabooCard(ArkhamCard):
    """A replacement card image taken from a taboo PDF."""

    def __init__(self, image: Image.Image, code: str | None = None,
                 name: str | None = None, taboo_text: str | None = None):
        super().__init__(image)
        self.code = code
        self.name = name
        self.taboo_text = taboo_text

    @property
    def type(self):
        return 'TabooCard'


class Taboo(object):
    """A single taboo list (e.g. id 9) plus its replacement-card PDF.

    The public API (GET /api/public/taboos/) returns every list; each
    list's `cards` field is itself a JSON-encoded string mapping
    5-character card codes (the same codes used as keys in a deck's
    `slots` dict) to modifications such as `xp`, `text`, `deck_limit`
    or `exceptional`.
    """

    id: int
    data: dict
    entries: dict[str, dict]

    def __init__(self, taboo_id: int, pdf_file: str | None = None, zoom: int = 4):
        self.id = taboo_id
        self.pdf_file = pdf_file
        self.zoom = zoom
        self._reader = None
        self._image_cache: dict[str, Image.Image | None] = {}

        for t in _load_taboos_data():
            if t['id'] == taboo_id:
                self.data = t
                break
        else:
            raise ValueError(f"Unknown taboo id: {taboo_id}")

        cards = self.data.get('cards', '[]')
        if isinstance(cards, str):
            cards = json.loads(cards)
        self.entries = {e['code']: e for e in cards}

    @property
    def reader(self):
        if self._reader is None:
            if self.pdf_file is None:
                raise ValueError("No pdf_file supplied for taboo images")
            # Local import so taboo metadata works without PyMuPDF installed.
            from arkham_utils.pdf.image_reader import PDFImageReader
            self._reader = PDFImageReader(self.pdf_file, zoom=self.zoom)
        return self._reader

    def is_tabooed(self, code: str) -> bool:
        return code in self.entries

    def has_text_change(self, code: str) -> bool:
        return 'text' in self.entries.get(code, {})

    def get_entry(self, code: str) -> dict | None:
        return self.entries.get(code)

    def image_for_name(self, name: str) -> Image.Image | None:
        return self.reader.find_card_image_by_name(name)

    def image_for_code(self, code: str, name: str | None = None) -> Image.Image | None:
        """Look up the replacement image for a card code.

        `name` avoids an extra /card/ fetch when the caller already has it.
        Returns None when the card is not tabooed, has no PDF, or no
        page matches.
        """
        if code in self._image_cache:
            return self._image_cache[code]
        if self.pdf_file is None or not self.is_tabooed(code):
            self._image_cache[code] = None
            return None
        if name is None:
            # Local import to avoid a circular import.
            from arkham_utils.arkhamdb.card import ArkhamDBCard
            name = ArkhamDBCard.from_id(code).name
        img = self.image_for_name(name)
        self._image_cache[code] = img
        return img

    def card_for(self, card, name: str | None = None) -> ArkhamCard:
        """Return a TabooCard replacement if a PDF image exists, else `card`.

        Accepts either an ArkhamDBCard (uses its `.code`/`.name`) or a
        bare code string (returns None instead of the original on a miss).
        """
        code = card if isinstance(card, str) else card.code
        label = name or (None if isinstance(card, str) else card.name)
        entry = self.get_entry(code)
        if entry is None:
            return None if isinstance(card, str) else card
        img = self.image_for_code(code, name=label)
        if img is None:
            return None if isinstance(card, str) else card
        return TabooCard(img, code=code,
                         name=label if label is not None else code,
                         taboo_text=entry.get('text'))
