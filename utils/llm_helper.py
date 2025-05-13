import os
import json
import requests
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

class LLMHelper:
    """Helper class for LLM-based decision making."""
    
    def __init__(self, api_key=None):
        """
        Initialize the LLM helper.
        
        Args:
            api_key (str, optional): API key for the LLM service. If not provided,
                                    will try to get from environment variable.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: No API key provided for LLM. Some features may not work.")

        self.logger = get_logger(self.__class__.__name__)
    
    def determine_category_path(self, mpn: str, available_categories: List[str]) -> List[str]:
        """
        Use LLM to determine the likely category path for a part number.
        
        Args:
            mpn (str): The manufacturer part number
            available_categories (list): List of available top-level categories
            
        Returns:
            list: List of category names to navigate
        """
        if not self.api_key:
            # Basic heuristic if no API key
            if any(x in mpn.upper() for x in ["CAP", "GRM", "CL", "C0G", "X7R"]):
                return ["Capacitors", "Ceramic Capacitors"]
            elif any(x in mpn.upper() for x in ["RES", "RC", "RL"]):
                return ["Resistors", "Chip Resistors"]
            elif any(x in mpn.upper() for x in ["IND", "LQG", "LQW"]):
                return ["Inductors", "Chip Inductors"]
            else:
                return ["Capacitors"]
        
        try:
            # Prepare the prompt for the LLM
            prompt = f"""
            I need to determine the most likely product category path for an electronic component with part number "{mpn}".
            
            Available top-level categories:
            {json.dumps(available_categories, indent=2)}
            
            Based on the part number "{mpn}", determine:
            1. Which top-level category is most appropriate
            2. What subcategories might be relevant (e.g., for capacitors: ceramic, aluminum, polymer, etc.)
            
            Return your answer as a JSON array of category names, starting with the top-level category.
            For example: ["Capacitors", "Polymer Aluminium Electrolytic Capacitors"]
            
            Only return the JSON array, no other text.
            """
            
            # Call the LLM API - using OpenAI API format, adjust as needed
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "gpt-3.5-turbo",  # or your preferred model
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"}
                }
            )
            
            # Parse the response
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"].strip()
                
                try:
                    # Parse the JSON response
                    category_path = json.loads(answer)
                    if isinstance(category_path, dict) and "categories" in category_path:
                        return category_path["categories"]
                    elif isinstance(category_path, list):
                        return category_path
                    else:
                        print(f"Unexpected LLM response format: {answer}")
                        return self._fallback_category_path(mpn)
                except json.JSONDecodeError:
                    print(f"Failed to parse LLM response as JSON: {answer}")
                    return self._fallback_category_path(mpn)
            
            return self._fallback_category_path(mpn)
            
        except Exception as e:
            print(f"Error in LLM category determination: {e}")
            return self._fallback_category_path(mpn)
    
    def identify_parameter_section(self, 
                                  param_name: str, 
                                  section_texts: List[str]) -> Optional[int]:
        """
        Use LLM to identify the correct parameter section based on section texts.
        
        Args:
            param_name (str): The parameter name we're looking for
            section_texts (List[str]): List of text content from each section
            
        Returns:
            Optional[int]: Index of the identified section, or None if no match found
        """
        if not self.api_key or not section_texts:
            return None
            
        try:
            # Prepare the prompt for the LLM
            prompt = f"""
            I need to identify which section contains the parameter "{param_name}" from the following list of sections.
            Each section is from a parametric search interface for electronic components.
            
            Sections:
            {json.dumps([f"Section {i+1}: {text[:200]}..." for i, text in enumerate(section_texts)], indent=2)}
            
            Return only the section number (e.g., "1" for Section 1) that most likely contains the "{param_name}" parameter.
            If none of the sections match, return "None".
            """
            
            # Call the LLM API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": "gpt-3.5-turbo",  # or your preferred model
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            
            # Parse the response
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"].strip()
                
                # Extract the section number
                if answer.isdigit():
                    section_index = int(answer) - 1  # Convert to 0-based index
                    if 0 <= section_index < len(section_texts):
                        return section_index
                elif "none" in answer.lower():
                    return None
                    
            return None
            
        except Exception as e:
            print(f"Error in LLM parameter identification: {e}")
            return None
    
    def genericQuestion(self, prompt: str) -> str:
        """
        Use LLM to generate a response based on the provided prompt.

        Args:
            prompt (str): The question to generate a response for

        Returns:
            str: The generated answer
        """
        if not self.api_key:
            return None

                
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            json={
                "model": "gpt-3.5-turbo",  # or your preferred model
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            self.logger.error(f"Error in LLM API call: {response.text}")
            self.logger.error(f"Error in LLM response: {response.status_code}")
            return None
            

    def _fallback_category_path(self, mpn: str) -> List[str]:
        """
        Provide a fallback category path based on simple heuristics.
        
        Args:
            mpn (str): The manufacturer part number
            
        Returns:
            list: List of category names
        """
        # Simple heuristic based on part number patterns
        if any(x in mpn.upper() for x in ["CAP", "GRM", "CL", "C0G", "X7R"]):
            return ["Capacitors", "Ceramic Capacitors"]
        elif any(x in mpn.upper() for x in ["RES", "RC", "RL"]):
            return ["Resistors", "Chip Resistors"]
        elif any(x in mpn.upper() for x in ["IND", "LQG", "LQW"]):
            return ["Inductors", "Chip Inductors"]
        else:
            # Default to capacitors if unsure
            return ["Capacitors"]