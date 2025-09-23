import os
from dotenv import load_dotenv
import logging
import sys

load_dotenv()

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log")
        ]
    )

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    DB_PATH: str = os.path.join(BASE_DIR, "bank_churn.db")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = "gpt-4o-mini"
    OPENROUTER_BASE = "https://models.inference.ai.azure.com"
    
    # OPENROUTER_BASE = "https://openrouter.ai/api/v1"
    # MODEL_NAME = "openai/gpt-oss-120b"
    MODEL_PATH = os.path.join(BASE_DIR, "assets", "Tuned-RF-with-SMOTE.pkl")
    PREPROCESSOR_PATH = os.path.join(BASE_DIR, "assets", "preprocessor.pkl")

config = Config()
