from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.services.llm_utils import llm
from src.core.config import config
from src.db.database import get_db_connection
import pandas as pd
import sqlite3

sql_prompt = PromptTemplate(
    template="""
You are a SQL expert. Convert the following natural language query to a valid SQLite query for a table named 'customers' with columns: CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited.

Query: {query}

Rules:
- Return only the SQL query as plain text.
- Do not include explanations or markdown.
- Ensure the query is safe and valid for SQLite.
- If the query is ambiguous, make reasonable assumptions (e.g., 'high balance' means Balance > 100000, 'low activity' means IsActiveMember = 0).

Examples:
- "Show customers with high balance but low activity" -> SELECT CustomerId, Surname, Balance FROM customers WHERE Balance > 100000 AND IsActiveMember = 0
- "Average age of exited customers" -> SELECT AVG(Age) FROM customers WHERE Exited = 1
    """,
    input_variables=["query"]
)
sql_chain = LLMChain(llm=llm, prompt=sql_prompt)

async def execute_sql_query(query: str, language: str = 'en') -> str:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate SQL query
        sql_query = await sql_chain.ainvoke({"query": query})
        sql_query = sql_query['text'].strip()
        
        # Execute query
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Format results
        if not results:
            return "No results found." if language == 'en' else "لا توجد نتائج."
        
        df = pd.DataFrame(results, columns=columns)
        try:
            return df.to_markdown(index=False)
        except ImportError:
            # Fallback if tabulate is not installed
            return df.to_string(index=False)
    except sqlite3.Error as e:
        return f"SQL Error: {str(e)}" if language == 'en' else f"خطأ SQL: {str(e)}"
    finally:
        conn.close()