import os
import sqlite3
import pandas as pd
from datetime import datetime
from src.core.config import config

def get_db_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows access to columns by name
    return conn

def init_db():
    conn = get_db_connection()
    
    # Load initial data if not present
    try:
        pd.read_sql("SELECT * FROM customers LIMIT 1", conn)
    except:
        # Get absolute path to project root
        PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        # Build path to dataset.csv
        DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'dataset.csv')
        
        # Load dataset
        df = pd.read_csv(DATA_PATH)
        df.to_sql('customers', conn, if_exists='replace', index=False)
    
    # Create predictions table if not exists
    conn.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        features TEXT,  -- JSON
        prediction INTEGER,
        probability REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create logs table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create chats table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create messages table
    conn.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        role TEXT NOT NULL,  -- 'user' or 'assistant'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# Call init_db on startup
init_db()