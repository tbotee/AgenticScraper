# view-source:https://product.tdk.com/product_top_page/sitemap.xml


# https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C0402C0G1C100D020BC
from bs4 import BeautifulSoup
import requests
from utils.base_api_client import BaseAPIClient
from utils.mpn_base import MPNBase
import re


class TdkMpnSearch(MPNBase, BaseAPIClient):

    @property
    def base_url(self):
        return "https://product.tdk.com"

    def get_products_by_number(self, number: str) -> list:
        try:
            products = self._get_product_urls_and_numbers(number)

            for product in products:
                product['details'] = self._get_product_data(product)
                product['url'] = self.base_url + product['url']

            return products
        except Exception as e:
            self.logger.error(str(e))
            return None

        
    def _get_product_data(self, product: dict) -> dict:
        """
        Get the product data for a given product URL.

        Args:
            product (dict): The product URL to get data for
        """
        response_html = self.get(
            endpoint=product['url'],
            json=False
        )

        soup = BeautifulSoup(response_html, 'html.parser')
        content = soup.find('div', class_='unit_l')

        products = {}

        parse_product = self._parse_table(content, 'dimension', products)
        parse_product = self._parse_table(content, 'electrical_characteristics', parse_product)
        parse_product = self._parse_table(content, 'other', parse_product)

        return parse_product

    def _parse_table(self, soup: BeautifulSoup, table_class: str, products: dict) -> dict:
        table = soup.find('table', class_=['spec_table', table_class])
        for row in table.find_all('tr'):
            name_cell = row.find('td', class_='name')
            value_cell = row.find('td', class_='value')
            
            if name_cell and value_cell:
                name = name_cell.get_text(strip=True)
                key = self._clean_key(name)
                value = value_cell.find('dt').get_text(strip=True)
                products[key] = value
        return products

    def _clean_key(self, key):
        # Remove special characters and spaces, convert to lowercase
        key = re.sub(r'[^a-zA-Z0-9]', '_', key)
        # Remove multiple underscores
        key = re.sub(r'_+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key.lower()

    def _get_product_urls_and_numbers(self, number: str) -> str:
        """
        Get the product URL for a given part number.

        Args:
            number (str): The part number to search for

        Returns:
            str: The product URL for the given part number
        """

        self.logger.info(f"Getting product URLs for part number: {number}")
        
        response = self.post(
            endpoint="/pdc_api/en/search/list/search_result",
            data={
                "pn": number,
                "_l": "20",
                "_p": "1",
                "_c": "pure_status-pure_status",
                "_d": "0  ",
            }
        )

        if not response or 'item_type_cnt' not in response or response['item_type_cnt'] == 0:
            raise Exception(f"No product found for part number: {number}")
        
        table_data = self._scrape_table_data(response['results'])

        return table_data
    
    def _scrape_table_data(self, text):
        # Parse the HTML
        soup = BeautifulSoup(text, 'html.parser')
        
        # Find the table
        table = soup.find('table', id='table_result')
        
        # Get all headers (th elements) and their IDs
        headers = []
        for th in table.find_all('th'):
            header_id = th.get('id')
            if header_id:  # Only include headers that have an ID
                headers.append(header_id)
        
        # Initialize list to store all rows as dictionaries
        table_data = []
        
        # Process each row in the tbody
        for row in table.find('tbody').find_all('tr'):
            row_data = {}
            
            # Get all cells in the row
            cells = row.find_all('td')
            
            # Match cells with headers and create dictionary
            for header, cell in zip(headers, cells):
                # Handle special cases for cells with links
                if cell.find('a') and header == "part_no":
                    cell_text = cell.find('a').get_text(strip=True)
                    row_data['mpn'] = cell_text
                    row_data['url'] = cell.find('a')['href']
                    table_data.append(row_data)
        
        return table_data



