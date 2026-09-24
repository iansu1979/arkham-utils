import glob
import re
import time
from typing import List
import zipfile

import requests
import os

from arkham_utils.octgn.set import OctgnSet
from platformdirs import user_data_dir

class OctgnSetDatabase(object):
    sets: List[OctgnSet]
    path: str

    @property
    def gitzip(self):
        return f'{self.path}/o8g.zip'

    def download(self):
        if os.path.exists(self.gitzip) and os.path.getmtime(self.gitzip) > time.time() - 60 * 60 * 24:
            return
        os.makedirs(self.path, exist_ok=True)
        r = requests.get('https://github.com/GeckoTH/arkham-horror/archive/refs/heads/master.zip', allow_redirects=True)
        open(self.gitzip, 'wb').write(r.content)
    
    def __init__(self, path='o8g'):
        self.path = path
        self.sets = []
        self.download()
        with zipfile.ZipFile(self.gitzip) as z:
            for f in z.filelist:
                if f.filename.endswith('/set.xml'):
                    with z.open(f.filename) as fd:
                        s = OctgnSet(fd)
                        self.sets.append(s)
        print(f'loaded {len(self.sets)} sets, {sum([len(s.cards) for s in self.sets])} cards')
        
    def lookup(self, card_id):
        for s in self.sets:
            card = s.find(card_id)
            if card is not None:
                return card
        return None
    
    def find_all(self, regex, xp=None):
        for s in self.sets:
            for found in s.find_by_regex(regex, xp):
                yield found
                
    def find(self, regex, xp=None):
        return next(self.find_all(regex, xp))
    
    def find_all_sets(self, regex):
        for s in self.sets:
            if re.search(regex, s.name):
                yield s
    
    def find_set(self, regex):
        return next(self.find_all_sets(regex))
            
db = OctgnSetDatabase(f'{user_data_dir("arkham_utils")}/o8g')