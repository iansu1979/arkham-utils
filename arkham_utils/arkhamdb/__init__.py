import re
from typing import Generator, Callable
import requests
from arkham_utils.arkhamdb.card import ArkhamDBCard
from arkham_utils.arkhamdb.constants import API
from arkham_utils.arkhamdb.set import ArkhamDBSet
import requests_cache
from platformdirs import user_cache_dir

requests_cache.install_cache(
    f'{user_cache_dir("arkham_utils")}/arkhamdb_cache', expire_after=1800)


class ArkhamDB(object):
    def __init__(self):
        print('loading packs', f'{API}/packs/')
        r = requests.get(f'{API}/packs/')
        self.packs_data = r.json()
        self.packs = [ArkhamDBSet(pack) for pack in self.packs_data]
        print(f'loaded {len(self.packs)} packs')

    def find_all_sets(self, regex: str) -> Generator[ArkhamDBSet, None, None]:
        for s in self.packs:
            m = re.search(regex, s.name)
            if m:
                yield s

    def find_set(self, regex: str) -> ArkhamDBSet:
        return next(self.find_all_sets(regex))

    # beware that this will return Revised Core and Core together
    def find_sets_in_cycle(self, regex: str) -> Generator[ArkhamDBSet, None, None]:
        root = self.find_set(regex)
        cycle = root.data['cycle_position']
        for s in self.packs:
            if s.data['cycle_position'] == cycle:
                yield s

    def find_all_cards(self, regex: str) -> Generator[ArkhamDBCard, None, None]:
        for s in self.packs:
            for c in s.cards:
                m = re.search(regex, c.name)
                if m:
                    yield c

    def search(self, regex: str) -> ArkhamDBCard:
        return next(self.find_all_cards(regex))
    
    def find_by_predicate(self, predicate: Callable[[ArkhamDBCard], bool]) -> Generator[ArkhamDBCard, None, None]:
        for s in self.packs:
            for c in s.find_by_predicate(predicate):
                yield c


db = ArkhamDB()
