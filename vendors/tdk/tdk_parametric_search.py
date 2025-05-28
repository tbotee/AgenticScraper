
import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
from requests_html import HTMLSession
import warnings
import os
import nest_asyncio
from playwright.sync_api import sync_playwright

from utils.cache_helper import cache_json_result
from utils.llm_helper import LLMHelper
from utils.llms.gemini import Gemini
from utils.parametric_base import ParametricBase
from vendors.tdk.models.category import Category
from vendors.tdk.models.filter import Filter


class TdkParametricSearch(ParametricBase, Gemini):
    def __init__(self):
        super().__init__()
        self.base_url = "https://product.tdk.com"
        self.llm_helper = LLMHelper()
        Gemini.__init__(self)  # Initialize Gemini client
    
    def search_by_parameters(self, category: str, subcategory: str = None, parameters: Dict[str, str] = None, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search for products based on specific parameters.
        
        Args:
            category (str): The main category to search in
            subcategory (str): The subcategory to search in
            parameters (Dict[str, str]): Dictionary of parameters to filter by
            max_results (int): Maximum number of results to return
            
        Returns:
            List[Dict[str, str]]: List of dictionaries containing product details
        """
        try:   
            
            # categories = self._get_categories()
            # search_page_url = self._get_category_page(category, subcategory, categories)

            # search_page_url = "https://product.tdk.com/en/search/emc/emc/3tf/characteristic"

            # form_data = self._serialize_form(search_page_url)

            # if len(form_data) == 0:
            #     self.logger.error("No form data found")
            #     return []

            # arguments = self._get_arguments(form_data, parameters)

            # products = self._get_products(search_page_url, arguments, max_results)
            products = self._get_products('https://product.tdk.com/en/search/emc/emc/3tf/list#ref=characteristic&3rvdct=33&3ilt=35&3ilFreqMint=2000&_l=10&_p=1&_c=pure_status-pure_status&_d=0', [], max_results)

            return products
            
        except Exception as e:  
            self.logger.error(str(e))
            return []
        
    def _get_products(self, search_page_url: str, arguments: list[Filter], max_results: int = 10) -> List[Dict[str, str]]:
        """
        Get products from the search page.

        Args:
            search_page_url (str): URL of the search page
            arguments (List[Dict[str, str]]): List of filter arguments
            max_results (int): Maximum number of results to return

        Returns:
            List[Dict[str, str]]: List of product dictionaries with mpn, url, and details
        """
        # Convert characteristic URL to list URL
        list_url = search_page_url.replace('/characteristic', '/list#ref=characteristic')
        
        # Add arguments to URL
        if arguments:
            query_params = []
            for filter in arguments:
                query_params.append(f"{filter.key}={filter.value}")
            list_url = f"{list_url}&{'&'.join(query_params)}&_l={max_results}&_p=1&_c=pure_status-pure_status&_d=0"
            
        self.logger.info(f"Searching products with URL: {list_url}")
        products = []
        
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            
            # Set headers
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })
            
            # Navigate to the page
            page.goto(list_url, wait_until='networkidle')
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find the table
            table = soup.find('table', {'id': 'table_result'})
            if not table:
                self.logger.warning("No product table found")
                return products
                
            # Get headers
            headers = []
            header_row = table.find('thead').find('tr')
            for th in header_row.find_all('th'):
                # Get the header text, removing any help icons
                header_text = th.get_text(strip=True)
                if header_text:
                    headers.append(header_text)
            
            # Process each row
            for row in table.find('tbody').find_all('tr', {'class': 'listBottr01'}):
                details = {}
                mpn = None
                url = None
                
                # Get all cells in the row
                cells = row.find_all('td')
                
                # Map each cell to its corresponding header
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        # Get the cell text, handling special cases
                        cell_text = cell.get_text(strip=True)
                        
                        # Handle special cases for certain columns
                        if headers[i] == 'Part No.':
                            # Get the part number from the link
                            part_link = cell.find('a')
                            if part_link:
                                mpn = part_link.get_text(strip=True)
                                url = part_link.get('href', '')
                                if url and not url.startswith('http'):
                                    url = f"{self.base_url}{url}"
                        elif headers[i] == 'Catalog / Data Sheet':
                            # Get the catalog link
                            catalog_link = cell.find('a')
                            if catalog_link:
                                cell_text = catalog_link.get('href', '')
                        elif headers[i] == 'Images':
                            # Get the image URL
                            img = cell.find('img')
                            if img:
                                cell_text = img.get('src', '')
                        elif headers[i] == 'Distributor Inventory':
                            # Get the buy/contact link
                            link = cell.find('a')
                            if link:
                                cell_text = link.get('href', '')
                                
                        details[headers[i]] = cell_text
                
                if mpn:  # Only add products that have a part number
                    products.append({
                        'mpn': mpn,
                        'url': url,
                        'details': details
                    })
            
            browser.close()
            
        return products

    def _get_arguments(self, form_data: Dict[str, Dict], parameters: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Get the arguments for the search.
        """

        filters = self._detect_filters_from_prompt_by_llm(parameters['details'])

        self.logger.info(f"Mapping filters to search form: {filters}")

        if 'details' in parameters:
            prompt = f"""
                ou are provided with a list of JSON filters: {filters}

                Your task is to match and map these filters to the appropriate inputs in a search form. Please follow these steps:

                1. For each filter in the list, find the most likely corresponding input in the search form by comparing the filter's key with the form input's **label** and **name** fields. Use semantic similarity and context clues to make the best match.
                2. Replace the filter's key with the 'name' of the matched input field from the form.
                3. If the filter type is 'select', 'radio', or 'checkbox', choose the most likely value from the filter's 'values' list that corresponds to the input's expected value.
                4. If the filter represents a **range** (e.g., `frequencyMin` and `frequencyMax`), attempt to match and map **each side independently**:
                - Match both `Min` and `Max` values even if they are the same.
                - Return each as a separate entry with the appropriate input name (e.g., `3il_freq_min[t]`, `3il_freq_max[t]`).
                - Do **not skip** `frequencyMax` just because `frequencyMin` has the same value.

                Only include filters that can be confidently matched to input fields in the form. If no match can be found for a filter, omit it.

                Return the result in the following JSON format:

                [
                    {{
                        "input_name": "selected_value"
                    }},
                    ...
                ]

                - The key (`input_name`) must be taken from the 'name' field of the matched input in the form.
                - Use the input's **label** to help determine the correct match when names are not obvious.
                - If no valid mappings are found, return an empty list: []

                Here is the search form (in JSON format):

                {form_data}
            """

            mapped_filters: list[Filter] = self.generate_llm_json(prompt, Filter)
            if len(mapped_filters) == 0:
                raise Exception("No filters found for the given prompt")
            
            self.logger.info(f"Found {len(mapped_filters)} filters in the mapped search form.")
            return mapped_filters
            
        return []

    @cache_json_result(cache_dir="llm_cache")
    def _detect_filters_from_prompt_by_llm(self, prompt: str) -> list[Filter]:

        self.logger.info(f"Detecting number of filters from prompt.")
        prompt = f"""
            You are given a product search prompt: '{prompt}'
            Detect all filters from the prompt. Get the name and the value of the filter.
            If you detect a range, return two values, one for the minimum and one for the maximum and add 'min' and 'max' to the name of the filter separate it with a space. 
            If you detect a range filter but only one value is provided, don't return 2 filters, just return one filter with the value.
            Range filters are usually in the format of "from X to Y" or "min X max Y" or something similar.
            Dont format the key with - or _ just use the name.
        """

        filters = self.generate_llm_json(prompt, Filter)
        self.logger.info(f"Found {len(filters)} filters in the prompt.")
        return filters


    def _get_category_page(self, category: str, subcategory: str, categories: List[Dict[str, str]]) -> str:
        """
        Determine the category path for a given category and subcategory.
        
        Args:
            category (str): The main category to search in
            subcategory (str): The subcategory to search in
        """
        main_category: list[Category] = self._get_category_url(category, categories)

        if not main_category or len(main_category) == 0:
            self.logger.error(f"Category not found: {category}")
            raise Exception(f"Category not found: {category}")

        if subcategory is not None:
            subcategories = self._get_subcategories(subcategory, main_category[0].url)
            sub_category: list[Category] = self._get_category_url(subcategory, subcategories)
            if not sub_category or len(sub_category) == 0:
                self.logger.error(f"Subcategory not found: {subcategory}")
                raise Exception(f"Subcategory not found: {subcategory}")
            
            return sub_category[0].url
            
        
    def _get_category_url(self, category: str, categories: List[Dict[str, str]]) -> Dict[str, str]:
        self.logger.info(f"Getting category page for: {category} ")
        prompt = f"""
            Determine the most likely url for the following category: {category} from the following list of categories: {categories}

            Return the result in the following json format:
            {{
                "name": "Category Name",
                "url": "here the most likely url for the category"
            }}

            If the category is not found, return:
            {{
                "category_name": "category name", 
                "url": ""
            }}
        """

        return self.generate_llm_json(prompt, Category)
    
    def _get_subcategories(self, subcategory: str, main_category_url: str) -> List[Dict[str, str]]:

        self.logger.info(f"Getting subcategory page for: {subcategory} from: {main_category_url}")


        self.logger.info(f"Getting categories from: {main_category_url}")
        response = self.session.get(main_category_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        categories = []
        
        # Find all category elements
        category_elements = soup.select('div.taxonomy-term')
        
        for element in category_elements:
            # Get category name
            name_element = element.select_one('.lineup-name')
            if not name_element:
                continue
            category_name = name_element.get_text(strip=True)
            
            # Get category URL from the "Search by Characteristics" link
            dropdown = element.select_one('.lineup_dropdown')
            if not dropdown:
                continue
                
            characteristic_link = dropdown.select_one('a[href*="/characteristic"]')
            if not characteristic_link:
                continue
                
            category_url = characteristic_link.get('href')
            if not category_url:
                continue
                
            # Make sure we have absolute URLs
            if not category_url.startswith('http'):
                category_url = f"{self.base_url}{category_url}"
            
            categories.append({
                'name': category_name,
                'link': category_url
            })

        if len(categories) == 0:
            self.logger.error(f"Subcategory not found: {subcategory}")
            raise Exception(f"Subcategory not found: {subcategory}")
        
        return categories
        

    @cache_json_result(cache_dir="llm_cache")
    def _get_categories(self) -> List[Dict[str, str]]:
        """
        Fetch all product categories from TDK's product page.
        
        Returns:
            List[Dict[str, str]]: List of dictionaries containing category names and links
        """
        # Make request to the product page
        self.logger.info(f"Getting categories from: {self.base_url}/en/products/index.html")
        response = self.session.get(f"{self.base_url}/en/products/index.html")
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all category elements
        categories = []
        category_elements = soup.select('div.field--name-field-image a')
        
        for element in category_elements:
            # Get the category link
            category_link = element.get('href')
            if not category_link:
                continue
                
            # Make sure we have absolute URLs
            if not category_link.startswith('http'):
                category_link = f"{self.base_url}{category_link}"
            
            # Get the category name from the image alt text or link text
            category_name = None
            img = element.find('img')
            if img:
                category_name = img.get('alt', '').strip()
            
            if not category_name:
                # Try to get name from the link text
                category_name = element.get_text(strip=True)
            
            # Extract category name from URL if still not found
            if not category_name:
                category_name = category_link.split('/')[-2].replace('-', ' ').title()
            
            if category_name and category_link:
                categories.append({
                    'name': category_name,
                    'link': category_link
                })
        
        return categories
            
    @cache_json_result(cache_dir="llm_cache")
    def _serialize_form(self, search_page_url: str) -> Dict[str, Dict]:
        """
        Serialize the form data from the conditions-normal div.
        
        Args:
            search_page_url (str): url of the search page
            
        Returns:
            Dict[str, Dict]: Dictionary containing form field information
        """
        self.logger.info(f"Serializing form for: {search_page_url}")
        try:
            with sync_playwright() as p:
                browser = p.webkit.launch(headless=True)
                page = browser.new_page()
                
                # Set headers
                page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                })
                
                # Navigate to the page
                page.goto(search_page_url, wait_until='networkidle')
                
                # Get the page content
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                form_data = {}
                
                # Find the conditions-normal div
                conditions_div = soup.find('div', {'id': 'conditions-normal'})
                if not conditions_div:
                    self.logger.warning(f"No conditions-normal div found at {search_page_url}")
                    return form_data
                    
                # Process each fieldset
                for fieldset in conditions_div.find_all('fieldset'):
                    # Get the field label
                    legend = fieldset.find('legend')
                    if not legend:
                        continue
                        
                    label = legend.find('span', {'class': 'ui_title'}).text.strip()
                    
                    # Get the field name and type
                    field_info = {
                        'label': label,
                        'type': None,
                        'name': None,
                        'values': []
                    }
                    
                    # Check for different input types
                    inputs = fieldset.find_all(['input', 'select'])
                    if not inputs:
                        continue
                        
                    # Get the first input to determine type
                    first_input = inputs[0]
                    input_type = first_input.get('type', '')
                    field_info['type'] = input_type
                    
                    # Handle different input types
                    if input_type in ['text', 'number']:
                        field_info['name'] = first_input.get('name')
                        # Get range if available
                        range_div = fieldset.find('div', {'class': 'inputtablerange'})
                        if range_div:
                            min_val = range_div.find('span', {'id': lambda x: x and x.endswith('-min')})
                            max_val = range_div.find('span', {'id': lambda x: x and x.endswith('-max')})
                            if min_val and max_val:
                                field_info['min'] = min_val.text.strip()
                                field_info['max'] = max_val.text.strip()
                                
                    elif input_type == 'checkbox':
                        field_info['name'] = first_input.get('name')
                        field_info['values'] = [
                            {
                                'value': input_elem.get('value'),
                                'label': input_elem.find_next('span').text.strip()
                            }
                            for input_elem in inputs
                        ]
                        
                    elif input_type == 'radio':
                        field_info['name'] = first_input.get('name')
                        field_info['values'] = [
                            {
                                'value': input_elem.get('value'),
                                'label': input_elem.find_next('span').text.strip(),
                                'checked': input_elem.get('checked') is not None
                            }
                            for input_elem in inputs
                        ]
                        
                    elif first_input.name == 'select':
                        field_info['name'] = first_input.get('name')
                        field_info['values'] = [
                            {
                                'value': option.get('value'),
                                'label': option.text.strip(),
                                'selected': option.get('selected') is not None
                            }
                            for option in first_input.find_all('option')
                        ]
                    
                    # Add to form data using fieldset id as key
                    fieldset_id = fieldset.get('id')
                    if fieldset_id:
                        form_data[fieldset_id] = field_info
                        
                browser.close()
                return form_data
                
        except Exception as e:
            self.logger.error(f"Error serializing form: {e}")
            return {}
            
    
