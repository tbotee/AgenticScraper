import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

from .search_engine import VendorSearchEngine

class ExampleMPNSearch(VendorSearchEngine):
    """Class for performing MPN-based searches on vendor website."""
    
    def search_by_mpn(self, mpn):
        """
        Search for a specific manufacturer part number.
        
        Args:
            mpn (str): The manufacturer part number to search for
            
        Returns:
            list: List of dictionaries with product information
        """
        self.navigate_to_search_page()
        
        try:
            # Find and fill the search input - adjust selector for specific vendor
            search_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#search-input, .search-box, input[name='q']"))
            )
            search_input.clear()
            
            # Type the MPN
            search_input.send_keys(mpn)
            
            # Wait briefly for auto-suggestions
            time.sleep(1)
            
            # Check if there are auto-suggestions to click
            suggestions = self.driver.find_elements(By.CSS_SELECTOR, 
                ".suggestion, .autocomplete-item, .typeahead-result")
            
            if suggestions:
                # Look for exact match in suggestions
                for suggestion in suggestions:
                    if mpn.lower() in suggestion.text.lower():
                        suggestion.click()
                        break
                else:
                    # If no exact match, just click the first suggestion
                    suggestions[0].click()
            else:
                # No suggestions, submit the search
                search_input.send_keys(Keys.RETURN)
            
            # Wait for results page to load
            time.sleep(2)
            
            # Parse and return results
            return self.parse_results()
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error in MPN search: {e}")
            return []