import requests
import xmltodict
import json
from pathlib import Path

def fetch_tdk_sitemap():
    """Fetch TDK sitemap XML and convert it to JSON."""
    url = "https://product.tdk.com/product_top_page/sitemap.xml"
    
    try:
        # Fetch the XML content
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse XML to dictionary
        xml_dict = xmltodict.parse(response.content)
        
        # Convert to JSON string with pretty printing
        json_str = json.dumps(xml_dict, indent=2)
        
        # Save to file
        output_path = Path(__file__).parent / "tdk_sitemap.json"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
            
        print(f"Sitemap successfully saved to: {output_path}")
        return xml_dict
        
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return None
    except Exception as e:
        print(f"Error processing sitemap: {e}")
        return None

if __name__ == "__main__":
    fetch_tdk_sitemap() 