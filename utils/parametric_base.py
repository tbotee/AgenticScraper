from abc import abstractmethod

class ParametricBase:
    @abstractmethod
    def search_by_parameters(self, category, subcategory=None, parameters=None, max_results=10) -> list:
        pass

