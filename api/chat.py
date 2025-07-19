from fastapi import APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from services.auth_utils import get_current_user_id
from services.database import get_db_session, Chat, Message, User
from services.chatbot_service import generate_response
from datetime import datetime
from schemas.chat import ChatSchema 

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    mode: str  # "general" or "pdf"
    chat_id: int  
    chunk_filename: Optional[str] = None

class ChatResponse(BaseModel):
    response: str

class ChatHistoryResponse(BaseModel):
    chat_id: int
    chat_name: str
    messages: List[dict]


@router.get("/chats", response_model=List[ChatSchema])
async def get_chats(
    db_session: AsyncSession = Depends(get_db_session),
    user_id: int = Depends(get_current_user_id)
):
    try:
        stmt = (
            select(Chat)
            .where(Chat.user_id == user_id)
            .options(selectinload(Chat.messages))
            .order_by(Chat.created_at.desc())
        )
        result = await db_session.execute(stmt)
        chats = result.scalars().all()
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_chats", status_code=201)
async def create_chat(
    user_id: int = Body(...), chat_name: str = Body(...), db_session: AsyncSession = Depends(get_db_session)
):
    stmt = select(User).filter(User.id == user_id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_chat = Chat(user_id=user_id, chat_name=chat_name, created_at=datetime.utcnow())
    db_session.add(new_chat)
    await db_session.commit()
    await db_session.refresh(new_chat)

    return {"chat_id": new_chat.id, "chat_name": new_chat.chat_name}

@router.post("/chats/{chat_id}/messages", status_code=201)
async def add_message(
    chat_id: int, sender: str, message: str, db_session: AsyncSession = Depends(get_db_session)
):
    stmt = select(Chat).filter(Chat.id == chat_id)
    result = await db_session.execute(stmt)
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    new_message = Message(chat_id=chat_id, sender=sender, message=message, timestamp=datetime.utcnow())
    db_session.add(new_message)
    await db_session.commit()
    await db_session.refresh(new_message)

    return {"message_id": new_message.id, "sender": new_message.sender, "message": new_message.message}

@router.get("/chats/{chat_id}/messages", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: int, db_session: AsyncSession = Depends(get_db_session)
):
    stmt = select(Chat).filter(Chat.id == chat_id).options(selectinload(Chat.messages))
    result = await db_session.execute(stmt)
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = [{"sender": msg.sender, "message": msg.message, "timestamp": msg.timestamp} for msg in chat.messages]
    return {"chat_id": chat.id, "chat_name": chat.chat_name, "messages": messages}

@router.put("/chats/{chat_id}")
async def rename_chat(
    chat_id: int, new_name: str, db_session: AsyncSession = Depends(get_db_session)
):
    stmt = select(Chat).filter(Chat.id == chat_id)
    result = await db_session.execute(stmt)
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.chat_name = new_name
    await db_session.commit()
    return {"chat_id": chat.id, "new_name": chat.chat_name}

@router.delete("/chats/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: int, db_session: AsyncSession = Depends(get_db_session)
):
    stmt = select(Chat).filter(Chat.id == chat_id)
    result = await db_session.execute(stmt)
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    await db_session.delete(chat)
    await db_session.commit()
    return {"detail": "Chat deleted successfully"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db_session: AsyncSession = Depends(get_db_session)):

    print("📥 Received request:", request)
    try:
        response_text = generate_response(
            query=request.query,
            mode=request.mode,
            chunk_filename=request.chunk_filename
        )
        
        new_user_message = Message(
            chat_id=request.chat_id,
            sender="user",
            message=request.query,
            timestamp=datetime.utcnow()
        )
        db_session.add(new_user_message)
        
        new_bot_message = Message(
            chat_id=request.chat_id,
            sender="bot",
            message=response_text,
            timestamp=datetime.utcnow()
        )
        db_session.add(new_bot_message)
        
        await db_session.commit()
        return ChatResponse(response=response_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
