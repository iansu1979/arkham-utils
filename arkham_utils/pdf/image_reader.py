from typing import Generator, Tuple, List
from arkham_utils.card import ArkhamCard
from arkham_utils.pdf.builder import PDFBuilder
import fitz
from PIL import Image
import re


def card_name_pattern(name: str) -> str:
    """Build a PDF-text-tolerant regex for a card name.

    Extracted PDF text often differs from ArkhamDB names (curly vs.
    straight quotes, ligatures, dashes), so joining the alphanumeric
    tokens with a flexible non-word matcher matches across those
    punctuation variants.
    """
    tokens = re.findall(r'\w+', name, flags=re.UNICODE)
    if not tokens:
        return re.escape(name)
    return r'\W+'.join(re.escape(tok) for tok in tokens)


class PDFImageReader(object):
    def __init__(self, filename, zoom=4):
        self.filename = filename
        self.zoom = zoom
        self.pages: List[Tuple[Image.Image]] = None
    def get_images(self) -> Generator[Image.Image, None, None]:
        with fitz.open(self.filename) as pdf:
            mat = fitz.Matrix(self.zoom, self.zoom)
            for i in range(len(pdf)):
                page = pdf.load_page(i)
                pix = page.get_pixmap(matrix=mat)
                yield Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def find_image_by_regex(self, regexp: re.Pattern | str) -> Image.Image | None:
        if self.pages is None:
            self.pages = []
            with fitz.open(self.filename) as pdf:
                mat = fitz.Matrix(self.zoom, self.zoom)
                for i in range(len(pdf)):
                    page = pdf.load_page(i)
                    pix = page.get_pixmap(matrix=mat)
                    self.pages.append((Image.frombytes("RGB", [pix.width, pix.height], pix.samples), page.get_textpage().extractText()))
        for i, (img, txt) in enumerate(self.pages):
            m = re.search(regexp, txt, re.MULTILINE | re.IGNORECASE)
            if m is not None:
                print(f"Found {regexp} in {txt} (page {i+1})")
                return img
        return None

    def find_card_image_by_name(self, name: str) -> Image.Image | None:
        """Find a page by card name, tolerating PDF text quirks.

        Tries an exact match first, then falls back to a punctuation-
        tolerant pattern (see `card_name_pattern`).
        """
        img = self.find_image_by_regex(re.escape(name))
        if img is None:
            img = self.find_image_by_regex(card_name_pattern(name))
        return img

    def build_pdf(self):
        return PDFBuilder([ArkhamCard(im) for im in self.get_images()])
