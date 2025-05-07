from abc import ABC, abstractmethod

class MPNBase(ABC):
    @abstractmethod
    def get_products_by_number(self, number: str):
        pass