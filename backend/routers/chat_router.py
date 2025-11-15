"""Chat API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Annotated, List
from schemas.chat import ChatRequest, ChatResponse, ChatHistory
from schemas.auth import TokenPayload
from utils.dependencies import get_current_user
import utils.dependencies as deps
from datetime import datetime
import uuid
import json
import asyncio

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)]
):
    """
    Send a chat message and get LLM response.

    Creates or uses existing session, stores messages, and returns LLM inference.
    """
    deps.monitoring_service.increment_request_count()

    # Create or get session
    session_id = request.session_id
    if not session_id:
        session_id = deps.session_service.create_session(current_user.sub)
    else:
        # Verify session exists and belongs to user
        session = deps.session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        if session.user_id != current_user.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )

    # Add user message to session
    deps.session_service.add_message(
        session_id=session_id,
        user_id=current_user.sub,
        role="user",
        content=request.prompt,
        tokens_used=None
    )

    # Get conversation history to build context
    session = deps.session_service.get_session(session_id)
    conversation_history = session.messages if session else []

    # Build chat prompt with conversation history
    # TinyLlama-Chat format: <|system|>\n{system_message}</s>\n<|user|>\n{user_message}</s>\n<|assistant|>\n
    formatted_prompt = ""

    # Add system message
    formatted_prompt += "<|system|>\nYou are a helpful assistant. Answer questions directly without using prefixes like 'AI:', 'Assistant:', or 'User:'. Do not generate example dialogues.</s>\n"

    # Add conversation history (skip the last message as we just added it)
    for msg in conversation_history[:-1]:
        if msg.role == "user":
            formatted_prompt += f"<|user|>\n{msg.content}</s>\n"
        elif msg.role == "assistant":
            formatted_prompt += f"<|assistant|>\n{msg.content}</s>\n"

    # Add the current user message
    formatted_prompt += f"<|user|>\n{request.prompt}</s>\n<|assistant|>\n"

    # Run LLM inference
    response_text, cached = deps.inference_service.infer(
        prompt=formatted_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        use_cache=True
    )

    # Count tokens (approximate - split by spaces)
    tokens_used = len(response_text.split())

    # Add assistant message to session
    deps.session_service.add_message(
        session_id=session_id,
        user_id=current_user.sub,
        role="assistant",
        content=response_text,
        tokens_used=tokens_used
    )

    return ChatResponse(
        message_id=str(uuid.uuid4()),
        session_id=session_id,
        response=response_text,
        tokens_used=tokens_used,
        cached=cached,
        timestamp=datetime.utcnow()
    )


@router.get("/history", response_model=List[ChatHistory])
async def get_history(
    current_user: Annotated[TokenPayload, Depends(get_current_user)]
):
    """
    Get all chat sessions for current user.
    """
    deps.monitoring_service.increment_request_count()
    sessions = deps.session_service.get_user_sessions(current_user.sub)
    return sessions


@router.get("/history/{session_id}", response_model=ChatHistory)
async def get_session_history(
    session_id: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)]
):
    """
    Get specific session history.
    """
    deps.monitoring_service.increment_request_count()
    session = deps.session_service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.user_id != current_user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session"
        )

    return session


@router.delete("/history/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Annotated[TokenPayload, Depends(get_current_user)]
):
    """
    Delete a chat session.
    """
    deps.monitoring_service.increment_request_count()
    success = deps.session_service.delete_session(session_id, current_user.sub)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Session deleted successfully"}


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)]
):
    """
    Send a chat message and get streaming LLM response.

    Returns Server-Sent Events (SSE) stream with incremental response.
    """
    deps.monitoring_service.increment_request_count()

    # Create or get session
    session_id = request.session_id
    if not session_id:
        session_id = deps.session_service.create_session(current_user.sub)
    else:
        # Verify session exists and belongs to user
        session = deps.session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        if session.user_id != current_user.sub:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )

    # Add user message to session
    deps.session_service.add_message(
        session_id=session_id,
        user_id=current_user.sub,
        role="user",
        content=request.prompt,
        tokens_used=None
    )

    # Get conversation history
    session = deps.session_service.get_session(session_id)
    conversation_history = session.messages if session else []

    # Build formatted prompt
    formatted_prompt = "<|system|>\nYou are a helpful assistant. Answer questions directly without using prefixes like 'AI:', 'Assistant:', or 'User:'. Do not generate example dialogues.</s>\n"

    for msg in conversation_history[:-1]:
        if msg.role == "user":
            formatted_prompt += f"<|user|>\n{msg.content}</s>\n"
        elif msg.role == "assistant":
            formatted_prompt += f"<|assistant|>\n{msg.content}</s>\n"

    formatted_prompt += f"<|user|>\n{request.prompt}</s>\n<|assistant|>\n"

    # Stream generator function
    async def generate_stream():
        """Generate Server-Sent Events stream."""
        full_response = ""
        message_id = str(uuid.uuid4())

        # Send initial event with session_id and message_id
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id, 'message_id': message_id})}\n\n"

        # Stream LLM response
        try:
            token_stream = deps.inference_service.stream_infer(
                prompt=formatted_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            for token in token_stream:
                if token:
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    # Allow event loop to send data immediately
                    await asyncio.sleep(0)

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return

        # Add assistant message to session
        tokens_used = len(full_response.split())
        deps.session_service.add_message(
            session_id=session_id,
            user_id=current_user.sub,
            role="assistant",
            content=full_response,
            tokens_used=tokens_used
        )

        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'tokens_used': tokens_used, 'timestamp': datetime.utcnow().isoformat()})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
