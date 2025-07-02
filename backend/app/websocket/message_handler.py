from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime

from ..services.mahjong_game_service import MahjongGameService
from ..models.mahjong import (
    TileOperationRequest, Tile, TileType, GameStateRequest
)
from .connection_manager import manager

logger = logging.getLogger(__name__)


class MessageHandler:
    """WebSocket消息处理器"""
    
    def __init__(self):
        self.game_service = MahjongGameService()
        
        # 消息处理映射
        self.handlers = {
            "get_game_state": self._handle_get_game_state,
            "set_game_state": self._handle_set_game_state,
            "player_action": self._handle_player_action,
            "game_control": self._handle_game_control,
            "missing_suit": self._handle_missing_suit,
            "export_record": self._handle_export_record,
            "import_record": self._handle_import_record,
            "health_check": self._handle_health_check,
            "get_connections": self._handle_get_connections
        }
    
    async def handle_message(self, websocket, connection_id: str, message_data: dict):
        """处理WebSocket消息"""
        try:
            message_type = message_data.get("type", "")
            action = message_data.get("action", "")
            data = message_data.get("data", {})
            request_id = message_data.get("request_id", "")
            
            if message_type != "request":
                await self._send_error_response(websocket, request_id, f"不支持的消息类型: {message_type}")
                return
            
            if action not in self.handlers:
                await self._send_error_response(websocket, request_id, f"不支持的操作: {action}")
                return
            
            # 调用对应的处理函数
            handler = self.handlers[action]
            await handler(websocket, connection_id, data, request_id)
            
        except Exception as e:
            logger.error(f"处理消息失败 {connection_id}: {e}")
            await self._send_error_response(websocket, 
                                          message_data.get("request_id", ""), 
                                          f"处理消息失败: {str(e)}")
    
    async def _send_response(self, websocket, request_id: str, action: str, 
                           success: bool, data: Any = None, message: str = ""):
        """发送响应消息"""
        response = {
            "type": "response",
            "action": action,
            "success": success,
            "data": data,
            "message": message,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(response, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送响应失败: {e}")
    
    async def _send_error_response(self, websocket, request_id: str, error_message: str):
        """发送错误响应"""
        await self._send_response(websocket, request_id, "error", False, None, error_message)
    
    async def _broadcast_event(self, room_id: str, event: str, data: Any, exclude_connections: list = None):
        """广播事件"""
        message = {
            "type": "broadcast",
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await manager.broadcast_to_room(room_id, message, exclude=exclude_connections or [])
    
    # ============ 消息处理函数 ============
    
    async def _handle_get_game_state(self, websocket, connection_id: str, data: dict, request_id: str):
        """获取游戏状态"""
        try:
            game_state = self.game_service.get_game_state()
            await self._send_response(websocket, request_id, "get_game_state", True, 
                                    {"game_state": game_state}, "获取游戏状态成功")
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"获取游戏状态失败: {str(e)}")
    
    async def _handle_set_game_state(self, websocket, connection_id: str, data: dict, request_id: str):
        """设置游戏状态"""
        try:
            game_state = data.get("game_state")
            if not game_state:
                await self._send_error_response(websocket, request_id, "缺少游戏状态数据")
                return
            
            success = self.game_service.set_game_state_dict(game_state)
            
            if success:
                # 广播游戏状态更新
                room_id = manager.connection_rooms.get(connection_id, "default")
                await self._broadcast_event(room_id, "game_state_updated", 
                                          {"game_state": game_state}, [connection_id])
                
                await self._send_response(websocket, request_id, "set_game_state", True, 
                                        {"game_state": game_state}, "设置游戏状态成功")
            else:
                await self._send_error_response(websocket, request_id, "设置游戏状态失败")
                
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"设置游戏状态失败: {str(e)}")
    
    async def _handle_player_action(self, websocket, connection_id: str, data: dict, request_id: str):
        """处理玩家操作"""
        try:
            operation_type = data.get("operation_type")  # add_tile, discard, peng, gang等
            player_id = data.get("player_id")
            tile_data = data.get("tile", {})
            
            if not all([operation_type, player_id is not None, tile_data]):
                await self._send_error_response(websocket, request_id, "缺少必要的操作参数")
                return
            
            # 创建牌对象
            tile = Tile(
                type=TileType(tile_data.get("type")),
                value=tile_data.get("value")
            )
            
            # 创建操作请求
            request = TileOperationRequest(
                player_id=player_id,
                operation_type=operation_type,
                tile=tile,
                source_player_id=data.get("source_player_id"),
                game_id=data.get("game_id")
            )
            
            # 处理操作
            success, message = self.game_service.process_operation(request)
            
            if success:
                # 获取更新后的游戏状态
                updated_state = self.game_service.get_game_state()
                
                # 广播操作结果
                room_id = manager.connection_rooms.get(connection_id, "default")
                await self._broadcast_event(room_id, "player_action_performed", {
                    "player_id": player_id,
                    "operation_type": operation_type,
                    "tile": tile_data,
                    "message": message,
                    "game_state": updated_state
                }, [connection_id])
                
                await self._send_response(websocket, request_id, "player_action", True,
                                        {"game_state": updated_state}, message)
            else:
                await self._send_error_response(websocket, request_id, message)
                
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"处理玩家操作失败: {str(e)}")
    
    async def _handle_game_control(self, websocket, connection_id: str, data: dict, request_id: str):
        """游戏控制操作"""
        try:
            control_type = data.get("control_type")  # reset, set_current_player, next_player等
            
            if control_type == "reset":
                self.game_service.reset_game()
                updated_state = self.game_service.get_game_state()
                
                # 广播重置事件
                room_id = manager.connection_rooms.get(connection_id, "default")
                await self._broadcast_event(room_id, "game_reset", 
                                          {"game_state": updated_state}, [connection_id])
                
                await self._send_response(websocket, request_id, "game_control", True,
                                        {"game_state": updated_state}, "游戏重置成功")
            
            elif control_type == "set_current_player":
                player_id = data.get("player_id")
                if player_id is None:
                    await self._send_error_response(websocket, request_id, "缺少玩家ID")
                    return
                
                current_state = self.game_service.get_game_state()
                current_state["current_player"] = player_id
                success = self.game_service.set_game_state_dict(current_state)
                
                if success:
                    room_id = manager.connection_rooms.get(connection_id, "default")
                    await self._broadcast_event(room_id, "current_player_changed", {
                        "current_player": player_id,
                        "game_state": current_state
                    }, [connection_id])
                    
                    await self._send_response(websocket, request_id, "game_control", True,
                                            {"current_player": player_id}, f"当前玩家已切换为: {player_id}")
                else:
                    await self._send_error_response(websocket, request_id, "设置当前玩家失败")
            
            elif control_type == "next_player":
                current_state = self.game_service.get_game_state()
                current_player = current_state.get("current_player", 0)
                next_player = (current_player + 1) % 4
                
                current_state["current_player"] = next_player
                success = self.game_service.set_game_state_dict(current_state)
                
                if success:
                    room_id = manager.connection_rooms.get(connection_id, "default")
                    await self._broadcast_event(room_id, "current_player_changed", {
                        "previous_player": current_player,
                        "current_player": next_player,
                        "game_state": current_state
                    }, [connection_id])
                    
                    await self._send_response(websocket, request_id, "game_control", True, {
                        "previous_player": current_player,
                        "current_player": next_player
                    }, f"轮到下一个玩家: {next_player}")
                else:
                    await self._send_error_response(websocket, request_id, "切换玩家失败")
            
            else:
                await self._send_error_response(websocket, request_id, f"不支持的控制操作: {control_type}")
                
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"游戏控制失败: {str(e)}")
    
    async def _handle_missing_suit(self, websocket, connection_id: str, data: dict, request_id: str):
        """定缺操作"""
        try:
            action_type = data.get("action_type")  # set, get, reset
            
            if action_type == "set":
                player_id = data.get("player_id")
                missing_suit = data.get("missing_suit")
                
                if player_id is None or not missing_suit:
                    await self._send_error_response(websocket, request_id, "缺少玩家ID或定缺花色")
                    return
                
                # 设置定缺
                current_state = self.game_service.get_game_state()
                player_id_str = str(player_id)
                
                if player_id_str not in current_state.get("player_hands", {}):
                    current_state.setdefault("player_hands", {})[player_id_str] = {
                        "tiles": None if player_id != 0 else [],
                        "tile_count": 0,
                        "melds": []
                    }
                
                current_state["player_hands"][player_id_str]["missing_suit"] = missing_suit
                success = self.game_service.set_game_state_dict(current_state)
                
                if success:
                    room_id = manager.connection_rooms.get(connection_id, "default")
                    await self._broadcast_event(room_id, "missing_suit_set", {
                        "player_id": player_id,
                        "missing_suit": missing_suit,
                        "game_state": current_state
                    }, [connection_id])
                    
                    await self._send_response(websocket, request_id, "missing_suit", True,
                                            {"player_id": player_id, "missing_suit": missing_suit},
                                            f"玩家{player_id}定缺设置成功: {missing_suit}")
                else:
                    await self._send_error_response(websocket, request_id, "设置定缺失败")
            
            elif action_type == "get":
                current_state = self.game_service.get_game_state()
                missing_suits = {}
                
                for player_id, hand in current_state.get("player_hands", {}).items():
                    missing_suits[player_id] = hand.get("missing_suit")
                
                await self._send_response(websocket, request_id, "missing_suit", True,
                                        {"missing_suits": missing_suits}, "获取定缺信息成功")
            
            elif action_type == "reset":
                current_state = self.game_service.get_game_state()
                
                for player_id, hand in current_state.get("player_hands", {}).items():
                    hand["missing_suit"] = None
                
                success = self.game_service.set_game_state_dict(current_state)
                
                if success:
                    room_id = manager.connection_rooms.get(connection_id, "default")
                    await self._broadcast_event(room_id, "missing_suits_reset", 
                                              {"game_state": current_state}, [connection_id])
                    
                    await self._send_response(websocket, request_id, "missing_suit", True,
                                            {"game_state": current_state}, "所有玩家定缺已重置")
                else:
                    await self._send_error_response(websocket, request_id, "重置定缺失败")
            
            else:
                await self._send_error_response(websocket, request_id, f"不支持的定缺操作: {action_type}")
                
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"定缺操作失败: {str(e)}")
    
    async def _handle_export_record(self, websocket, connection_id: str, data: dict, request_id: str):
        """导出牌谱"""
        try:
            current_state = self.game_service.get_game_state()
            
            # 构建牌谱数据（与HTTP API相同逻辑）
            game_record = {
                "game_info": {
                    "game_id": current_state.get("game_id", "unknown"),
                    "start_time": datetime.now().isoformat(),
                    "player_count": 4,
                    "game_mode": "xuezhan_daodi",
                    "export_time": datetime.now().isoformat()
                },
                "players": {
                    "0": {"name": "我", "position": "我"},
                    "1": {"name": "下家", "position": "下家"},
                    "2": {"name": "对家", "position": "对家"},
                    "3": {"name": "上家", "position": "上家"}
                },
                "missing_suits": {},
                "actions": current_state.get("actions_history", []),
                "final_state": {
                    "player_hands": current_state.get("player_hands", {}),
                    "player_discarded_tiles": current_state.get("player_discarded_tiles", {}),
                    "discarded_tiles": current_state.get("discarded_tiles", [])
                }
            }
            
            # 添加定缺信息
            for player_id in ["0", "1", "2", "3"]:
                player_missing = self.game_service.get_player_missing_suit(int(player_id))
                if player_missing:
                    game_record["missing_suits"][player_id] = player_missing
            
            await self._send_response(websocket, request_id, "export_record", True,
                                    {"game_record": game_record}, "牌谱导出成功")
            
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"导出牌谱失败: {str(e)}")
    
    async def _handle_import_record(self, websocket, connection_id: str, data: dict, request_id: str):
        """导入牌谱"""
        try:
            game_record = data.get("game_record")
            if not game_record:
                await self._send_error_response(websocket, request_id, "请提供有效的牌谱数据")
                return
            
            # 重置游戏状态
            self.game_service.reset_game()
            
            # 导入定缺设置
            missing_suits = game_record.get("missing_suits", {})
            for player_id_str, missing_suit in missing_suits.items():
                player_id = int(player_id_str)
                self.game_service.set_player_missing_suit(player_id, missing_suit)
            
            # 导入最终状态
            final_state = game_record.get("final_state", {})
            if final_state:
                # 设置玩家手牌
                player_hands = final_state.get("player_hands", {})
                for player_id_str, hand_data in player_hands.items():
                    self.game_service._game_state["player_hands"][player_id_str] = hand_data
                
                # 设置弃牌记录
                player_discarded = final_state.get("player_discarded_tiles", {})
                self.game_service._game_state["player_discarded_tiles"] = player_discarded
                
                # 设置公共弃牌
                discarded_tiles = final_state.get("discarded_tiles", [])
                self.game_service._game_state["discarded_tiles"] = discarded_tiles
            
            # 导入操作历史
            actions = game_record.get("actions", [])
            self.game_service._game_state["actions_history"] = actions
            
            # 保存状态
            self.game_service._save_state()
            updated_state = self.game_service.get_game_state()
            
            # 广播牌谱导入事件
            room_id = manager.connection_rooms.get(connection_id, "default")
            await self._broadcast_event(room_id, "game_record_imported", 
                                      {"game_state": updated_state}, [connection_id])
            
            await self._send_response(websocket, request_id, "import_record", True,
                                    {"game_state": updated_state}, 
                                    f"牌谱导入成功，共导入{len(actions)}个操作")
            
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"导入牌谱失败: {str(e)}")
    
    async def _handle_health_check(self, websocket, connection_id: str, data: dict, request_id: str):
        """健康检查"""
        await self._send_response(websocket, request_id, "health_check", True,
                                {"status": "healthy"}, "WebSocket服务正常运行")
    
    async def _handle_get_connections(self, websocket, connection_id: str, data: dict, request_id: str):
        """获取连接信息"""
        try:
            room_id = manager.connection_rooms.get(connection_id, "default")
            room_info = manager.get_room_info(room_id)
            all_rooms = manager.get_all_rooms()
            
            connection_info = {
                "current_connection": connection_id,
                "current_room": room_info,
                "all_rooms": [manager.get_room_info(r) for r in all_rooms],
                "total_connections": manager.get_connection_count()
            }
            
            await self._send_response(websocket, request_id, "get_connections", True,
                                    connection_info, "获取连接信息成功")
            
        except Exception as e:
            await self._send_error_response(websocket, request_id, f"获取连接信息失败: {str(e)}")


# 全局消息处理器实例
handler = MessageHandler()