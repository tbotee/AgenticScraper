
import os
from utils.base_api_client import BaseAPIClient
from utils.cache_helper import cache_json_result
from utils.llm_helper import LLMHelper
import json
from vendors.murata.murata_base import Murata

class MurataParametricSearch(Murata):
    @property
    def base_url(self):
        return "https://www.murata.com/webapi/"

    def __init__(self):
        """
        Initialize the search engine with a WebDriver instance.
        """
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
        
        categories = self.get_product_categories_from_the_category_tree()

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

            # check for parameters is string or json
            if 'details' in parameters:
                # python main.py parametric --category "Capacitors" --subcategory 
                # "Ceramic Capacitors(SMD)" --parameters '{"details": "the dc rated voltage should be in the range of 100-200 and the capacitance no more than 10"}' 
                # --max-results 10 --output results_parametric.json --api-key


                filter_parameters = self.get_filter_parameters(result['Result']['header'])
                filters_by_llm = self._generate_filter_by_llm(filter_parameters, parameters['details'])
                if filters_by_llm:
                    for filter in filters_by_llm['filters']:
                        if isinstance(filter, dict) and ('min' in filter or 'max' in filter): 
                            f = f"{filter['filter_id']};{filter.get('min', '')}|{filter.get('max', '')}"
                            filters.append(f)

                        if isinstance(filter, dict) and 'value' in filter : 
                            possile_selectable_values = self._get_possible_selectable_values(filter['filter_id'], result['Result']['listdata'])
                            most_likely_value = self._get_most_likely_value(possile_selectable_values, filter['filter_id'])
                            if most_likely_value != "None":
                                filters.append(f"{filter['filter_id']};{most_likely_value}")
                self.logger.info(f"Filters from the llm: {filters}")
            else:
                param_names = list(parameters.keys())
                filter_ids = self._get_filter_ids(result['Result']['header'], param_names)
                
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
    def _generate_filter_by_llm(self, filter_parameters, details):
        """
        Generate the filter for the given parameters and category id.
        """
        prompt = f"""
            Here are the possible filter ids: {json.dumps(filter_parameters, indent=2)}. Each filter id has a label.
            Generate as many filters as the following prompt: '{details}'. Note that there are multiple filters.

            If you detect that one of the filters is a range filter (legth and width are not range filters: 0.1x0.25 is a single value filter), add these format to the result list:
            [
                {{
                    "filter_id": "filter_id",
                    "min": "filter_min",
                    "max": "filter_max",
                }},
                ...
            ]

            If you detect that one of the filterst is a range but only one value is provided (like the maximum or minimum value) leave the other empty and add the following format to the result list:
            [
                {{
                    "filter_id": "filter_id",
                    "min": "filter_min" or "",
                    "max": "filter_max" or "",
                }},
                ...
            ]

            If you detect that it is a single value add these format to the result list:
            [
                {{
                    "filter_id": "filter_id",
                    "value": "filter_value",
                }},
                ...
            ]

            So the final result shoudl be: 
            {{
                "filters": [
                    .... put all the filters here
                ]
            }}

            Return your answer as a JSON list with all the filter options.
         """

        result = self.llm_helper.genericQuestion(prompt)
        if result:
            try:
                filter_value = json.loads(result)
                return filter_value
            except:
                self.logger.error(f"Failed to parse result: {result}")

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

        filter_labels_list = self.get_filter_parameters(filter_labels)

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
