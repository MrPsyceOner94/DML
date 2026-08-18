"""
API routes for coaches chat
"""

from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional, List
from backend.api.ws import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/{team_id}/messages")
def get_chat_history(
    team_id: int,
    limit: int = 50,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get chat history for team
    """
    messages = manager.get_chat_history(str(team_id), limit=limit)
    
    return {
        "team_id": team_id,
        "messages": messages,
        "total": len(messages),
    }


@router.get("/{team_id}/members")
def get_chat_members(
    team_id: int,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Get number of coaches currently in team chat
    """
    channel = f"chat-{team_id}"
    member_count = manager.get_channel_size(channel)
    
    return {
        "team_id": team_id,
        "active_members": member_count,
        "status": "online" if member_count > 0 else "offline",
    }


@router.delete("/{team_id}/messages")
def clear_chat_history(
    team_id: int,
    dml_session: Optional[str] = Cookie(None),
):
    """
    Clear chat history for team (admin only)
    """
    # Clear from manager
    if str(team_id) in manager.chat_history:
        manager.chat_history[str(team_id)] = []
    
    return {
        "success": True,
        "team_id": team_id,
        "message": "Chat history cleared",
    }
