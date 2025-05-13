from utils.base_api_client import BaseAPIClient
from utils.cache_helper import cache_json_result


class Murata(BaseAPIClient):

    def format_product_details(self, result, max_results=None):
        if not result or 'Result' not in result or 'header' not in result['Result'] or 'data' not in result['Result']:
            return None

        headers = [h.split(':')[0] for h in result['Result']['header']]
        products = result['Result']['data']['products']

        all_product_details = []
        
        for product in products:
            values = product['Value']
            product_details = {}
            for header, value in zip(headers, values):
                key = header.split(':')[0]
                product_details[key] = value

            formatted_result = {
                "mpn": product_details.get("partnumber", ""),
                "url": f"https://www.murata.com/en-us/products/productdetail?partno={product_details.get('partnumber', '')}",
                "details": product_details
            }
            all_product_details.append(formatted_result)
            
            if max_results and len(all_product_details) >= max_results:
                break

        return all_product_details


    @cache_json_result(cache_dir="llm_cache")
    def get_product_categories_from_the_category_tree(self):
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
                    "xrefcategory_id": category['xrefcategory_id'],
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
        

