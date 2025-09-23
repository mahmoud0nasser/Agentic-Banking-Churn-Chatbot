import re
import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.core.config import config

llm = ChatOpenAI(
    model=config.MODEL_NAME,
    openai_api_key=config.OPENAI_API_KEY,
    base_url=config.OPENROUTER_BASE,
    temperature=0.0
)

def generate_extraction_prompt(text: str) -> str:
    return f"""
Extract the following fields from the text and provide them in JSON format: 
CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary.

Rules:
- All values must be in English and numeric where applicable.
- For boolean fields, use true/false.
- Detect the language of the input and extract accordingly, but output JSON in English keys.

Text: "{text}"
JSON:
"""

def parse_text_to_json(text: str) -> Dict[str, Any]:
    prompt = generate_extraction_prompt(text)
    response = llm.invoke(prompt).content
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            data['HasCrCard'] = bool(data.get('HasCrCard', False))
            data['IsActiveMember'] = bool(data.get('IsActiveMember', False))
            return data
        except:
            pass
    return None