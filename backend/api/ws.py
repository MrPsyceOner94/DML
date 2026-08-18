"""
WebSocket endpoints for real-time features:
- Live match scoring
- Coaches chat
- Alert broadcasts
- Trade recommendations
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List, Set
import json
import logging
from datetime import datetime
from asyncio import sleep

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.chat_history: Dict[str, List[Dict]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        logger.info(f"Client connected to {channel}. Total: {len(self.active_connections[channel])}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            logger.info(f"Client disconnected from {channel}. Total: {len(self.active_connections[channel])}")
    
    async def broadcast(self, channel: str, message: Dict):
        """Broadcast message to all clients in channel"""
        if channel not in self.active_connections:
            return
        
        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {channel}: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn, channel)
    
    async def send_personal(self, websocket: WebSocket, message: Dict):
        """Send message to specific client"""
        message["timestamp"] = datetime.utcnow().isoformat()
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    def get_channel_size(self, channel: str) -> int:
        return len(self.active_connections.get(channel, []))
    
    def store_chat_message(self, team_id: str, message: Dict):
        """Store chat message in memory (persist to DB in production)"""
        if team_id not in self.chat_history:
            self.chat_history[team_id] = []
        message["timestamp"] = datetime.utcnow().isoformat()
        self.chat_history[team_id].append(message)
        # Keep last 100 messages
        if len(self.chat_history[team_id]) > 100:
            self.chat_history[team_id] = self.chat_history[team_id][-100:]
    
    def get_chat_history(self, team_id: str, limit: int = 50) -> List[Dict]:
        return self.chat_history.get(team_id, [])[-limit:]


manager = ConnectionManager()


@router.websocket("/ws/live-scoring")
async def websocket_live_scoring(websocket: WebSocket):
    """Live match scoring updates"""
    channel = "live-scoring"
    await manager.connect(websocket, channel)
    
    try:
        while True:
            # Receive client heartbeat
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"Live scoring error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket, team_id: int = Query(...)):
    """Real-time alerts for team (injuries, suspensions, trades)"""
    channel = f"alerts-{team_id}"
    await manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/chat/{team_id}")
async def websocket_chat(websocket: WebSocket, team_id: int):
    """Coaches real-time chat for team"""
    channel = f"chat-{team_id}"
    await manager.connect(websocket, channel)
    
    # Send chat history on connect
    history = manager.get_chat_history(str(team_id), limit=20)
    await manager.send_personal(websocket, {
        "type": "history",
        "messages": history
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                message = {
                    "type": "message",
                    "sender": data.get("sender", "Anonymous"),
                    "sender_id": data.get("sender_id"),
                    "content": data.get("content", ""),
                    "team_id": team_id,
                }
                
                # Store message
                manager.store_chat_message(str(team_id), message)
                
                # Broadcast to all coaches in team
                await manager.broadcast(channel, message)
                
                logger.info(f"Chat message in team {team_id}: {message['sender']}")
            
            elif data.get("type") == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        await manager.broadcast(channel, {
            "type": "notification",
            "message": f"{data.get('sender', 'A coach')} left the chat"
        })
    except Exception as e:
        logger.error(f"Chat error: {e}")
        manager.disconnect(websocket, channel)


@router.websocket("/ws/trades/{team_id}")
async def websocket_trades(websocket: WebSocket, team_id: int):
    """Real-time trade recommendations and updates"""
    channel = f"trades-{team_id}"
    await manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"Trades error: {e}")
        manager.disconnect(websocket, channel)
