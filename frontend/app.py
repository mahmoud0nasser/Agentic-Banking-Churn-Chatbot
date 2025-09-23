import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import pytz
import json

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "chats" not in st.session_state:
    st.session_state.chats = []
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = "chat"

# API base URL
API_BASE = "http://127.0.0.1:8000/api"

# API functions
def fetch_chats():
    try:
        response = requests.get(f"{API_BASE}/chats", timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching chats: {e}")
        return []

def load_chat(chat_id):
    try:
        response = requests.get(f"{API_BASE}/chats/{chat_id}", timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error loading chat: {e}")
        return None

def create_new_chat():
    try:
        welcome_message = "Welcome! How can I assist you with customer churn prediction?"
        response = requests.post(
            f"{API_BASE}/chat",
            json={"message": welcome_message, "chat_id": None},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        if "chat_id" not in data:
            st.error("Failed to retrieve chat_id from server")
            return None
        return data
    except requests.RequestException as e:
        st.error(f"Error creating new chat: {e}")
        return None

def send_message(message, chat_id):
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"message": message, "chat_id": chat_id},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error sending message: {e}")
        return None

def delete_chat(chat_id):
    try:
        response = requests.delete(f"{API_BASE}/chats/{chat_id}", timeout=60)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"Error deleting chat: {e}")
        return False

def delete_all_chats():
    try:
        response = requests.delete(f"{API_BASE}/chats", timeout=60)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"Error deleting all chats: {e}")
        return False

# UI Components
def render_header():
    st.title("Customer Churn Prediction System")
    st.write("Interact with the assistant to predict churn and analyze customer data.")

def render_sidebar():
    st.sidebar.header("Chat History")
    
    col1, col2 = st.sidebar.columns([1, 1])
    with col1:
        if st.sidebar.button("➕ New Chat", key="new_chat"):
            new_chat = create_new_chat()
            if new_chat:
                st.session_state.current_chat_id = new_chat["chat_id"]
                st.session_state.chat_history = [{"role": "assistant", "content": new_chat["response"]}]
                st.session_state.chats = fetch_chats()
                st.rerun()
    with col2:
        if st.sidebar.button("🗑 Delete All", key="delete_all_chats"):
            if delete_all_chats():
                st.session_state.chats = []
                st.session_state.current_chat_id = None
                st.session_state.chat_history = []
                st.rerun()

    for chat in st.session_state.chats:
        created_at = datetime.fromisoformat(chat["created_at"].replace("Z", "+00:00")).astimezone(pytz.timezone("Asia/Riyadh"))
        label = f"{chat['title']} ({created_at.strftime('%Y-%m-%d %I:%M %p')})"
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(label, key=f"chat_{chat['id']}"):
                st.session_state.current_chat_id = chat["id"]
                chat_data = load_chat(chat["id"])
                if chat_data:
                    st.session_state.chat_history = chat_data.get("messages", [])
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{chat['id']}"):
                if delete_chat(chat["id"]):
                    st.session_state.chats = fetch_chats()
                    if st.session_state.current_chat_id == chat['id']:
                        st.session_state.current_chat_id = None
                        st.session_state.chat_history = []
                    st.rerun()

def render_chat():
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and message["content"].startswith("|"):
                try:
                    # Try parsing as Markdown table
                    lines = message["content"].strip().split("\n")
                    if len(lines) >= 2:  # Header and separator
                        headers = [h.strip() for h in lines[0].strip("|").split("|")]
                        data = [[c.strip() for c in row.strip("|").split("|")] for row in lines[2:]]
                        df = pd.DataFrame(data, columns=headers)
                        st.dataframe(df)
                    else:
                        st.write(message["content"])
                except:
                    st.write(message["content"])
            else:
                st.write(message["content"])

    prompt = st.chat_input("Type your message here...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.spinner("Processing..."):
            chat_id = st.session_state.current_chat_id if st.session_state.current_chat_id else None
            response = send_message(prompt, chat_id)
            if response:
                st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
                st.session_state.current_chat_id = response["chat_id"]
                st.session_state.chats = fetch_chats()
                st.rerun()

# Initialize chats on first load
if not st.session_state.chats:
    st.session_state.chats = fetch_chats()
    if st.session_state.chats:
        st.session_state.current_chat_id = st.session_state.chats[0]["id"]
        chat = load_chat(st.session_state.current_chat_id)
        if chat:
            st.session_state.chat_history = chat.get("messages", [])
    else:
        new_chat = create_new_chat()
        if new_chat:
            st.session_state.current_chat_id = new_chat["chat_id"]
            st.session_state.chat_history = [{"role": "assistant", "content": new_chat["response"]}]
            st.session_state.chats = fetch_chats()

# Main Layout
render_header()
render_sidebar()
render_chat()