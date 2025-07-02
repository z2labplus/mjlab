from typing import Dict, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储所有活跃连接 {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 连接到房间的映射 {connection_id: room_id}
        self.connection_rooms: Dict[str, str] = {}
        # 房间到连接的映射 {room_id: [connection_ids]}
        self.room_connections: Dict[str, List[str]] = {}
        # 连接信息 {connection_id: connection_info}
        self.connection_info: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, room_id: str = "default"):
        """新连接接入"""
        await websocket.accept()
        
        # 存储连接
        self.active_connections[connection_id] = websocket
        self.connection_rooms[connection_id] = room_id
        
        # 加入房间
        if room_id not in self.room_connections:
            self.room_connections[room_id] = []
        self.room_connections[room_id].append(connection_id)
        
        # 存储连接信息
        self.connection_info[connection_id] = {
            "id": connection_id,
            "room_id": room_id,
            "connected_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        logger.info(f"WebSocket连接建立: {connection_id} (房间: {room_id})")
        
        # 向房间其他成员广播新成员加入
        await self.broadcast_to_room(room_id, {
            "type": "broadcast",
            "event": "client_connected",
            "data": {
                "connection_id": connection_id,
                "room_id": room_id,
                "total_connections": len(self.room_connections[room_id])
            },
            "timestamp": datetime.now().isoformat()
        }, exclude=[connection_id])
    
    def disconnect(self, connection_id: str):
        """连接断开"""
        room_id = self.connection_rooms.get(connection_id)
        
        # 从连接池中移除
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # 从房间中移除
        if connection_id in self.connection_rooms:
            del self.connection_rooms[connection_id]
        
        if room_id and room_id in self.room_connections:
            if connection_id in self.room_connections[room_id]:
                self.room_connections[room_id].remove(connection_id)
            
            # 如果房间为空，删除房间
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        
        # 删除连接信息
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]
        
        logger.info(f"WebSocket连接断开: {connection_id} (房间: {room_id})")
        
        # 向房间其他成员广播成员离开（使用异步任务）
        if room_id:
            asyncio.create_task(self.notify_client_disconnected(room_id, connection_id))
    
    async def notify_client_disconnected(self, room_id: str, disconnected_id: str):
        """通知客户端断开连接"""
        remaining_count = len(self.room_connections.get(room_id, []))
        await self.broadcast_to_room(room_id, {
            "type": "broadcast",
            "event": "client_disconnected", 
            "data": {
                "connection_id": disconnected_id,
                "room_id": room_id,
                "total_connections": remaining_count
            },
            "timestamp": datetime.now().isoformat()
        })
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """发送个人消息"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                
                # 更新最后活动时间
                if connection_id in self.connection_info:
                    self.connection_info[connection_id]["last_activity"] = datetime.now().isoformat()
                
                return True
            except Exception as e:
                logger.error(f"发送个人消息失败 {connection_id}: {e}")
                # 连接已断开，清理连接
                self.disconnect(connection_id)
                return False
        return False
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude: List[str] = None):
        """向房间广播消息"""
        exclude = exclude or []
        
        if room_id not in self.room_connections:
            return
        
        connection_ids = self.room_connections[room_id].copy()
        failed_connections = []
        
        for connection_id in connection_ids:
            if connection_id in exclude:
                continue
                
            success = await self.send_personal_message(message, connection_id)
            if not success:
                failed_connections.append(connection_id)
        
        # 清理失败的连接
        for failed_id in failed_connections:
            self.disconnect(failed_id)
        
        logger.info(f"房间广播 {room_id}: 成功{len(connection_ids) - len(failed_connections)}个, 失败{len(failed_connections)}个")
    
    async def broadcast_to_all(self, message: dict):
        """向所有连接广播消息"""
        connection_ids = list(self.active_connections.keys())
        failed_connections = []
        
        for connection_id in connection_ids:
            success = await self.send_personal_message(message, connection_id)
            if not success:
                failed_connections.append(connection_id)
        
        # 清理失败的连接
        for failed_id in failed_connections:
            self.disconnect(failed_id)
        
        logger.info(f"全局广播: 成功{len(connection_ids) - len(failed_connections)}个, 失败{len(failed_connections)}个")
    
    def get_room_connections(self, room_id: str) -> List[str]:
        """获取房间所有连接"""
        return self.room_connections.get(room_id, [])
    
    def get_connection_count(self, room_id: str = None) -> int:
        """获取连接数量"""
        if room_id:
            return len(self.room_connections.get(room_id, []))
        return len(self.active_connections)
    
    def get_all_rooms(self) -> List[str]:
        """获取所有房间"""
        return list(self.room_connections.keys())
    
    def get_connection_info(self, connection_id: str) -> Optional[dict]:
        """获取连接信息"""
        return self.connection_info.get(connection_id)
    
    def get_room_info(self, room_id: str) -> dict:
        """获取房间信息"""
        connections = self.room_connections.get(room_id, [])
        return {
            "room_id": room_id,
            "connection_count": len(connections),
            "connections": [
                self.connection_info.get(conn_id, {"id": conn_id})
                for conn_id in connections
            ]
        }


# 全局连接管理器实例
manager = ConnectionManager()