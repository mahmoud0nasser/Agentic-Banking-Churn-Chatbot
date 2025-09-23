from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import chat
from src.db.database import init_db
from src.core.config import setup_logging

setup_logging()

app = FastAPI(title="Bank Churn Prediction Chatbot")

# Setup CORS to allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(chat.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)