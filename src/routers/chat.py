from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.models.pydantic_models import ChatRequest, ChatResponse
from src.services.router_agent import route_query
from src.db import crud
from src.db.database import get_db_connection
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    try:
        logger.info(f"Received chat request: {chat_request}")
        
        # Create new chat if no chat_id provided or chat_id is 0
        if not chat_request.chat_id or chat_request.chat_id == 0:
            title = chat_request.message[:30] + "..." if len(chat_request.message) > 30 else chat_request.message
            chat_id = crud.create_chat(title)
        else:
            chat_id = chat_request.chat_id
            if not crud.get_chat(chat_id):
                raise HTTPException(status_code=404, detail="Chat not found")
        
        # Save user message
        crud.create_message(chat_id, chat_request.message, "user")
        
        # Get chat history
        messages = crud.get_messages(chat_id)
        history = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        
        # Route query
        response_text = await route_query(chat_request.message, history)
        
        # Save assistant response
        crud.create_message(chat_id, response_text, "assistant")
        
        # Update chat title if default
        chat = crud.get_chat(chat_id)
        if chat and chat["title"] == chat_request.message[:30] + "...":
            new_title = response_text[:30] + "..." if len(response_text) > 30 else response_text
            crud.update_chat_title(chat_id, new_title)
        
        return ChatResponse(response=response_text, chat_id=chat_id)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats")
async def get_chats():
    try:
        chats = crud.get_chats()
        return [dict(chat) for chat in chats]
    except Exception as e:
        logger.error(f"Error getting chats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chats/{chat_id}")
async def get_chat(chat_id: int):
    try:
        chat = crud.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        messages = crud.get_messages(chat_id)
        return {
            "id": chat["id"],
            "title": chat["title"],
            "created_at": chat["created_at"],
            "messages": [dict(message) for message in messages]
        }
    except Exception as e:
        logger.error(f"Error getting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int):
    try:
        success = crud.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found")
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chats")
async def delete_all_chats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chats")
        cursor.execute("DELETE FROM messages")  # Cascade delete messages
        conn.commit()
        conn.close()
        return {"message": "All chats deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting all chats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))