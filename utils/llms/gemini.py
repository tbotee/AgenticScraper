import os
from google import genai
import json
from typing import Type, TypeVar, List, Any, Dict
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class Gemini:
    def __init__(self):

        self.client = genai.Client(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_llm_json(self, prompt: str, response_type: Type[T]) -> list[T]:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20", 
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[response_type]
            }
        )
        try:
            return response.parsed
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON. Error: {e}")
            print(f"Response text: {response.text}")
            return None