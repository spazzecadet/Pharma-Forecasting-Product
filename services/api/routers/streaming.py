from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import asyncio
import sys
from pathlib import Path

from auth.dependencies import get_current_user_optional
from auth.models import User

router = APIRouter(prefix="/streaming", tags=["streaming"])

# Add repo root to path for ML imports
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.append(str(repo_root))

from data.connectors.streaming import rt_manager  # type: ignore

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.disconnect(connection)

manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Send real-time data every 5 seconds
            await asyncio.sleep(5)
            
            # Get latest data from all sources
            summary = rt_manager.get_data_summary()
            
            message = {
                "type": "data_update",
                "timestamp": datetime.utcnow().isoformat(),
                "sources": summary
            }
            
            await manager.send_personal_message(json.dumps(message), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/sources")
def get_data_sources(current_user: User = Depends(get_current_user_optional)):
    """Get available real-time data sources."""
    summary = rt_manager.get_data_summary()
    return {
        "sources": summary,
        "total_sources": len(summary),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/sources/{source_name}/data")
def get_source_data(
    source_name: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user_optional)
):
    """Get recent data from a specific source."""
    data = rt_manager.get_cached_data(source_name, limit)
    return {
        "source": source_name,
        "data": data,
        "count": len(data),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/sources/{source_name}/subscribe")
def subscribe_to_source(
    source_name: str,
    current_user: User = Depends(get_current_user_optional)
):
    """Subscribe to real-time updates from a data source."""
    def data_callback(data):
        # This would be called when new data arrives
        rt_manager.cache_data(source_name, data)
    
    rt_manager.subscribe_to_data(source_name, data_callback)
    
    return {
        "message": f"Subscribed to {source_name}",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
def streaming_health_check():
    """Health check for streaming services."""
    try:
        summary = rt_manager.get_data_summary()
        return {
            "status": "healthy",
            "active_connections": len(manager.active_connections),
            "data_sources": len(summary),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
