from typing import Dict, List
from arkham_utils.arkhamdb.card import ArkhamDBCard
from arkham_utils.arkhamdb.constants import API
import requests


class ArkhamDBPublicDeck(object):
  id: int
  data: object
  _cards: Dict[str, ArkhamDBCard]

  #: Placeholder code for the "Random Basic Weakness" slot filler.
  RANDOM_BASIC_WEAKNESS = '01000'

  def __init__(self, id: int, is_decklist: bool = False,
               taboo_pdf: str | None = None, taboo_zoom: int = 4,
               customizable_pdf: str | None = None,
               customizable_zoom: int = 4,
               include_random_weakness: bool = False,
               include_investigator: bool = False,
               include_signature_cards: bool = False,
               use_octgn: bool = False):
    self.id = id
    key = 'decklist' if is_decklist else 'deck'
    r = requests.get(f"{API}/{key}/{self.id}.json")
    print(f"{API}/{key}/{self.id}.json")
    print(r.content)
    self.data = r.json()
    self._cards = None
    self.taboo_pdf = taboo_pdf
    self.taboo_zoom = taboo_zoom
    self._taboo = None
    self.customizable_pdf = customizable_pdf
    self.customizable_zoom = customizable_zoom
    self._checklists = None
    self.include_random_weakness = include_random_weakness
    self.include_investigator = include_investigator
    self.include_signature_cards = include_signature_cards
    self.use_octgn = use_octgn
    self._investigator = None
    self._octgn = None
    self._octgn_cards = {}

  @property
  def taboo_id(self) -> int | None:
    return self.data.get('taboo_id')

  @property
  def taboo(self):
    """The Taboo list this deck conforms to, or None.

    Always loads the taboo card data when the deck has a `taboo_id`;
    replacement images are only available when `taboo_pdf` was supplied.
    """
    from arkham_utils.arkhamdb.taboo import Taboo
    if self.taboo_id is None:
      return None
    if self._taboo is None:
      self._taboo = Taboo(self.taboo_id, pdf_file=self.taboo_pdf,
                          zoom=self.taboo_zoom)
    return self._taboo

  @property
  def checklists(self):
    """Upgrade checklists for customizable cards, or None.

    Unlike `taboo`, this needs no deck metadata: whether a card needs
    a checklist comes from the card itself (`is_customizable`). It
    exists exactly when a `customizable_pdf` was supplied.
    """
    from arkham_utils.arkhamdb.customizable import CustomizableChecklists
    if self.customizable_pdf is None:
      return None
    if self._checklists is None:
      self._checklists = CustomizableChecklists(self.customizable_pdf,
                                               zoom=self.customizable_zoom)
    return self._checklists

  @property
  def investigator(self) -> ArkhamDBCard | None:
    """The deck's investigator card (double-sided), or None if unknown."""
    code = self.data.get('investigator_code')
    if code is None:
      return None
    if self._investigator is None:
      self._investigator = ArkhamDBCard.from_id(code)
    return self._investigator

  @property
  def _octgn_db(self):
    """The OCTGN set database, or None when `use_octgn` is off.

    Imported lazily: importing `arkham_utils.octgn` downloads/parses
    the set data and requires local `o8c` image packs, so non-OCTGN
    users must never pay that cost.
    """
    if not self.use_octgn:
      return None
    if self._octgn is None:
      from arkham_utils.octgn import db as octgn_db
      self._octgn = octgn_db
    return self._octgn

  def _to_octgn(self, card):
    """Swap an ArkhamDBCard for its OCTGN equivalent.

    Returns `card` unchanged when OCTGN is off, the card has no
    `octgn_id`, the OCTGN set DB has no match, or its image packs
    lack the images. PDF-sourced cards (taboo replacements,
    checklists) are not ArkhamDBCards and pass through untouched.
    Double-sided ids (`front:back`) fall back to the front half.
    """
    if self._octgn_db is None or not isinstance(card, ArkhamDBCard):
      return card
    if card.code in self._octgn_cards:
      return self._octgn_cards[card.code]
    found = None
    oid = card.data.get('octgn_id')
    if oid:
      found = self._octgn_db.lookup(oid)
      if found is None and ':' in oid:
        found = self._octgn_db.lookup(oid.split(':')[0])
    if found is not None:
      try:
        found.images  # eager: missing image packs raise KeyError here
      except KeyError:
        found = None
    resolved = found if found is not None else card
    self._octgn_cards[card.code] = resolved
    return resolved

  @property
  def cards(self):
    if self._cards is None:
      self._cards = {}
      for id in self.data['slots']:
        self._cards[id] = ArkhamDBCard.from_id(id)

    all_cards = []
    if self.include_investigator and self.investigator is not None:
      all_cards.append(self._to_octgn(self.investigator))
    for id, count in self.data['slots'].items():
      if id == self.RANDOM_BASIC_WEAKNESS and not self.include_random_weakness:
        continue
      card = self._cards[id]
      # Signature status is a property of the base card, not its taboo
      # replacement (TabooCard has no card data).
      if not self.include_signature_cards and card.is_signature:
        continue
      if self.taboo is not None:
        card = self.taboo.card_for(card)
      card = self._to_octgn(card)
      all_cards.extend([card] * count)
      # Checklist sheets go in *addition to* the base card. A single
      # copy is shared no matter how many copies of the card are in
      # the deck. Customizability is a property of the base card, not
      # its taboo replacement (TabooCard has no is_customizable).
      if self.checklists is not None:
        checklist = self.checklists.checklist_for(self._cards[id])
        if checklist is not None:
          all_cards.append(checklist)

    return all_cards

  def dump(self):
    self.cards
    from arkham_utils.arkhamdb.taboo import TabooCard
    print(f"{self.data['name']}")
    if self.include_investigator and self.investigator is not None:
      inv = self._to_octgn(self.investigator)
      suffix = " (octgn)" if inv is not self.investigator else ""
      print(f"  {self.investigator.name} (investigator){suffix} x1")
    for id, count in self.data['slots'].items():
      if id == self.RANDOM_BASIC_WEAKNESS and not self.include_random_weakness:
        continue
      card = self._cards[id]
      if not self.include_signature_cards and card.is_signature:
        continue
      resolved = self.taboo.card_for(card) if self.taboo is not None else card
      suffix = " (taboo)" if isinstance(resolved, TabooCard) else ""
      if self._to_octgn(resolved) is not resolved:
        suffix += " (octgn)"
      print(f"  {card.name}{suffix} x{count}")
      checklist = self.checklists.checklist_for(card) if self.checklists is not None else None
      if checklist is not None:
        print(f"  {card.name} checklist x1")
