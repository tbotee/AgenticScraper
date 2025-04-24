import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .search_engine import VendorSearchEngine

class ExampleParametricSearch(VendorSearchEngine):
    """Class for performing parametric searches on vendor website."""
    
    def search_by_parameters(self, category, subcategory=None, parameters=None, max_results=10):
        """
        Search using category navigation and parameter filters.
        
        Args:
            category (str): Main category name (e.g., "Capacitors")
            subcategory (str, optional): Subcategory name
            parameters (dict, optional): Parameters to filter by
                Format: {
                    "parameter_name": value,  # For single values
                    "parameter_name": {"min": min_val, "max": max_val},  # For ranges
                    "parameter_name": [val1, val2, ...]  # For multiple checkbox values
                }
            max_results (int): Maximum number of results to return
                
        Returns:
            list: List of dictionaries with product information
        """
        self.navigate_to_search_page()
        
        # Navigate to category
        if not self._navigate_to_category(category, subcategory):
            print(f"Failed to navigate to category: {category}, subcategory: {subcategory}")
            return []
            
        # Apply parameter filters if provided
        if parameters:
            self._apply_filters(parameters)
            
        # Parse results
        results = self.parse_results()
        
        # Limit results if needed
        return results[:max_results] if max_results and len(results) > max_results else results
    
    def _navigate_to_category(self, category, subcategory=None):
        """
        Navigate to a specific category and optional subcategory.
        
        Args:
            category (str): Main category name
            subcategory (str, optional): Subcategory name
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Find and click the main category - adjust selector for specific vendor
            category_elements = self.driver.find_elements(By.XPATH, 
                f"//a[contains(text(), '{category}')]")
            
            if not category_elements:
                # Try dropdown selection if no links found
                category_dropdown = self.driver.find_elements(By.CSS_SELECTOR, 
                    "select.category-select, #category-dropdown")
                
                if category_dropdown:
                    select = Select(category_dropdown[0])
                    select.select_by_visible_text(category)
                else:
                    return False
            else:
                # Click the first matching category link
                category_elements[0].click()
            
            # Wait for category page to load
            time.sleep(1.5)
            
            # If subcategory is provided, navigate to it
            if subcategory:
                subcategory_elements = self.driver.find_elements(By.XPATH, 
                    f"//a[contains(text(), '{subcategory}')]")
                
                if subcategory_elements:
                    subcategory_elements[0].click()
                    time.sleep(1.5)
                else:
                    # Try dropdown selection if no links found
                    subcategory_dropdown = self.driver.find_elements(By.CSS_SELECTOR, 
                        "select.subcategory-select, #subcategory-dropdown")
                    
                    if subcategory_dropdown:
                        select = Select(subcategory_dropdown[0])
                        select.select_by_visible_text(subcategory)
                    else:
                        return False
            
            return True
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error navigating to category: {e}")
            return False
    
    def _apply_filters(self, parameters):
        """
        Apply parameter filters to the search.
        
        Args:
            parameters (dict): Dictionary of parameters to filter by
        """
        for param_name, param_value in parameters.items():
            try:
                # Find parameter section - adjust for specific vendor
                param_elements = self.driver.find_elements(By.XPATH, 
                    f"//label[contains(text(), '{param_name}')]/following-sibling::*[1]")
                
                if not param_elements:
                    # Try alternative selectors
                    param_elements = self.driver.find_elements(By.XPATH, 
                        f"//div[contains(@class, 'filter-group')]//span[contains(text(), '{param_name}')]/../following-sibling::*")
                
                if param_elements:
                    # Handle different parameter types
                    if isinstance(param_value, dict) and ("min" in param_value or "max" in param_value):
                        # Range parameter
                        self._apply_range_filter(param_elements[0], param_value)
                    elif isinstance(param_value, list):
                        # Multiple checkbox values
                        self._apply_checkbox_filter(param_elements[0], param_value)
                    else:
                        # Single value (dropdown or text)
                        self._apply_single_value_filter(param_elements[0], param_value)
                
            except Exception as e:
                print(f"Error applying filter for {param_name}: {e}")
    
    def _apply_range_filter(self, element, value_dict):
        """Apply a range filter (min/max)."""
        # Find min and max inputs - adjust selectors for specific vendor
        inputs = element.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number']")
        
        if len(inputs) >= 2:
            # Typically, first input is min, second is max
            if "min" in value_dict and inputs[0]:
                inputs[0].clear()
                inputs[0].send_keys(str(value_dict["min"]))
            
            if "max" in value_dict and inputs[1]:
                inputs[1].clear()
                inputs[1].send_keys(str(value_dict["max"]))
                
            # Look for apply button
            apply_button = element.find_elements(By.CSS_SELECTOR, 
                "button.apply, button.filter-apply, input[type='submit']")
            
            if apply_button:
                apply_button[0].click()
    
    def _apply_checkbox_filter(self, element, values):
        """Apply checkbox filters for multiple values."""
        for value in values:
            # Find checkbox with matching value - adjust for specific vendor
            checkboxes = element.find_elements(By.XPATH, 
                f".//input[@type='checkbox']/following-sibling::label[contains(text(), '{value}')]/../input")
            
            if not checkboxes:
                # Try alternative selector
                checkboxes = element.find_elements(By.XPATH, 
                    f".//label[contains(text(), '{value}')]/input[@type='checkbox']")
            
            if checkboxes:
                if not checkboxes[0].is_selected():
                    checkboxes[0].click()
    
    def _apply_single_value_filter(self, element, value):
        """Apply a single value filter (dropdown or text)."""
        # Check if it's a dropdown
        dropdowns = element.find_elements(By.TAG_NAME, "select")
        
        if dropdowns:
            # It's a dropdown
            select = Select(dropdowns[0])
            select.select_by_visible_text(str(value))
        else:
            # Check if it's a text input
            inputs = element.find_elements(By.CSS_SELECTOR, "input[type='text']")
            
            if inputs:
                inputs[0].clear()
                inputs[0].send_keys(str(value))
                
                # Look for apply button
                apply_button = element.find_elements(By.CSS_SELECTOR, 
                    "button.apply, button.filter-apply, input[type='submit']")
                
                if apply_button:
                    apply_button[0].click()