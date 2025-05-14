from utils.cache_helper import cache_json_result
from utils.llm_helper import LLMHelper
from utils.xref_base import XrefBase
from vendors.murata.murata_base import Murata
import json


class MurataXrefSearch(XrefBase, Murata):
    @property
    def base_url(self):
        return "https://www.murata.com/webapi/"
    
    def __init__(self):
        self.llm_helper = LLMHelper()
        super().__init__()

    def search_by_cross_reference(self, competitor_mpn, category_path=None):
        """
        Search for vendor equivalents to a competitor's part number.

        Args:
            competitor_mpn (str): The competitor's part number
            category_path (list, optional): List of category names

        Returns:
            list: List of dictionaries with product information

        Runs with the command:
            python main.py xref 337XMPL002MG28A --category-path '["Capacitors", "Polymer Aluminium Electrolytic Capacitors"]' 
                --output results_xref.json --api-key
        """
        self.logger.info(f"Searching for cross-reference to competitor MPN {competitor_mpn}: {category_path}")

        try:
            xrefcategory_id = self._get_xref_category(category_path)
            return self._fetch_product_details(xrefcategory_id, competitor_mpn)
        except Exception as e:
            self.logger.error(str(e))
            return []
        

    def _fetch_product_details(self, xrefcategory_id, competitor_mpn) -> list:
        arguments = {
            'cate': xrefcategory_id,
            'partno': competitor_mpn,
            'lang': 'en-us'
        }
        result = self.get('SearchCrossReference', arguments)

        if 'murataPsDispRest' in result:
            all_product_details = self.format_product_details(result['murataPsDispRest'])
            if all_product_details:
                return all_product_details
        
        raise Exception(f"No product details found for competitor MPN {competitor_mpn}")    

    def _get_xref_category(self, category_path) -> str:
        """
        Get the cross-reference category from the category tree.

        Args:
            category_path (list): List of category names

        Returns:
            string: xrefcategory_id
        """
        self.logger.info(f"Getting cross-reference category from category tree: {category_path}")
        categories = self.get_product_categories_from_the_category_tree()


        xrefcategory = self._get_xrefcategory_id_from_llm_according_to_the_parameter(categories, category_path)

        if (xrefcategory == "None"):
            raise Exception(f"No cross-reference category id found for {category_path}")

        self.logger.info(f"Cross-reference category id: {xrefcategory}")

        return xrefcategory

    @cache_json_result(cache_dir="llm_cache")
    def _get_xrefcategory_id_from_llm_according_to_the_parameter(self, categories, category_path) -> str:
        """
        Get the xref category id for the given category name.

        Args:
            categories (list): List of category dictionaries
            category_path (list): List of category names

        Returns:
            string: xrefcategory_id
        """

        prompt = f"""

            I need to determine the most likely product xrefcategory_id	for the following category path: {json.dumps(category_path, indent=2)}

            The category information is in the following format:
            {{
                'category_id': '123',
                "name": "Category Name",
                "xrefcategory_id": "123",
                "children": [
                    {{
                        "category_id": "456", 
                        "name": "Subcategory Name".
                        "children": ...
                    }}
                ]
            }}

            Here are the categories:
            {json.dumps(categories, indent=2)}
            
            Return your answer as a JSON. If no match is found, return {{"xrefcategory_id", "None"}}.
            For example: {{"xrefcategory_id", "dgs1288sKXZK"]}}
            """

        result = self.llm_helper.genericQuestion(prompt)
        if result:
            try:
                result = json.loads(result)
                return result["xrefcategory_id"]
            except:
                self.logger.error(f"Failed to parse category ID from LLM response: {result}")
                return None
        return None