import json
import zipfile
import io
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from app.models.game_record import (
    GameRecord, GameAction, PlayerGameRecord, 
    GameReplay, ActionType, MahjongCard, GangType
)
from app.services.redis_service import RedisService

class ReplayService:
    """牌谱服务类"""
    
    def __init__(self, redis_service: RedisService):
        self.redis = redis_service
        self.current_games: Dict[str, GameRecord] = {}
    
    async def start_game_recording(
        self, 
        game_id: str, 
        players: List[Dict], 
        game_mode: str = "xuezhan"
    ) -> GameRecord:
        """开始记录游戏"""
        # 创建玩家记录
        player_records = []
        for i, player in enumerate(players):
            player_record = PlayerGameRecord(
                player_id=i,
                player_name=player.get("name", f"玩家{i+1}"),
                position=i
            )
            player_records.append(player_record)
        
        # 创建游戏记录
        game_record = GameRecord(
            game_id=game_id,
            start_time=datetime.now(),
            player_count=len(players),
            game_mode=game_mode,
            players=player_records
        )
        
        # 保存到内存和Redis
        self.current_games[game_id] = game_record
        await self._save_game_record(game_record)
        
        return game_record
    
    async def record_action(
        self,
        game_id: str,
        player_id: int,
        action_type: ActionType,
        card: Optional[MahjongCard] = None,
        target_player: Optional[int] = None,
        gang_type: Optional[GangType] = None,
        missing_suit: Optional[str] = None,
        score_change: int = 0,
        game_state_snapshot: Optional[Dict] = None
    ) -> GameAction:
        """记录游戏操作"""
        if game_id not in self.current_games:
            raise ValueError(f"游戏 {game_id} 不存在或未开始记录")
        
        game_record = self.current_games[game_id]
        
        # 创建操作记录
        action = GameAction(
            sequence=len(game_record.actions) + 1,
            timestamp=datetime.now(),
            player_id=player_id,
            action_type=action_type,
            card=card,
            target_player=target_player,
            gang_type=gang_type,
            missing_suit=missing_suit,
            score_change=score_change
        )
        
        # 添加到游戏记录
        game_record.actions.append(action)
        game_record.total_actions = len(game_record.actions)
        
        # 更新玩家统计
        player_record = game_record.players[player_id]
        self._update_player_statistics(player_record, action)
        
        # 保存关键状态快照
        if game_state_snapshot and self._is_key_moment(action):
            game_record.snapshots[action.sequence] = game_state_snapshot
        
        # 保存到Redis
        await self._save_game_record(game_record)
        
        return action
    
    async def record_initial_hand(
        self, 
        game_id: str, 
        player_id: int, 
        initial_cards: List[MahjongCard]
    ):
        """记录玩家起手牌"""
        if game_id not in self.current_games:
            raise ValueError(f"游戏 {game_id} 不存在")
        
        game_record = self.current_games[game_id]
        player_record = game_record.players[player_id]
        player_record.initial_hand = initial_cards
        
        await self._save_game_record(game_record)
    
    async def record_missing_suit(
        self, 
        game_id: str, 
        player_id: int, 
        missing_suit: str
    ):
        """记录玩家定缺"""
        if game_id not in self.current_games:
            raise ValueError(f"游戏 {game_id} 不存在")
        
        game_record = self.current_games[game_id]
        player_record = game_record.players[player_id]
        player_record.missing_suit = missing_suit
        
        # 同时记录定缺操作
        await self.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.MISSING_SUIT,
            missing_suit=missing_suit
        )
    
    async def record_game_end(
        self,
        game_id: str,
        final_scores: List[int],
        winners: List[int],
        hu_types: Optional[List[str]] = None
    ):
        """记录游戏结束"""
        if game_id not in self.current_games:
            raise ValueError(f"游戏 {game_id} 不存在")
        
        game_record = self.current_games[game_id]
        game_record.end_time = datetime.now()
        game_record.duration = int((game_record.end_time - game_record.start_time).total_seconds())
        game_record.winner_count = len(winners)
        
        # 更新玩家最终结果
        for i, player_record in enumerate(game_record.players):
            player_record.final_score = final_scores[i]
            player_record.is_winner = i in winners
            
            if player_record.is_winner and hu_types:
                player_record.hu_type = hu_types[winners.index(i)]
                # 找到胡牌操作的序号
                for action in reversed(game_record.actions):
                    if action.player_id == i and action.action_type == ActionType.HU:
                        player_record.hu_sequence = action.sequence
                        break
        
        # 最终保存
        await self._save_game_record(game_record)
        
        # 从内存中移除(可选)
        # del self.current_games[game_id]
    
    async def get_game_replay(self, game_id: str) -> Optional[GameReplay]:
        """获取游戏牌谱"""
        # 先从内存查找
        if game_id in self.current_games:
            game_record = self.current_games[game_id]
        else:
            # 从Redis加载
            game_record = await self._load_game_record(game_id)
            if not game_record:
                return None
        
        replay_metadata = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "format": "xuezhan_mahjong"
        }
        
        return GameReplay(
            game_record=game_record,
            replay_metadata=replay_metadata
        )
    
    async def export_replay_json(self, game_id: str) -> str:
        """导出JSON格式牌谱"""
        replay = await self.get_game_replay(game_id)
        if not replay:
            raise ValueError(f"牌谱 {game_id} 不存在")
        
        export_data = replay.to_export_format()
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    async def export_replay_file(self, game_id: str, format: str = "json") -> bytes:
        """导出牌谱文件"""
        replay = await self.get_game_replay(game_id)
        if not replay:
            raise ValueError(f"牌谱 {game_id} 不存在")
        
        if format.lower() == "json":
            # JSON格式导出
            json_data = await self.export_replay_json(game_id)
            return json_data.encode('utf-8')
        
        elif format.lower() == "zip":
            # ZIP压缩包格式
            return await self._export_replay_zip(replay)
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    async def get_player_game_history(
        self, 
        player_name: str, 
        limit: int = 50
    ) -> List[GameRecord]:
        """获取玩家游戏历史"""
        # 从Redis搜索该玩家的游戏记录
        player_games = []
        
        game_keys = self.redis.keys("game_record:*") 
        for key in game_keys:
            try:
                game_data = self.redis.get(key)
                if game_data:
                    game_record = GameRecord.model_validate_json(game_data)
                    # 检查是否包含该玩家
                    if any(p.player_name == player_name for p in game_record.players):
                        player_games.append(game_record)
            except:
                continue
        
        # 按时间排序，返回最新的记录
        player_games.sort(key=lambda x: x.start_time, reverse=True)
        return player_games[:limit]
    
    def _update_player_statistics(self, player_record: PlayerGameRecord, action: GameAction):
        """更新玩家统计数据"""
        if action.action_type == ActionType.DRAW:
            player_record.draw_count += 1
        elif action.action_type == ActionType.DISCARD:
            player_record.discard_count += 1
        elif action.action_type == ActionType.PENG:
            player_record.peng_count += 1
        elif action.action_type == ActionType.GANG:
            player_record.gang_count += 1
    
    def _is_key_moment(self, action: GameAction) -> bool:
        """判断是否为关键时刻，需要保存状态快照"""
        key_actions = {ActionType.PENG, ActionType.GANG, ActionType.HU, ActionType.MISSING_SUIT}
        return action.action_type in key_actions
    
    async def _save_game_record(self, game_record: GameRecord):
        """保存游戏记录到Redis"""
        key = f"game_record:{game_record.game_id}"
        # 使用model_dump_json替代json方法
        json_data = game_record.model_dump_json(indent=None)
        self.redis.set(
            key, 
            json_data,
            expire=7*24*3600  # 7天过期
        )
    
    async def _load_game_record(self, game_id: str) -> Optional[GameRecord]:
        """从Redis加载游戏记录"""
        key = f"game_record:{game_id}"
        data = self.redis.get(key)
        if data:
            try:
                # 使用model_validate_json替代parse_raw
                return GameRecord.model_validate_json(data)
            except:
                return None
        return None
    
    async def _export_replay_zip(self, replay: GameReplay) -> bytes:
        """导出ZIP格式牌谱"""
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 主要牌谱文件
            game_data = replay.to_export_format()
            zf.writestr(
                f"{replay.game_record.game_id}.json",
                json.dumps(game_data, ensure_ascii=False, indent=2)
            )
            
            # 添加摘要信息
            summary = {
                "game_id": replay.game_record.game_id,
                "start_time": replay.game_record.start_time.isoformat(),
                "duration": replay.game_record.duration,
                "players": [p.player_name for p in replay.game_record.players],
                "winners": [p.player_name for p in replay.game_record.players if p.is_winner],
                "total_actions": replay.game_record.total_actions
            }
            zf.writestr(
                "summary.json",
                json.dumps(summary, ensure_ascii=False, indent=2)
            )
            
            # 添加说明文件
            readme = f"""# 血战麻将牌谱

游戏ID: {replay.game_record.game_id}
开始时间: {replay.game_record.start_time}
游戏时长: {replay.game_record.duration}秒
玩家人数: {replay.game_record.player_count}

## 文件说明
- {replay.game_record.game_id}.json: 完整牌谱数据
- summary.json: 游戏摘要信息
- README.md: 说明文件

## 牌谱格式说明
牌谱采用JSON格式存储，包含完整的游戏操作序列和玩家信息。
可以使用支持的工具导入并回放游戏过程。
"""
            zf.writestr("README.md", readme)
        
        buffer.seek(0)
        return buffer.read() 