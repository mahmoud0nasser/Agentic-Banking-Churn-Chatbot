from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.services.llm_utils import llm

recommend_prompt = PromptTemplate(
    template="""
Based on customer data: {data}
List 3 concise recommendations to reduce churn risk in {language}.
Use bullet points and keep each recommendation short.
    """,
    input_variables=["data", "language"]
)
recommend_chain = LLMChain(llm=llm, prompt=recommend_prompt)

def recommend_actions(features: Dict[str, Any], query: str, language: str = 'en') -> str:
    return recommend_chain.invoke({"data": features, "language": language})['text']