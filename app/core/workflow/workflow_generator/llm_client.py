from litellm import completion
from typing import Optional

class LLMClient:
    def __init__(self, model: str, api_key: str, api_base: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
    
    def generate(self, messages: list[dict[str, str]], **kwargs):
        response = completion(
            model=self.model,
            messages=messages,
            api_key=self.api_key,
            base_url=self.api_base,
            **kwargs
        )
        return response

