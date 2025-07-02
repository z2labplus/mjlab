"""
标准化牌谱格式解析服务
支持直接读取和处理新格式文件 model/first_hand/sample_mahjong_game_final.json
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.models.standard_replay import (
    StandardReplayData, StandardGameAction, InitialHandData, 
    TileConverter, StandardActionType
)
from app.models.game_record import (
    GameRecord, GameAction, PlayerGameRecord, 
    ActionType, MahjongCard, GangType
)
from app.services.redis_service import RedisService

class StandardReplayService:
    """标准化牌谱服务"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.tile_converter = TileConverter()
    
    def load_standard_replay_file(self, file_path: str) -> StandardReplayData:
        """加载标准格式牌谱文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 使用Pydantic验证和解析数据
            standard_replay = StandardReplayData(**data)
            return standard_replay
            
        except Exception as e:
            raise ValueError(f"加载标准牌谱文件失败: {e}")
    
    def convert_standard_to_backend_format(self, standard_replay: StandardReplayData) -> Dict[str, Any]:
        """将标准格式转换为后台GameRecord格式"""
        
        # 创建玩家记录
        players = []
        for player_id_str, hand_data in standard_replay.initial_hands.items():
            player_id = int(player_id_str)
            
            # 转换初始手牌
            initial_cards = []
            card_id_counter = player_id * 1000  # 确保每个玩家的牌ID不重复
            
            for tile_str in hand_data.tiles:
                try:
                    card_dict = self.tile_converter.to_mahjong_card_dict(tile_str, card_id_counter)
                    card = MahjongCard(**card_dict)
                    initial_cards.append(card)
                    card_id_counter += 1
                except Exception as e:
                    print(f"⚠️ 转换牌失败: {tile_str}, 错误: {e}")
            
            # 创建玩家记录
            player_record = PlayerGameRecord(
                player_id=player_id,
                player_name=f"玩家{player_id + 1}",
                position=player_id,
                initial_hand=initial_cards,
                final_score=0,  # 暂时设为0，后续可以从final_hands推导
                is_winner=False,  # 暂时设为False
                draw_count=0,
                discard_count=0,
                peng_count=0,
                gang_count=0
            )
            
            players.append(player_record)
        
        # 转换游戏动作
        actions = []
        for action_data in standard_replay.actions:
            try:
                # 转换动作类型
                action_type = self._convert_action_type(action_data.type)
                
                # 转换牌信息
                card = None
                if action_data.tile:
                    card_dict = self.tile_converter.to_mahjong_card_dict(action_data.tile)
                    card = MahjongCard(**card_dict)
                
                # 创建动作记录
                game_action = GameAction(
                    sequence=action_data.sequence,
                    timestamp=datetime.now(),  # 使用当前时间，实际应该从数据中获取
                    player_id=action_data.player_id,
                    action_type=action_type,
                    card=card,
                    target_player=action_data.target_player,
                    gang_type=self._convert_gang_type(action_data.gang_type) if action_data.gang_type else None
                )
                
                actions.append(game_action)
                
                # 更新玩家统计
                player = players[action_data.player_id]
                if action_type == ActionType.DRAW:
                    player.draw_count += 1
                elif action_type == ActionType.DISCARD:
                    player.discard_count += 1
                elif action_type == ActionType.PENG:
                    player.peng_count += 1
                elif action_type == ActionType.GANG:
                    player.gang_count += 1
                    
            except Exception as e:
                print(f"⚠️ 转换动作失败: {action_data}, 错误: {e}")
        
        # 创建游戏记录
        game_record = GameRecord(
            game_id=standard_replay.game_info.game_id,
            start_time=datetime.now() - timedelta(minutes=30),
            end_time=datetime.now(),
            duration=30 * 60,  # 30分钟
            players=players,
            actions=actions,
            total_actions=len(actions),
            winner_count=0,  # 后续可以从final_hands计算
            game_mode=standard_replay.mjtype,
            metadata={
                "source": "standard_format",
                "original_file": standard_replay.game_info.original_file,
                "mjtype": standard_replay.mjtype,
                "misssuit": standard_replay.misssuit,
                "dong": standard_replay.dong,
                "description": standard_replay.game_info.description
            }
        )
        
        return {
            "game_record": game_record,
            "replay_metadata": {
                "format": "standard",
                "generated_at": datetime.now().isoformat(),
                "source_file": standard_replay.game_info.original_file
            }
        }
    
    def _convert_action_type(self, standard_type: StandardActionType) -> ActionType:
        """转换动作类型"""
        mapping = {
            StandardActionType.DRAW: ActionType.DRAW,
            StandardActionType.DISCARD: ActionType.DISCARD,
            StandardActionType.PENG: ActionType.PENG,
            StandardActionType.GANG: ActionType.GANG,
            StandardActionType.JIAGANG: ActionType.GANG,  # 加杠也映射为GANG
            StandardActionType.HU: ActionType.HU,
            StandardActionType.ZIMO: ActionType.HU,  # 自摸也映射为HU
            StandardActionType.PASS: ActionType.PASS,
        }
        
        return mapping.get(standard_type, ActionType.PASS)
    
    def _convert_gang_type(self, gang_type_str: str) -> Optional[GangType]:
        """转换杠牌类型"""
        if not gang_type_str:
            return None
            
        mapping = {
            "angang": GangType.AN_GANG,
            "minggang": GangType.MING_GANG,
            "jiagang": GangType.JIA_GANG,
        }
        
        return mapping.get(gang_type_str.lower(), GangType.MING_GANG)
    
    async def import_standard_replay_to_system(self, file_path: str, target_game_id: str = None) -> str:
        """
        将标准格式牌谱导入到后台系统
        
        Args:
            file_path: 标准格式文件路径
            target_game_id: 目标游戏ID，如果不指定则使用文件中的game_id
            
        Returns:
            游戏ID
        """
        print(f"📥 导入标准格式牌谱: {file_path}")
        
        # 加载标准格式数据
        standard_replay = self.load_standard_replay_file(file_path)
        
        # 确定游戏ID
        game_id = target_game_id or standard_replay.game_info.game_id
        print(f"🎮 游戏ID: {game_id}")
        
        # 转换为后台格式
        backend_data = self.convert_standard_to_backend_format(standard_replay)
        game_record = backend_data["game_record"]
        
        # 更新游戏ID
        game_record.game_id = game_id
        
        # 存储到Redis
        game_record_key = f"game_record:{game_id}"
        
        # 将GameRecord转换为可序列化的字典
        game_record_dict = game_record.model_dump()
        
        # 处理datetime字段序列化
        serialized_dict = self._serialize_datetime_fields(game_record_dict)
        
        # 存储到Redis
        self.redis.set(game_record_key, json.dumps(serialized_dict, ensure_ascii=False))
        
        print(f"✅ 标准格式牌谱已导入系统: {game_id}")
        print(f"📊 玩家数: {len(game_record.players)}")
        print(f"📊 动作数: {len(game_record.actions)}")
        
        return game_id
    
    def _serialize_datetime_fields(self, data: Any) -> Any:
        """递归处理datetime字段，转换为ISO字符串"""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: self._serialize_datetime_fields(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_datetime_fields(item) for item in data]
        else:
            return data
    
    async def get_available_standard_replays(self) -> List[Dict[str, Any]]:
        """获取可用的标准格式牌谱列表"""
        
        # 预定义的标准格式文件列表
        standard_files = [
            {
                "file_path": "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json",
                "name": "推导算法生成的完整牌谱",
                "description": "通过初始手牌推导算法生成的标准格式牌谱"
            }
        ]
        
        available_replays = []
        
        for file_info in standard_files:
            file_path = file_info["file_path"]
            if Path(file_path).exists():
                try:
                    # 读取基本信息
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    game_info = data.get("game_info", {})
                    
                    available_replays.append({
                        "game_id": game_info.get("game_id", "unknown"),
                        "name": file_info["name"],
                        "description": file_info["description"],
                        "file_path": file_path,
                        "mjtype": data.get("mjtype", "xuezhan_daodi"),
                        "player_count": len(data.get("initial_hands", {})),
                        "action_count": len(data.get("actions", [])),
                        "source": game_info.get("source", "unknown"),
                        "version": game_info.get("version", "unknown")
                    })
                    
                except Exception as e:
                    print(f"⚠️ 读取标准文件信息失败: {file_path}, 错误: {e}")
        
        return available_replays