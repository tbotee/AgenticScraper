from abc import abstractmethod
import requests

class ParametricBase:
    @abstractmethod
    def search_by_parameters(self, category, subcategory=None, parameters=None, max_results=10) -> list:
        pass

    def __init__(self):
        self.session = requests.Session()
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })

        from utils.logger import get_logger
        self.logger = get_logger(self.__class__.__name__)

