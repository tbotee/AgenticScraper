
import requests

class BaseAPIClient:
    def __init__(self):
        """
        Initialize the API client with a logger.
        """
        from utils.logger import get_logger
        self.logger = get_logger(self.__class__.__name__)

    @property 
    def base_url(self):
        """
        Must be overridden by child classes.
        Returns:
            str: The base URL for the API
        """
        raise NotImplementedError("Subclasses must define a base_url")

    def default_headers(self):
        """
        Child classes can override this to add custom headers.
        Returns:
            dict: The default headers for the API
        """
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

    def get(self, endpoint, params=None):
        """
        Make a GET request to the API.
        Args:
            endpoint (str): The endpoint to request
            params (dict, optional): The parameters to send with the request
        Returns:
            dict: The JSON response from the API
        """
        url = self.base_url + endpoint
        try:
            response = requests.get(url, headers=self.default_headers(), params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            return None