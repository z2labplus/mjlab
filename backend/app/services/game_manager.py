from typing import Dict, Optional
from fastapi import WebSocket
import json


class GameManager:
    """游戏管理器，处理WebSocket连接和游戏状态同步"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.game_states: Dict[str, dict] = {}
    
    async def add_client(self, client_id: str, websocket: WebSocket):
        """添加客户端连接"""
        self.active_connections[client_id] = websocket
        print(f"客户端 {client_id} 已连接")
    
    def remove_client(self, client_id: str):
        """移除客户端连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.game_states:
            del self.game_states[client_id]
        print(f"客户端 {client_id} 已断开连接")
    
    async def send_to_client(self, client_id: str, message: dict):
        """发送消息给特定客户端"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print(f"发送消息给客户端 {client_id} 失败: {e}")
                self.remove_client(client_id)
    
    async def broadcast(self, message: dict, exclude_client: Optional[str] = None):
        """广播消息给所有客户端"""
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue
            
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print(f"广播消息给客户端 {client_id} 失败: {e}")
                disconnected_clients.append(client_id)
        
        # 清理断开的连接
        for client_id in disconnected_clients:
            self.remove_client(client_id)
    
    def update_game_state(self, client_id: str, game_state: dict):
        """更新游戏状态"""
        self.game_states[client_id] = game_state
    
    def get_game_state(self, client_id: str) -> Optional[dict]:
        """获取游戏状态"""
        return self.game_states.get(client_id)
    
    def get_connected_clients(self) -> list:
        """获取已连接的客户端列表"""
        return list(self.active_connections.keys())
    
    def get_client_count(self) -> int:
        """获取连接的客户端数量"""
        return len(self.active_connections) 