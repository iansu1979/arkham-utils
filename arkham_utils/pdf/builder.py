from typing import Dict, List, Tuple

from fpdf import FPDF

from arkham_utils.card import ArkhamCard
from PIL import Image


MAX_PAGES = 100
card_width = 2.4
card_height = 3.5
cards_per_row = 3
rows_per_page = 3
a4_width = 8.27
a4_height = 11.69
bleed_thickness = 0.05
padding = 0.015


class PDFBuilderConfig(object):
    card_width: float = card_width
    card_height: float = card_height
    cards_per_row: int = cards_per_row
    rows_per_page: int = rows_per_page
    bleed_thickness: float = bleed_thickness
    paper_width: float = a4_width
    paper_height: float = a4_height
    padding: float = padding


class PDFBuilder(object):
    def __init__(self, cards: List[ArkhamCard], config: PDFBuilderConfig = PDFBuilderConfig()):
        self.cards = cards
        self.config = config
        self.layout = self.get_layout()

    def get_layout(self) -> Dict[Tuple[int, int, int], Image.Image]:
        layout = {}
        twosided = [c for c in self.cards if len(c.images) == 2]
        onesided = [c for c in self.cards if len(c.images) == 1]
        for card in twosided:
            for _ in range(card.quantity):
                self.layout_2side(layout, card)
        for card in onesided:
            for _ in range(card.quantity):
                self.layout_1side(layout, card)
        return layout

    def layout_2side(self, layout, card: ArkhamCard):
        front, back = card.images
        if front.width < front.height:
            front = front.rotate(180)
        for p in range(MAX_PAGES):
            for r in range(0, self.config.rows_per_page, 2):
                if r + 1 == self.config.rows_per_page:
                    continue
                for c in range(self.config.cards_per_row):
                    if (p, r, c) not in layout:
                        layout[(p, r, c)] = back
                        layout[(p, r + 1, c)] = front
                        return
        raise RuntimeError('Exceeded last page')

    def layout_1side(self, layout, card: ArkhamCard):
        for p in range(MAX_PAGES):
            for r in range(self.config.rows_per_page):
                for c in range(self.config.cards_per_row):
                    if (p, r, c) not in layout:
                        layout[(p, r, c)] = card.image
                        return
        raise RuntimeError('Exceeded last page')

    def write(self, filename: str):
        padding_left = (self.config.paper_width -
                        (self.config.cards_per_row * self.config.card_width) - ((self.config.cards_per_row - 1) * self.config.padding)) / 2
        padding_top = (self.config.paper_height - (self.config.rows_per_page *
                       self.config.card_height) - ((self.config.rows_per_page - 1) * self.config.padding)) / 2

        pdf = FPDF(orientation='P', format='A4', unit='in')
        pages = max([p for (p, r, c) in self.layout]) + 1
        for p in range(pages):
            pdf.add_page()
            # add bleed bg
            for row in range(self.config.rows_per_page):
                for col in range(self.config.cards_per_row):
                    if (p, row, col) in self.layout:
                        pdf.rect(w=self.config.card_width + 2 * self.config.bleed_thickness,
                                 h=self.config.card_height + 2 * self.config.bleed_thickness,
                                 x=padding_left + col *
                                 (self.config.card_width + self.config.padding) -
                                 self.config.bleed_thickness,
                                 y=padding_top + row *
                                 (self.config.card_height + self.config.padding) -
                                 self.config.bleed_thickness,
                                 style='F')
            # add actual images
            for row in range(self.config.rows_per_page):
                for col in range(self.config.cards_per_row):
                    if (p, row, col) in self.layout:
                        image = self.layout[(p, row, col)]
                        if image.width > image.height:
                            image = image.rotate(-90, expand=True)
                        pdf.image(image, w=self.config.card_width, h=self.config.card_height, x=padding_left +
                                  col * (self.config.card_width +
                                         self.config.padding),
                                  y=padding_top + row * (self.config.card_height + self.config.padding))
        pdf.output(filename)
