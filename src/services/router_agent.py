import re
from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.services.llm_utils import llm, parse_text_to_json
from src.services.prediction import predict_and_explain
from src.services.recommendation import recommend_actions
from src.services.sql import execute_sql_query, sql_chain  # Import sql_chain
from src.db.database import get_db_connection
from pandas import read_sql
import asyncio
import logging
from langdetect import detect
import pandas as pd
import numpy as np
from src.core.config import config
import joblib

logger = logging.getLogger(__name__)

model = joblib.load(config.MODEL_PATH)
preprocessor = joblib.load(config.PREPROCESSOR_PATH)

# Token estimation function (approximate: 1 token ≈ 4 characters)
def estimate_tokens(text: str) -> int:
    return len(text) // 4 + 1

# Maximum token limit for gpt-4o-mini
MAX_TOKENS = 8000
# Reserve some tokens for the prompt and response
RESERVED_TOKENS = 1000
MAX_HISTORY_TOKENS = MAX_TOKENS - RESERVED_TOKENS

def get_features_from_query(query: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    if re.search(r'\d{8}', query):
        customer_id = re.search(r'\d{8}', query).group(0)
        conn = get_db_connection()
        try:
            customer_df = read_sql("SELECT * FROM customers WHERE CustomerId = ?", conn, params=(customer_id,))
            if customer_df.empty:
                return None
            return customer_df.iloc[0].to_dict()
        finally:
            conn.close()
    else:
        features = parse_text_to_json(query)
        if features:
            return features
    
    if 'this customer' in query.lower() or 'the customer' in query.lower():
        for msg in reversed(history):
            if msg['role'] == 'user' and (re.search(r'\d{8}', msg['content']) or 'year-old' in msg['content']):
                return get_features_from_query(msg['content'], [])
    
    return None

def detect_language(query: str) -> str:
    try:
        return detect(query)
    except:
        return 'en'  # Default to English

router_prompt = PromptTemplate(
    template="""
Previous conversation:
{history}

Current query: {query}

Classify the query and choose ONE tool:
- prediction_tool: For predicting churn or explaining a prediction (keywords: predict, churn, explain, why).
- recommendation_tool: For recommendations or actions to retain customers (keywords: recommend, actions, suggestions).
- sql_tool: For database queries, aggregates, averages, counts, or lists (keywords: average, count, show all, list, how many).
- probability_filter_tool: For queries filtering customers by churn probability (keywords: churn probability, probability greater than, probability above).

Respond ONLY with the tool name: prediction_tool, recommendation_tool, sql_tool, probability_filter_tool.
    """,
    input_variables=["history", "query"]
)
router_chain = LLMChain(llm=llm, prompt=router_prompt)

def extract_probability_threshold(query: str) -> float:
    match = re.search(r'probability\s*(?:greater than|above)\s*([\d.]+)', query, re.IGNORECASE)
    return float(match.group(1)) if match else 0.5

def extract_sql_conditions(query: str) -> str:
    conditions = re.split(r'with\s*churn\s*probability', query, flags=re.IGNORECASE)[0].strip()
    return conditions

async def probability_filter_query(query: str, language: str = 'en') -> str:
    try:
        conn = get_db_connection()
        try:
            # Extract conditions and threshold
            conditions = extract_sql_conditions(query)
            threshold = extract_probability_threshold(query)
            
            # Generate SQL query for conditions
            sql_query = await sql_chain.ainvoke({"query": conditions})
            sql_query = sql_query['text'].strip()
            
            # Fetch matching customers
            df = pd.read_sql(sql_query, conn)
            if df.empty:
                return "No customers found matching the criteria." if language == 'en' else "لم يتم العثور على عملاء مطابقين للمعايير."
            
            # Compute churn probabilities
            features = df[['CreditScore', 'Geography', 'Gender', 'Age', 'Tenure', 'Balance', 
                          'NumOfProducts', 'HasCrCard', 'IsActiveMember', 'EstimatedSalary']]
            processed = preprocessor.transform(features)
            probs = model.predict_proba(processed)[:, 1]
            
            # Filter by probability
            df['ChurnProbability'] = probs
            filtered_df = df[df['ChurnProbability'] > threshold]
            
            if filtered_df.empty:
                return "No customers found with churn probability above the threshold." if language == 'en' else "لم يتم العثور على عملاء باحتمالية التسرب فوق الحد."
            
            return filtered_df.to_markdown(index=False)
        finally:
            conn.close()
    except Exception as e:
        return f"Error: {str(e)}" if language == 'en' else f"خطأ: {str(e)}"

async def route_query(query: str, history: List[Dict[str, str]]) -> str:
    language = detect_language(query)  # Define language early
    try:
        # Truncate history to fit within token limit
        total_tokens = estimate_tokens(query)
        truncated_history = []
        history_tokens = 0
        
        # Add messages from history (most recent first) until token limit is reached
        for msg in reversed(history[-4:]):  # Limit to last 4 messages initially
            msg_text = f"{msg['role']}: {msg['content']}"
            msg_tokens = estimate_tokens(msg_text)
            if history_tokens + msg_tokens + total_tokens <= MAX_HISTORY_TOKENS:
                truncated_history.insert(0, msg)  # Insert at beginning to maintain order
                history_tokens += msg_tokens
            else:
                logger.info(f"Truncating history: message '{msg_text[:30]}...' exceeds token limit")
                break
        
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in truncated_history])
        total_tokens += history_tokens
        
        # Log token usage
        logger.info(f"Estimated tokens: query={estimate_tokens(query)}, history={history_tokens}, total={total_tokens}")
        
        # Check if total tokens still exceed limit
        if total_tokens > MAX_TOKENS:
            return (
                "Error: Input too large, even after truncating history. Please shorten your query or clear chat history."
                if language == 'en' else
                "خطأ: الإدخال كبير جدًا، حتى بعد تقليص السجل. يرجى تقصير الطلب أو مسح سجل الدردشة."
            )
        
        response = await router_chain.ainvoke({"history": history_str, "query": query})
        tool_name = response['text'].strip().lower()
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            if "prediction" in tool_name:
                features = get_features_from_query(query, truncated_history)
                if not features:
                    return "Customer data not found or invalid." if language == 'en' else "بيانات العميل غير موجودة أو غير صالحة."
                customer_id = features.get('CustomerId')
                result = await asyncio.to_thread(predict_and_explain, features, query, customer_id, language)
            elif "recommendation" in tool_name:
                features = get_features_from_query(query, truncated_history)
                if not features:
                    return "Customer data not found or invalid." if language == 'en' else "بيانات العميل غير موجودة أو غير صالحة."
                result = await asyncio.to_thread(recommend_actions, features, query, language)
            elif "sql" in tool_name:
                result = await execute_sql_query(query, language)
            elif "probability_filter" in tool_name:
                result = await probability_filter_query(query, language)
            else:
                return "Invalid query type." if language == 'en' else "نوع الطلب غير صالح."
            
            cursor.execute("INSERT INTO logs (query, response) VALUES (?, ?)", (query, str(result)))
            conn.commit()
            return result
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error in route_query: {str(e)}")
        return f"Error: {str(e)}" if language == 'en' else f"خطأ: {str(e)}"