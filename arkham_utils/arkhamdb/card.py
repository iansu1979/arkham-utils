import requests
from arkham_utils.card import ArkhamCard
from PIL import Image
import io
import requests
from arkham_utils.arkhamdb.constants import API


def _get_image_from_url(url) -> Image.Image:
    r = requests.get(url)
    return Image.open(io.BytesIO(r.content))


def _get_linked_back_image(data) -> Image.Image | None:
    """Back image for split two-sided cards (e.g. Discipline `08011a`).

    ArkhamDB models these as two records linked by `linked_to_code`
    rather than a single record with `backimagesrc`. Returns None when
    there is no linked card or its image cannot be fetched.
    """
    code = data.get('linked_to_code')
    if not code:
        return None
    try:
        back = requests.get(f"{API}/card/{code}.json").json()
    except requests.RequestException:
        return None
    if 'imagesrc' not in back:
        return None
    return _get_image_from_url(f'https://arkhamdb.com{back["imagesrc"]}')


class ArkhamDBCard(ArkhamCard):
    def __init__(self, data):
        self.data = data
        self._images = None

    def _lazy_load_images(self):
        if self._images is not None:
            return
        if 'backimagesrc' in self.data:
            self._images = _get_image_from_url(f'https://arkhamdb.com{self.data["imagesrc"]}'), _get_image_from_url(
                f'https://arkhamdb.com{self.data["backimagesrc"]}')
        elif 'imagesrc' in self.data:
            front = _get_image_from_url(
                f'https://arkhamdb.com{self.data["imagesrc"]}')
            back = _get_linked_back_image(self.data)
            self._images = (front, back) if back is not None else (front,)
        else:
            self._images = []
            print(f"{self.name} has no images!")

    @property
    def code(self):
        return self.data['code']

    @property
    def name(self):
        return self.data['name']

    @property
    def image(self):
        self._lazy_load_images()
        return self._images[0]
    
    @property
    def faction(self):
        return self.data['faction_code']
    
    @property
    def type(self):
        return self.data['type_code']

    @property
    def is_customizable(self) -> bool:
        return bool(self.data.get('customization_options'))

    @property
    def is_signature(self) -> bool:
        """Investigator signature cards (asset or weakness)."""
        return bool((self.data.get('restrictions') or {}).get('investigator'))

    @property
    def images(self):
        self._lazy_load_images()
        return self._images

    @staticmethod
    def from_id(id: str):
        r = requests.get(f"{API}/card/{id}.json")
        return ArkhamDBCard(r.json())
