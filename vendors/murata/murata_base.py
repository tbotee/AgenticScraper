class Murata():

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
