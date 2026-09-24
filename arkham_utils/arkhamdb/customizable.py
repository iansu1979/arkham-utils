from PIL import Image

from arkham_utils.card import ArkhamCard


class CustomizableChecklistCard(ArkhamCard):
    """An upgrade checklist sheet for a customizable card.

    Unlike taboo replacements, this is added to a deck's cards *in
    addition to* the base card, not instead of it.
    """

    def __init__(self, image: Image.Image, code: str | None = None,
                 name: str | None = None):
        super().__init__(image)
        self.code = code
        self.name = name

    @property
    def type(self):
        return 'CustomizableChecklist'


class CustomizableChecklists(object):
    """Upgrade checklist sheets (e.g. ahc69_upgrades_v5.pdf) for
    customizable cards.

    Whether a card needs a checklist comes from the card data itself
    (`ArkhamDBCard.is_customizable`); this class only handles the PDF
    lookup, mirroring the reader role of `Taboo`.
    """

    def __init__(self, pdf_file: str, zoom: int = 4):
        self.pdf_file = pdf_file
        self.zoom = zoom
        self._reader = None
        self._image_cache: dict[str, Image.Image | None] = {}

    @property
    def reader(self):
        if self._reader is None:
            # Local import so this module works without PyMuPDF installed.
            from arkham_utils.pdf.image_reader import PDFImageReader
            self._reader = PDFImageReader(self.pdf_file, zoom=self.zoom)
        return self._reader

    def image_for_card(self, card) -> Image.Image | None:
        if card.code in self._image_cache:
            return self._image_cache[card.code]
        img = self.reader.find_card_image_by_name(card.name)
        self._image_cache[card.code] = img
        return img

    def checklist_for(self, card) -> CustomizableChecklistCard | None:
        """Return the checklist sheet for `card`, or None.

        Returns None when the card is not customizable or no page in
        the PDF matches its name.
        """
        if not getattr(card, 'is_customizable', False):
            return None
        img = self.image_for_card(card)
        if img is None:
            return None
        return CustomizableChecklistCard(img, code=card.code, name=card.name)
