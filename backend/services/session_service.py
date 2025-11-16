"""Session management service for chat sessions."""
from datetime import datetime
from typing import List, Optional
from schemas.chat import ChatMessage, ChatHistory
from database import SessionLocal
from database.models import Session as SessionModel, Message as MessageModel
import uuid


class SessionService:
    """Manages user chat sessions and message history."""

    def __init__(self):
        """Initialize session service."""
        pass

    def create_session(self, user_id: str) -> str:
        """Create a new chat session for a user."""
        session_id = str(uuid.uuid4())
        db = SessionLocal()
        try:
            session = SessionModel(
                session_id=session_id,
                user_id=user_id
            )
            db.add(session)
            db.commit()
            return session_id
        finally:
            db.close()

    def get_session(self, session_id: str) -> Optional[ChatHistory]:
        """Get session by ID."""
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if not session:
                return None

            # Convert messages to schema
            messages = [
                ChatMessage(
                    message_id=msg.message_id,
                    session_id=msg.session_id,
                    user_id=msg.user_id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    tokens_used=msg.tokens_used
                )
                for msg in session.messages
            ]

            return ChatHistory(
                session_id=session.session_id,
                user_id=session.user_id,
                messages=messages,
                created_at=session.created_at,
                updated_at=session.updated_at
            )
        finally:
            db.close()

    def get_user_sessions(self, user_id: str) -> List[ChatHistory]:
        """Get all sessions for a user."""
        db = SessionLocal()
        try:
            sessions = db.query(SessionModel).filter(SessionModel.user_id == user_id).all()

            result = []
            for session in sessions:
                messages = [
                    ChatMessage(
                        message_id=msg.message_id,
                        session_id=msg.session_id,
                        user_id=msg.user_id,
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.timestamp,
                        tokens_used=msg.tokens_used
                    )
                    for msg in session.messages
                ]

                result.append(ChatHistory(
                    session_id=session.session_id,
                    user_id=session.user_id,
                    messages=messages,
                    created_at=session.created_at,
                    updated_at=session.updated_at
                ))

            return result
        finally:
            db.close()

    def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None
    ) -> ChatMessage:
        """Add a message to a session."""
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if session.user_id != user_id:
                raise ValueError("User does not own this session")

            message_id = str(uuid.uuid4())
            message = MessageModel(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                tokens_used=tokens_used
            )

            db.add(message)
            session.updated_at = datetime.utcnow()
            db.commit()

            return ChatMessage(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                timestamp=message.timestamp,
                tokens_used=tokens_used
            )
        finally:
            db.close()

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages in a session."""
        db = SessionLocal()
        try:
            messages = db.query(MessageModel).filter(MessageModel.session_id == session_id).all()
            return [
                ChatMessage(
                    message_id=msg.message_id,
                    session_id=msg.session_id,
                    user_id=msg.user_id,
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp,
                    tokens_used=msg.tokens_used
                )
                for msg in messages
            ]
        finally:
            db.close()

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a session."""
        db = SessionLocal()
        try:
            session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
            if not session:
                return False

            if session.user_id != user_id:
                raise ValueError("User does not own this session")

            db.delete(session)
            db.commit()
            return True
        finally:
            db.close()

    def clear_all_sessions(self) -> int:
        """Clear all sessions (admin operation)."""
        db = SessionLocal()
        try:
            count = db.query(SessionModel).count()
            db.query(SessionModel).delete()
            db.commit()
            return count
        finally:
            db.close()

    def get_total_sessions_count(self) -> int:
        """Get total number of sessions in the database."""
        db = SessionLocal()
        try:
            return db.query(SessionModel).count()
        finally:
            db.close()

    def get_total_users_count(self) -> int:
        """Get total number of unique users with sessions."""
        db = SessionLocal()
        try:
            from sqlalchemy import func
            return db.query(func.count(func.distinct(SessionModel.user_id))).scalar()
        finally:
            db.close()
