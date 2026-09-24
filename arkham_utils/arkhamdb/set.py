from typing import Generator, Callable
import requests
from arkham_utils.arkhamdb.card import ArkhamDBCard
from arkham_utils.arkhamdb.constants import API
import re

class ArkhamDBSet(object):
    def __init__(self, data):
        self.data = data
        self._cards = None

    def _lazy_load_cards(self, include_encounter=True):
        if self._cards is not None:
            return
        r = requests.get(
            f"{API}/cards/{self.data['code']}?encounter={1 if include_encounter else 0}")
        cards_data = r.json()
        self._cards = [ArkhamDBCard(data) for data in cards_data]

    @property
    def name(self):
        return self.data['name']

    @property
    def cards(self):
        self._lazy_load_cards()
        return self._cards

    def find_by_regex(self, regex: str | re.Pattern[str]) -> Generator[ArkhamDBCard, None, None]:
        for c in self.cards:
            if re.match(regex, c.name):
                yield c

    def find_by_predicate(self, predicate: Callable[[ArkhamDBCard], bool]) -> Generator[ArkhamDBCard, None, None]:
        for c in self.cards:
            if predicate(c):
                yield c
