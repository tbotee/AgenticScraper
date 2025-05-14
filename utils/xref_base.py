from abc import abstractmethod

class XrefBase:
    @abstractmethod
    def search_by_cross_reference(self, competitor_mpn, category_path=None):
        pass

