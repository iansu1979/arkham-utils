from abc import ABC,abstractmethod

class ArkhamCard(ABC):
    def __init__(self, front, back=None):
        self._images = (front, back) if back else front,

    @property
    def image(self):
        return self._images[0]

    @property
    def images(self):
        return self._images
    
    @property
    @abstractmethod
    def type(self):
        return 'Card'

class ArkhamRawCard(ArkhamCard):
    @property
    def type(self):
        return 'RawCard'