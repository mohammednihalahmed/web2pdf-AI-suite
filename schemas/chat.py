from pydantic import BaseModel
from typing import List
from datetime import datetime

class MessageSchema(BaseModel):
    id: int
    sender: str
    message: str
    timestamp: datetime

    class Config:
        orm_mode = True

class ChatSchema(BaseModel):
    id: int
    user_id: int
    chat_name: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        orm_mode = True
