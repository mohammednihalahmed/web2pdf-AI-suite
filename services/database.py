from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from passlib.context import CryptContext
from typing import Optional
import os
from datetime import datetime

# Define the PostgreSQL connection URL
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:123@localhost/web2pdf"

# Create the async engine and session factory
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Create a configured "Session" class
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for declarative models
Base = declarative_base()

# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the User model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    files = relationship("UserFile", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

class UserFile(Base):
    __tablename__ = 'user_files'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Optional: Back-reference to the User
    user = relationship("User", back_populates="files")

class Chat(Base):
    __tablename__ = 'chats'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    chat_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id', ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)  # Sender can be either 'user' or 'ai'
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    chat = relationship("Chat", back_populates="messages")


# Function to create a new user
async def create_user(db_session: AsyncSession, email: str, username: str, password: str) -> User:
    hashed_password = pwd_context.hash(password)
    db_user = User(email=email, username=username, hashed_password=hashed_password)
    db_session.add(db_user)
    await db_session.commit()
    await db_session.refresh(db_user)
    return db_user

# Function to get user by email
async def get_user_by_email(db_session: AsyncSession, email: str) -> Optional[User]:
    stmt = select(User).filter(User.email == email)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()

# Function to get user by username (if needed for future functionality)
async def get_user_by_username(db_session: AsyncSession, username: str) -> Optional[User]:
    stmt = select(User).filter(User.username == username)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()

# Function to verify the user's password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create a new chat for a user
async def create_chat(db_session: AsyncSession, user_id: int, chat_name: str) -> Chat:
    db_chat = Chat(user_id=user_id, chat_name=chat_name)
    db_session.add(db_chat)
    await db_session.commit()
    await db_session.refresh(db_chat)
    return db_chat

# Add a message to a specific chat
async def add_message_to_chat(db_session: AsyncSession, chat_id: int, sender: str, message: str) -> Message:
    db_message = Message(chat_id=chat_id, sender=sender, message=message)
    db_session.add(db_message)
    await db_session.commit()
    await db_session.refresh(db_message)
    return db_message

# Get messages for a specific chat
async def get_chat_messages(db_session: AsyncSession, chat_id: int) -> Optional[list[Message]]:
    stmt = select(Message).filter(Message.chat_id == chat_id).order_by(Message.timestamp.asc())
    result = await db_session.execute(stmt)
    return result.scalars().all()

# Rename a chat
async def rename_chat(db_session: AsyncSession, chat_id: int, new_name: str) -> Optional[Chat]:
    stmt = select(Chat).filter(Chat.id == chat_id).first()
    chat = await db_session.execute(stmt)
    if chat:
        chat.chat_name = new_name
        await db_session.commit()
        return chat
    return None

# Delete a chat and all related messages
async def delete_chat(db_session: AsyncSession, chat_id: int) -> Optional[bool]:
    stmt = select(Chat).filter(Chat.id == chat_id).first()
    chat = await db_session.execute(stmt)
    if chat:
        await db_session.delete(chat)
        await db_session.commit()
        return True
    return False

# Dependency to get the DB session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        # this issues CREATE TABLE IF NOT EXISTS ... for all models
        await conn.run_sync(Base.metadata.create_all)
