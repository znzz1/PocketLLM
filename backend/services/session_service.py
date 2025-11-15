"""Session management service for chat sessions."""
from datetime import datetime
from typing import Dict, List, Optional
from schemas.chat import ChatMessage, ChatHistory
import uuid


class SessionService:
    """Manages user chat sessions and message history."""

    def __init__(self):
        """Initialize session service."""
        # In-memory session store (replace with database in production)
        self.sessions: Dict[str, ChatHistory] = {}
        # User sessions index
        self.user_sessions: Dict[str, List[str]] = {}

    def create_session(self, user_id: str) -> str:
        """Create a new chat session for a user."""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()

        session = ChatHistory(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            created_at=now,
            updated_at=now
        )

        self.sessions[session_id] = session

        # Add to user sessions index
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[ChatHistory]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[ChatHistory]:
        """Get all sessions for a user."""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None
    ) -> ChatMessage:
        """Add a message to a session."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.user_id != user_id:
            raise ValueError("User does not own this session")

        message = ChatMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            tokens_used=tokens_used
        )

        session.messages.append(message)
        session.updated_at = datetime.utcnow()

        return message

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages in a session."""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session.messages

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a session."""
        session = self.sessions.get(session_id)
        if not session:
            return False

        if session.user_id != user_id:
            raise ValueError("User does not own this session")

        # Remove from sessions
        del self.sessions[session_id]

        # Remove from user sessions index
        if user_id in self.user_sessions:
            self.user_sessions[user_id].remove(session_id)

        return True

    def clear_all_sessions(self) -> int:
        """Clear all sessions (admin operation)."""
        count = len(self.sessions)
        self.sessions.clear()
        self.user_sessions.clear()
        return count
