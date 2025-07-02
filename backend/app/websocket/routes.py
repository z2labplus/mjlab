from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import uuid
import logging
from typing import Optional

from .connection_manager import manager
from .message_handler import handler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: Optional[str] = Query(default="default", description="房间ID"),
    client_id: Optional[str] = Query(default=None, description="客户端ID")
):
    """WebSocket连接端点"""
    
    # 生成唯一连接ID
    connection_id = client_id or f"conn_{uuid.uuid4().hex[:8]}"
    
    try:
        # 建立连接
        await manager.connect(websocket, connection_id, room_id)
        
        # 发送连接成功消息
        welcome_message = {
            "type": "system",
            "event": "connected",
            "data": {
                "connection_id": connection_id,
                "room_id": room_id,
                "message": "WebSocket连接建立成功"
            },
            "timestamp": "2024-01-01T00:00:00"
        }
        await websocket.send_text(json.dumps(welcome_message, ensure_ascii=False))
        
        # 监听消息
        while True:
            # 接收客户端消息
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                logger.info(f"收到消息 {connection_id}: {message_data.get('action', 'unknown')}")
                
                # 处理消息
                await handler.handle_message(websocket, connection_id, message_data)
                
            except json.JSONDecodeError:
                error_message = {
                    "type": "error",
                    "message": "消息格式错误，请发送有效的JSON数据",
                    "timestamp": "2024-01-01T00:00:00"
                }
                await websocket.send_text(json.dumps(error_message, ensure_ascii=False))
            
            except Exception as e:
                logger.error(f"处理消息异常 {connection_id}: {e}")
                error_message = {
                    "type": "error", 
                    "message": f"处理消息失败: {str(e)}",
                    "timestamp": "2024-01-01T00:00:00"
                }
                await websocket.send_text(json.dumps(error_message, ensure_ascii=False))
    
    except WebSocketDisconnect:
        # WebSocket断开连接
        manager.disconnect(connection_id)
        logger.info(f"WebSocket正常断开: {connection_id}")
    
    except Exception as e:
        # 其他异常
        logger.error(f"WebSocket异常断开 {connection_id}: {e}")
        manager.disconnect(connection_id)


@router.get("/ws/rooms")
async def get_rooms():
    """获取所有房间信息"""
    try:
        all_rooms = manager.get_all_rooms()
        rooms_info = []
        
        for room_id in all_rooms:
            room_info = manager.get_room_info(room_id)
            rooms_info.append(room_info)
        
        return {
            "success": True,
            "message": "获取房间信息成功",
            "data": {
                "total_rooms": len(all_rooms),
                "total_connections": manager.get_connection_count(),
                "rooms": rooms_info
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取房间信息失败: {str(e)}"
        }


@router.get("/ws/room/{room_id}")
async def get_room_info(room_id: str):
    """获取指定房间信息"""
    try:
        room_info = manager.get_room_info(room_id)
        
        if room_info["connection_count"] == 0:
            return {
                "success": False,
                "message": "房间不存在或无连接"
            }
        
        return {
            "success": True,
            "message": "获取房间信息成功",
            "data": room_info
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"获取房间信息失败: {str(e)}"
        }


@router.post("/ws/broadcast/{room_id}")
async def broadcast_to_room(room_id: str, message: dict):
    """向指定房间广播消息（管理员功能）"""
    try:
        connections = manager.get_room_connections(room_id)
        
        if not connections:
            return {
                "success": False,
                "message": "房间不存在或无连接"
            }
        
        # 构造广播消息
        broadcast_message = {
            "type": "broadcast",
            "event": "admin_message",
            "data": message,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        await manager.broadcast_to_room(room_id, broadcast_message)
        
        return {
            "success": True,
            "message": f"向房间 {room_id} 广播消息成功",
            "data": {
                "room_id": room_id,
                "target_connections": len(connections),
                "message": message
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"广播消息失败: {str(e)}"
        }


@router.post("/ws/broadcast")
async def broadcast_to_all(message: dict):
    """向所有连接广播消息（管理员功能）"""
    try:
        total_connections = manager.get_connection_count()
        
        if total_connections == 0:
            return {
                "success": False,
                "message": "当前无活跃连接"
            }
        
        # 构造广播消息
        broadcast_message = {
            "type": "broadcast",
            "event": "admin_message",
            "data": message,
            "timestamp": "2024-01-01T00:00:00"
        }
        
        await manager.broadcast_to_all(broadcast_message)
        
        return {
            "success": True,
            "message": "全局广播消息成功",
            "data": {
                "target_connections": total_connections,
                "message": message
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"广播消息失败: {str(e)}"
        }