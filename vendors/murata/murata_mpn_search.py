from utils.mpn_base import MPNBase
from vendors.murata.murata_base import Murata


class MurataMPNSearch(MPNBase, Murata):
    @property
    def base_url(self):
        return "https://www.murata.com/webapi/"

    def get_products_by_number(self, number: str) -> list:
        """
        Get a list of product information by number. Murata uses category to get product information. 
        First get the category and then get the products.

        Returns: 
            list: A list of dictionaries with product information  
        """
        try:
            self.logger.info(f"Getting products information for part number: {number}")
            category_id = self._get_product_category_by_id(number)
            results  = self._get_products_details(category_id, number)
            return results
        except Exception as e:
            self.logger.error(str(e))
            return None

    def _get_product_category_by_id(self, number: str) -> str:
        """
        Get the product category by ID
        Args:
            number (str): The part number to search for
        
        Returns:
            str: The category ID for the given part number
        """

        self.logger.info(f"Fetching category for part number: {number}")
        result = self.get('SelectCategory', {
            'partno': number,
            'stype': 2,
            'lang': 'en-us'
        })
        
        if result and 'cateid' in result and result['cateid'] and len(result['cateid']) > 0:
            self.logger.info(f"Category id found successfully: {result['cateid'][0]}")
            return result['cateid'][0]
        else:
            self.logger.error(f"No category ID found for the given part number: {number}")
            raise Exception("No category ID found for the given part number")

    def _get_products_details(self, category_id: str, number: str) -> list:
        """
        Get products with details by category ID and part number

        Args:
            category_id (str): The category ID to search for
            number (str): The part number to search for
        
        Returns: 
            list: A list of dictionaries with product information
        """
        self.logger.info(f"Fetching product details for part number: {number} in category: {category_id}")
        
        result = self.get('PsdispRest', {
            'cate': category_id,
            'partno': number,
            'lang': 'en-us',
            'stype': 2
        })

        all_product_details = self.format_product_details(result)

        if not all_product_details:
            raise Exception(f"No product details found for part number: {number}")

        self.logger.info(f"Successfully retrieved details for {len(all_product_details)} products with part number: {number}")
        
        return all_product_details