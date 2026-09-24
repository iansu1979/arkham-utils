import glob
import zipfile
import re
from PIL import Image
from platformdirs import user_data_dir
import os

# download files from https://ahlcgoctgn.wordpress.com/image-packs/ into o8c/
class OctgnImageDatabase(object):
    def __init__(self, path='o8c'):
        if not os.path.exists(path):
            raise RuntimeError(f'{path} does not exist! Please download the image packs from https://ahlcgoctgn.wordpress.com/image-packs/ into {path}')
        
        self.images = {} # uuid -> (zip_name, zip_internal_file)
        self.images_back = {}
        for o8c in glob.glob(f'{path}/*.o8c'):
            with zipfile.ZipFile(o8c) as z:
                for f in z.filelist:
                    m = re.match(
                        r'[^/]+/Sets/[^/]+/Cards/([^\.]+)\.(jpg|png)$', f.filename)
                    if m is not None:
                        uuid = m.group(1)
                        self.images[uuid] = (o8c, f.filename)
                    else:
                        m = re.match(
                            r'[^/]+/Sets/[^/]+/Cards/([^\.]+)\.[A-Za-z]\.(jpg|png)$', f.filename)
                        if m is not None:
                            uuid = m.group(1)
                            self.images_back[uuid] = (o8c, f.filename)

        print(f'loaded {len(self.images)} card images and {len(self.images_back)} back images')
    
    def get_image(self, card_id, front=True):
        images = self.images if front else self.images_back
        if card_id not in images:
            raise KeyError('unknown card_id', card_id)
        o8c, fname = images[card_id]
        with zipfile.ZipFile(o8c) as z:
            with z.open(fname) as f:
                i = Image.open(f)
                i.load()
        return i
    
    def get_images(self, card_id):
        front = self.get_image(card_id)
        try:
            back = self.get_image(card_id, False)
            return front, back
        except KeyError:
            return front,

image_db = OctgnImageDatabase(f'{user_data_dir("arkham_utils")}/o8c')