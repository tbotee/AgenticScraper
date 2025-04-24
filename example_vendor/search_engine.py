import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class VendorSearchEngine:
    """Base class for vendor website search operations."""
    
    BASE_URL = "https://example.com/search"  # Replace with actual vendor URL
    
    def __init__(self, driver):
        """
        Initialize the search engine with a WebDriver instance.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        
    def navigate_to_search_page(self):
        """Navigate to the vendor's product search page and handle any overlays."""
        self.driver.get(self.BASE_URL)
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for and handle any initial popups or cookie notices
        try:
            # Common selectors for cookie notices and popups
            selectors = [
                ".cookie-notice .accept", 
                "#cookie-consent-accept",
                ".popup-close",
                ".modal .close",
                "[data-dismiss='modal']"
            ]
            
            for selector in selectors:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if buttons:
                    buttons[0].click()
                    time.sleep(0.5)
                    break
                    
        except (TimeoutException, NoSuchElementException):
            # No popups found, continue
            pass
        
    def parse_results(self):
        """
        Parse search results and extract product information.
        
        Returns:
            list: List of dictionaries with product information
        """
        results = []
        
        try:
            # Wait for results to load - adjust selector for specific vendor
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results, .product-list, #results"))
            )
            
            # Find all product items - adjust selector for specific vendor
            product_items = self.driver.find_elements(By.CSS_SELECTOR, 
                ".product-item, .search-result-item, tr.result-row")
            
            for item in product_items:
                try:
                    # Extract MPN - adjust selectors for specific vendor
                    mpn_elem = item.find_element(By.CSS_SELECTOR, ".product-mpn, .part-number")
                    mpn = mpn_elem.text.strip()
                    
                    # Extract URL
                    link_elem = item.find_element(By.CSS_SELECTOR, "a")
                    url = link_elem.get_attribute("href")
                    
                    # Extract basic specifications if available
                    specs = {}
                    try:
                        spec_elems = item.find_elements(By.CSS_SELECTOR, ".specification")
                        for spec in spec_elems:
                            name = spec.get_attribute("data-name")
                            value = spec.text.strip()
                            if name and value:
                                specs[name] = value
                    except (NoSuchElementException, AttributeError):
                        pass
                    
                    # Only add if we have at least an MPN and URL
                    if mpn and url:
                        result = {
                            "mpn": mpn,
                            "url": url
                        }
                        
                        # Add specifications if found
                        if specs:
                            result["specifications"] = specs
                            
                        results.append(result)
                        
                except (NoSuchElementException, AttributeError) as e:
                    print(f"Error extracting product info: {e}")
                    continue
            
        except TimeoutException as e:
            print(f"Timeout waiting for results: {e}")
            
        return results