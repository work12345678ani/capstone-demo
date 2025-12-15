from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User table to track conversation owners"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    password_hash = Column(String(255), nullable=False)  # <-- add this
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to conversations
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Conversation(Base):
    """
    Conversation metadata table linking users to LangGraph thread_ids.
    This bridges your custom user system with LangGraph's checkpoint system.
    """
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Optional conversation title
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="conversations")
    
    # Create composite index for common queries
    __table_args__ = (
        Index('idx_user_updated', 'user_id', 'updated_at'),
    )

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True)  # opaque token
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_sessions_id_expires", "id", "expires_at"),)
