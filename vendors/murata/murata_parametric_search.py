
import os
from utils.base_api_client import BaseAPIClient
from utils.cache_helper import cache_json_result
from utils.llm_helper import LLMHelper
import json
from vendors.murata.murata_base import Murata

class MurataParametricSearch(BaseAPIClient, Murata):
    @property
    def base_url(self):
        return "https://www.murata.com/webapi/"

    def __init__(self, driver):
        """
        Initialize the search engine with a WebDriver instance.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.llm_helper = LLMHelper()
        super().__init__()
    

    def search_by_parameters(self, category, subcategory=None, parameters=None, max_results=10) -> list:
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

        self.logger.info(f"Searching for products in category: {category}, "
                        f"subcategory: {subcategory} with parameters: {parameters}")
        
        categories = self._get_product_categories_from_the_category_tree()

        category_id = self._get_category_id_from_llm_according_to_the_parameter(categories, category, subcategory)

        if category_id == "None":
            self.logger.warning(f"No category id found for {category} and {subcategory}")
            return []
        
        arguments = {
            'cate': category_id,
            'stype': 2,
            'lang': 'en-us'
        }

        if parameters:
            filters = self._determine_filters(parameters, category_id)
            if isinstance(filters, list) and filters:
                arguments['scon'] = filters

        result = self.get('PsdispRest', arguments)

        all_product_details = self.format_product_details(result, max_results)

        if not all_product_details:
            self.logger.error(f"No product details found for {category} and {subcategory}")
            return []

        return all_product_details

    @cache_json_result(cache_dir="llm_cache")
    def _get_category_id_from_llm_according_to_the_parameter(self, categories, category, subcategory=None):
        """
        Get the category id for the given category name.

        Args:
            categories (list): List of category dictionaries
            category (str): Category name
            subcategory (str, optional): Subcategory name

        Returns:
            str: Category id
        """

        self.logger.info(f"Getting category id for {category} and {subcategory}")
        if not subcategory: 
            prompt = f"""
                I need to determine the most likely product category id which is named category_id for the following category: {category}
            """
        else:
            prompt = f"""
                I need to determine the most likely product category id which is named category_id for the following category: {category}
                and subcategory: {subcategory}
            """

        prompt += f"""
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
            
            Return your answer as a JSON. If no match is found, return {{"category_id", "None"]}}.
            For example: {{"category_id", "dgs1288sKXZ`K"]}}
            """
        

        result = self.llm_helper.genericQuestion(prompt)
        if result:
            try:
                result = json.loads(result)
                self.logger.info(f"Llmm category id result: {result['category_id']}")

                return result["category_id"]
            except:
                self.logger.error(f"Failed to parse category ID from LLM response: {result}")
                return None
        return None
    
    
    def _determine_filters(self, parameters, category_id):
        """
        Determine the filters for the given parameters and category id.

        Args:
            parameters (dict): The parameters to filter by 
                Format: {
                    'Capacitance': {'min': 1, 'max': 1.1}, 
                    'Capacitance 3 DigitCode': {'min': 1, 'max': 2}
                }
            category_id (str): The category id

        Returns:
        """
        
        result = self.get('GetSearchCondition', {
            'cate': category_id,
            'lang': 'en-us',
            'stype': 2
        })

        filters = []

        if result and 'Result' in result:
            param_names = list(parameters.keys())
            filter_ids = self._get_filter_ids(result['Result']['header'], param_names)
            # Loop through the filter IDs from the cache
            
            for filter_info in filter_ids['filters']:
                filter_id = filter_info["filter_id"]
                filter_label = filter_info["filter_label"]

                if filter_label in parameters:
                    param_value = parameters[filter_label]
                    if isinstance(param_value, dict) and 'min' in param_value and 'max' in param_value:
                        filters.append(f"{filter_id};{param_value['min']}|{param_value['max']}")
                    else:
                        possile_selectable_values = self._get_possible_selectable_values(filter_id, result['Result']['listdata'])
                        if possile_selectable_values:    
                            most_likely_value = self._get_most_likely_value(possile_selectable_values, param_value)
                            if most_likely_value != "None":
                                filters.append(f"{filter_id};{most_likely_value}")
                        
                        
            self.logger.info(f"Formatted filters from the arguments: {filters}")
        
        return filters


    @cache_json_result(cache_dir="llm_cache")
    def _get_most_likely_value(self, possile_selectable_values, value_to_filter):

        prompt = f"""
            Get the most likely filter value  for "{value_to_filter}" from following list: {json.dumps(possile_selectable_values, indent=2)} 
            
            Return your answer as a JSON. The return format is the following json format.
            {{ "filter_value": "filter_value" }}
            If no match is found, return {{ "filter_value": "None" }}
        """

        result = self.llm_helper.genericQuestion(prompt)
        if result:
            try:
                filter_value = json.loads(result)
                return filter_value['filter_value']
            except:
                self.logger.error(f"Failed to parse result: {result}")

    def _get_possible_selectable_values(self, filter_id, listdata):
        """
        Get the possible selectable values for the given filter id.
        """
        if filter_id in listdata:
            items = listdata[filter_id]
            return [item.split(":")[1] for item in items]
        return []
    
    @cache_json_result(cache_dir="llm_cache")
    def _get_product_categories_from_the_category_tree(self):
        """
        Get the product categories from the Murata navigation API.
        
        Returns:
            list: List of product category dictionaries
        """
        try:
            self.logger.info(f"Getting product categories")
            nav_data = self.get('GetCategoryRest', {
                'lang': 'en-us'
            })
            
            if not nav_data or 'categories' not in nav_data:
                self.logger.error("Invalid navigation data response")
                return []
            
            def simplify_category(category):
                simplified = {
                    "name": category['name'],
                    "category_id": category['category_id'],
                    "children": []
                }
                
                if 'children' in category:
                    simplified['children'] = [
                        simplify_category(child) 
                        for child in category['children']
                    ]
                    
                return simplified
            
            nav_data['categories'] = [
                simplify_category(category)
                for category in nav_data['categories']
            ]
                
            return nav_data['categories']
            
            
        except Exception as e:
            self.logger.error(f"Error getting product categories: {e}")
            return []
        1

    @cache_json_result(cache_dir="llm_cache")
    def _get_filter_ids(self, filter_labels, param_names) -> dict:
        """
        Get the filter ids for the given parameters.
        Args:
            categoryId (str): The category id
            filter_labels (list): The filter labels

        Returns:
            dict: The filter ids and labels
        """

        self.logger.info(f"Getting filter ids for {param_names}")

        filter_labels_list = []
        for header in filter_labels:
            # Split by colon and take first two parts
            parts = header.split(':')
            if len(parts) >= 2:
                filter_labels_list.append({
                    'filter_id': parts[0],
                    'filter_label': parts[1]
                })

        prompt = f"""
            Get the most likely filter_id for the following filter labels: {json.dumps(param_names, indent=2)} from the following result list:
            {json.dumps(filter_labels_list, indent=2)}
            
            Return your answer as a JSON. The return format is the following json list:
            {{ "filters": [
                    {{
                        "filter_id": "filter_id",
                        "filter_label": "Filter Label Name"
                    }},
                    ...
                ]
            }}
        """
        
        result = self.llm_helper.genericQuestion(prompt)

        if result:
            try:
                return json.loads(result)
            except:
                self.logger.error(f"Failed to parse result: {result}")
        
        return []
