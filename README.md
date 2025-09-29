# Agentic Banking Churn Chatbot

## Overview
The Bank Churn Prediction Chatbot is a web-based application designed to predict customer churn for a bank using a machine learning model and provide insights through a conversational interface. Built with FastAPI for the backend, Streamlit for the frontend, and SQLite for data storage, it allows users to:
- Predict churn for specific customers using their ID or attributes.
- Get recommendations to reduce churn risk.
- Query customer data (e.g., "Show all customers from France with churn probability > 0.1").
- Maintain chat history for interactive analysis.

The system leverages a pre-trained Random Forest model with SMOTE, SHAP for explainability, and a language model (GPT-4o-mini) for natural language processing and query routing.

### System Flow Diagram

![Agentic Bank Diagram](Misc/Agentic%20Bank%20Diagram.PNG)  
*Figure 1: End-to-End Flow of the Agentic Banking Churn Chatbot*

---

## Features
- **Churn Prediction**: Predicts whether a customer will churn based on features like CreditScore, Geography, Age, etc.
- **Explanations**: Uses SHAP to provide the top 3 factors influencing churn predictions.
- **Recommendations**: Suggests actions to reduce churn risk for specific customers.
- **SQL Queries**: Supports natural language queries to fetch customer data (e.g., averages, counts).
- **Chat Interface**: Maintains chat history with a Streamlit UI, allowing users to create, view, and delete chats.
- **Multilingual Support**: Detects query language and responds in English or Arabic.
- **Token Limit Handling**: Manages large chat histories to avoid exceeding the GPT-4o-mini token limit (8,000 tokens).

## Project Structure
```
bank-churn-chatbot/
├── data/
│   └── dataset.csv           # Customer data for initializing the database
├── src/
│   ├── core/
│   │   └── config.py         # Configuration settings (database path, API keys, logging)
│   ├── db/
│   │   ├── crud.py           # CRUD operations for chats and messages
│   │   └── database.py       # Database initialization and connection
│   ├── models/
│   │   └── pydantic_models.py # Pydantic models for data validation
│   ├── routers/
│   │   └── chat.py           # FastAPI routes for chat and history management
│   ├── services/
│   │   ├── llm_utils.py      # Language model utilities (e.g., text parsing)
│   │   ├── prediction.py     # Churn prediction and SHAP explanations
│   │   ├── recommendation.py # Churn prevention recommendations
│   │   ├── router_agent.py  # Query routing and token limit handling
│   │   └── sql.py           # SQL query generation from natural language
│   │   └── assets/
│   │   │   ├── Tuned-RF-with-SMOTE.pkl  # Pre-trained Random Forest model
│   │   │   ├── preprocessor.pkl         # Preprocessor for feature transformation
│   frontend
│   │   ├── app.py            # Streamlit frontend
├── main.py                   # FastAPI backend
├── requirements.txt          # Python dependencies
└── app.log                   # Application logs
```

# Screenshots

![App Name](Misc/App%20Name.PNG)

![1st Message](Misc/1st%20Message.PNG)

![2nd Message](Misc/2nd%20Message.PNG)

![3rd Message](Misc/3rd%20Message.PNG)

![4th Message](Misc/4th%20Message.PNG)

![5th Message](Misc/5th%20Message.PNG)

![6th Message](Misc/6th%20Message.PNG)

![All Endpoint](Misc/all%20Endpoint.PNG)

## Requirements
- Python 3.8+
- Libraries listed in `requirements.txt`:
  - `fastapi`
  - `uvicorn`
  - `streamlit`
  - `langchain`
  - `langchain-openai`
  - `pandas`
  - `joblib`
  - `shap`
  - `langdetect`
  - `python-dotenv`
  - `sqlite3` (built-in)
  - `requests`

## Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd bank-churn-chatbot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**:
   - Create a `.env` file in the project root:
     ```
     OPENAI_API_KEY=your-openai-api-key
     ```
   - Replace `your-openai-api-key` with your OpenAI or OpenRouter API key.

4. **Prepare Data**:
   - Ensure `data/dataset.csv` exists with customer data (columns: CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited).
   - The database (`bank_churn.db`) will be initialized automatically on startup.

5. **Run the Backend**:
   ```bash
   python main.py
   ```
   - This starts the FastAPI server on `http://127.0.0.1:8000`.

6. **Run the Frontend**:
   ```bash
   streamlit run app.py
   ```
   - This opens the Streamlit UI in your browser (typically `http://localhost:8501`).

## Usage
1. **Access the UI**:
   - Open the Streamlit app in your browser.
   - The sidebar shows chat history with options to create a new chat or delete chats.

2. **Interact with the Chatbot**:
   - **Churn Prediction**: Enter a customer ID (e.g., "12345678") or customer details (e.g., "35-year-old male from France with a credit score of 700").
   - **Recommendations**: Ask for actions to reduce churn (e.g., "What can I do to retain this customer?").
   - **SQL Queries**: Query customer data (e.g., "Show all customers from France with churn probability greater than 0.1").
   - **History**: View past chats and continue conversations.

3. **Example Queries**:
   - "Predict churn for customer 12345678"
   - "Recommend actions for a 40-year-old female from Germany with low activity"
   - "Show average balance for exited customers"
   - "List customers from France with churn probability > 0.1"

4. **API Endpoints**:
   - `POST /api/chat`: Send a message and get a response.
   - `GET /api/chats`: List all chats.
   - `GET /api/chats/{chat_id}`: Get details of a specific chat.
   - `DELETE /api/chats/{chat_id}`: Delete a specific chat.
   - `DELETE /api/chats`: Delete all chats.

   Example curl command:
   ```bash
   curl -X POST "http://127.0.0.1:8000/api/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "Show all customers from France with churn probability greater than 0.1", "chat_id": null}'
   ```

## Database Schema
- **customers**: Stores customer data (loaded from `dataset.csv`).
- **predictions**: Stores churn predictions (customer_id, features, prediction, probability, timestamp).
- **logs**: Stores query and response logs (query, response, timestamp).
- **chats**: Stores chat sessions (id, title, created_at).
- **messages**: Stores chat messages (id, chat_id, content, role, created_at).

## Token Limit Handling
- The system handles the GPT-4o-mini token limit (8,000 tokens) by truncating chat history when necessary.
- If the input is still too large, it prompts the user to shorten the query or clear the chat history.

## Troubleshooting
- **Token Limit Error**: If you see "tokens_limit_reached," clear the chat history using the "Delete All" button in the UI or shorten your query.
- **Database Errors**: Ensure `data/dataset.csv` exists and `bank_churn.db` is writable.
- **API Key Issues**: Verify that the `OPENAI_API_KEY` in `.env` is valid.
- **Logs**: Check `app.log` for detailed error messages and token usage.

## Limitations
- The token estimation (1 token ≈ 4 characters) is approximate. For precise counting, consider adding `tiktoken`.
- Large result sets from SQL queries may slow down the UI. Consider adding pagination.
- Non-English queries are detected automatically, but responses are limited to English and Arabic.

## Future Improvements
- Add precise token counting with `tiktoken`.
- Implement pagination for large query results.
- Support more languages for responses.
- Add a summary feature for long chat histories to preserve context.

## License
This project is licensed under the MIT License.
