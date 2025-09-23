from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class CustomerData(BaseModel):
    CreditScore: float = Field(..., ge=300, le=850, description='Credit score of the customer (300-850)')
    Geography: str = Field(..., description='Geography', pattern=r'^(France|Germany|Spain)$')
    Gender: str = Field(..., description='Gender', pattern=r'^(Male|Female)$')
    Age: int = Field(..., ge=18, le=100, description='Age of the customer (18-100)')
    Tenure: int = Field(..., ge=0, le=10, description='Number of years with the bank (0-10)')
    Balance: float = Field(..., ge=0, description='Account balance')
    NumOfProducts: int = Field(..., ge=1, le=4, description='Number of products (1-4)')
    HasCrCard: bool = Field(..., description='Does the customer have a credit card')
    IsActiveMember: bool = Field(..., description='Is the customer an active member')
    EstimatedSalary: float = Field(..., ge=0, description='Estimated salary')

class ChatQuery(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []  # [{"role": "user", "content": "..."}, ...]

class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    chat_id: int

class Chat(BaseModel):
    id: int
    title: str
    created_at: datetime

class Message(BaseModel):
    id: int
    chat_id: int
    content: str
    role: str
    created_at: datetime

class ChatWithMessages(Chat):
    messages: List[Message] = []