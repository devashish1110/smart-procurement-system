"""
Chatbot API Routes
File: backend/api/routes/chatbot.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime

from backend.config.database import get_db
from backend.models.database import User, ChatConversation
from backend.schemas.schemas import ChatMessage, ChatResponse
from backend.auth.security import get_current_user
from backend.ai.chatbot_engine import get_chatbot_engine


router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    chat_message: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send message to chatbot and get response.
    
    **Request Body:**
    ```json
    {
        "message": "What medicines are low in stock?",
        "session_id": "optional-session-id"
    }
    ```
    
    **Returns:**
    - response: Chatbot's response
    - session_id: Conversation session ID
    - intent: Detected intent
    - confidence: Intent confidence score
    - suggested_actions: List of suggested next actions
    
    **Example:**
    ```
    POST /api/v1/chatbot/chat
    {
        "message": "Show me expiring medicines"
    }
    ```
    """
    # Generate session ID if not provided
    if not chat_message.session_id:
        session_id = f"session_{current_user.user_id}_{uuid.uuid4().hex[:8]}"
    else:
        session_id = chat_message.session_id
    
    # Get chatbot engine
    chatbot = get_chatbot_engine()
    
    # Process message
    result = chatbot.process_message(
        user_message=chat_message.message,
        user_id=current_user.user_id,
        session_id=session_id,
        db=db
    )
    
    # Return response
    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        intent=result.get("intent"),
        confidence=result.get("confidence"),
        timestamp=result["timestamp"],
        suggested_actions=result.get("suggested_actions", [])
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation history for a session.
    
    **Path Parameters:**
    - session_id: Conversation session ID
    
    **Query Parameters:**
    - limit: Maximum number of messages to return (default: 20)
    
    **Returns:**
    - List of conversation messages with timestamps
    """
    conversations = db.query(ChatConversation).filter(
        ChatConversation.session_id == session_id,
        ChatConversation.user_id == current_user.user_id
    ).order_by(
        ChatConversation.created_at.desc()
    ).limit(limit).all()
    
    history = []
    for conv in reversed(conversations):
        history.append({
            "message": conv.message,
            "response": conv.response,
            "intent": conv.intent,
            "confidence": conv.confidence,
            "timestamp": conv.created_at
        })
    
    return {
        "session_id": session_id,
        "message_count": len(history),
        "history": history
    }


@router.get("/sessions")
async def get_user_sessions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all chat sessions for current user.
    
    **Query Parameters:**
    - limit: Maximum number of sessions to return (default: 10)
    
    **Returns:**
    - List of session IDs with message counts and timestamps
    """
    from sqlalchemy import func
    
    sessions = db.query(
        ChatConversation.session_id,
        func.count(ChatConversation.conversation_id).label('message_count'),
        func.max(ChatConversation.created_at).label('last_activity')
    ).filter(
        ChatConversation.user_id == current_user.user_id
    ).group_by(
        ChatConversation.session_id
    ).order_by(
        func.max(ChatConversation.created_at).desc()
    ).limit(limit).all()
    
    return [
        {
            "session_id": session_id,
            "message_count": count,
            "last_activity": last_activity
        }
        for session_id, count, last_activity in sessions
    ]


@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a chat session and its history.
    
    **Path Parameters:**
    - session_id: Conversation session ID to delete
    """
    # Verify session belongs to current user
    conversations = db.query(ChatConversation).filter(
        ChatConversation.session_id == session_id,
        ChatConversation.user_id == current_user.user_id
    ).all()
    
    if not conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Delete all conversations in session
    for conv in conversations:
        db.delete(conv)
    
    db.commit()
    
    return {
        "message": f"Session {session_id} deleted successfully",
        "deleted_messages": len(conversations)
    }


@router.post("/rebuild-knowledge-base")
async def rebuild_knowledge_base_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Rebuild the chatbot knowledge base (no-op in mock mode)."""
    import os
    if os.getenv('USE_MOCK_LLM', 'false').lower() == 'true':
        return {"message": "Running in mock mode — knowledge base not used", "timestamp": datetime.now()}
    try:
        from backend.ai.rag_pipeline import rebuild_knowledge_base
        rebuild_knowledge_base()
        return {"message": "Knowledge base rebuilt successfully", "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild knowledge base: {str(e)}")


@router.get("/stats")
async def get_chatbot_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get chatbot usage statistics for current user.
    
    **Returns:**
    - Total messages
    - Sessions count
    - Intent distribution
    - Recent activity
    """
    from sqlalchemy import func
    from datetime import timedelta, date
    
    # Total messages
    total_messages = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.user_id
    ).count()
    
    # Total sessions
    total_sessions = db.query(
        ChatConversation.session_id
    ).filter(
        ChatConversation.user_id == current_user.user_id
    ).distinct().count()
    
    # Intent distribution
    intent_dist = db.query(
        ChatConversation.intent,
        func.count(ChatConversation.conversation_id).label('count')
    ).filter(
        ChatConversation.user_id == current_user.user_id
    ).group_by(
        ChatConversation.intent
    ).all()
    
    # Recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_messages = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.user_id,
        ChatConversation.created_at >= week_ago
    ).count()
    
    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "recent_messages_7d": recent_messages,
        "intent_distribution": {
            intent: count for intent, count in intent_dist if intent
        },
        "average_confidence": 0.75  # Placeholder
    }


@router.get("/health")
async def chatbot_health_check():
    """Check if chatbot services are running properly."""
    import os
    use_mock = os.getenv('USE_MOCK_LLM', 'false').lower() == 'true'
    if use_mock:
        return {
            "status": "healthy",
            "mode": "mock",
            "llm_service": "operational",
            "rag_pipeline": "disabled (mock mode)",
        }
    try:
        from backend.ai.llm_service import get_llm_service
        from backend.ai.rag_pipeline import get_rag_pipeline
        llm_service = get_llm_service()
        rag_pipeline = get_rag_pipeline()
        return {
            "status": "healthy",
            "mode": "llm",
            "llm_service": "operational",
            "rag_pipeline": "operational",
            "knowledge_base_docs": len(rag_pipeline.documents) if rag_pipeline.documents else 0
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}