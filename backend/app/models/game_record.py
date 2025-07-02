from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Union
from datetime import datetime
from enum import Enum

class ActionType(str, Enum):
    """操作类型"""
    DRAW = "draw"           # 摸牌
    DISCARD = "discard"     # 弃牌
    PENG = "peng"          # 碰牌
    GANG = "gang"          # 杠牌
    HU = "hu"              # 胡牌
    PASS = "pass"          # 过牌
    MISSING_SUIT = "missing_suit"  # 定缺

class GangType(str, Enum):
    """杠牌类型"""
    MING_GANG = "ming_gang"     # 明杠(直杠)
    AN_GANG = "an_gang"         # 暗杠
    JIA_GANG = "jia_gang"       # 加杠

class MahjongCard(BaseModel):
    """麻将牌"""
    id: int = Field(..., description="牌的ID")
    suit: str = Field(..., description="花色: wan/tiao/tong")
    value: int = Field(..., ge=1, le=9, description="牌面值1-9")
    
    def __str__(self):
        suit_names = {"wan": "万", "tiao": "条", "tong": "筒"}
        return f"{self.value}{suit_names.get(self.suit, self.suit)}"

class GameAction(BaseModel):
    """游戏操作记录"""
    sequence: int = Field(..., description="操作序号")
    timestamp: datetime = Field(default_factory=datetime.now, description="操作时间")
    player_id: int = Field(..., description="操作玩家ID (0-3)")
    action_type: ActionType = Field(..., description="操作类型")
    
    # 操作相关数据
    card: Optional[MahjongCard] = Field(None, description="相关的牌")
    target_player: Optional[int] = Field(None, description="目标玩家(碰杠时)")
    gang_type: Optional[GangType] = Field(None, description="杠牌类型")
    missing_suit: Optional[str] = Field(None, description="定缺花色")
    
    # 操作结果
    is_success: bool = Field(True, description="操作是否成功")
    score_change: int = Field(0, description="分数变化")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "sequence": 1,
                "player_id": 0,
                "action_type": "discard",
                "card": {"id": 1, "suit": "wan", "value": 1},
                "is_success": True,
                "score_change": 0
            }
        }
    )

class PlayerGameRecord(BaseModel):
    """玩家游戏记录"""
    player_id: int = Field(..., description="玩家ID")
    player_name: str = Field(..., description="玩家昵称")
    position: int = Field(..., ge=0, le=3, description="座位号")
    
    # 初始状态
    initial_hand: List[MahjongCard] = Field(default_factory=list, description="起手牌")
    missing_suit: Optional[str] = Field(None, description="定缺花色")
    
    # 游戏结果
    final_score: int = Field(0, description="最终得分")
    is_winner: bool = Field(False, description="是否胡牌")
    hu_type: Optional[str] = Field(None, description="胡牌类型")
    hu_sequence: Optional[int] = Field(None, description="胡牌时的操作序号")
    
    # 统计数据
    draw_count: int = Field(0, description="摸牌次数")
    discard_count: int = Field(0, description="弃牌次数")
    peng_count: int = Field(0, description="碰牌次数")
    gang_count: int = Field(0, description="杠牌次数")

class GameRecord(BaseModel):
    """完整游戏记录"""
    game_id: str = Field(..., description="游戏ID")
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[int] = Field(None, description="游戏时长(秒)")
    
    # 游戏设置
    player_count: int = Field(4, description="玩家数量")
    game_mode: str = Field("xuezhan", description="游戏模式")
    
    # 玩家信息
    players: List[PlayerGameRecord] = Field(..., description="玩家记录")
    
    # 操作序列
    actions: List[GameAction] = Field(default_factory=list, description="所有操作记录")
    
    # 游戏状态快照(关键时刻)
    snapshots: Dict[int, Dict] = Field(default_factory=dict, description="游戏状态快照")
    
    # 统计信息
    total_actions: int = Field(0, description="总操作数")
    winner_count: int = Field(0, description="胡牌人数")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "game_id": "game_123456",
                "player_count": 4,
                "game_mode": "xuezhan",
                "players": [],
                "actions": [],
                "total_actions": 0,
                "winner_count": 0
            }
        }
    )

class GameReplay(BaseModel):
    """牌谱回放数据"""
    game_record: GameRecord = Field(..., description="游戏记录")
    replay_metadata: Dict = Field(default_factory=dict, description="回放元数据")
    
    def to_export_format(self) -> Dict:
        """转换为导出格式"""
        return {
            "game_info": {
                "game_id": self.game_record.game_id,
                "start_time": self.game_record.start_time.isoformat(),
                "end_time": self.game_record.end_time.isoformat() if self.game_record.end_time else None,
                "duration": self.game_record.duration,
                "player_count": self.game_record.player_count,
                "game_mode": self.game_record.game_mode
            },
            "players": [
                {
                    "id": p.player_id,
                    "name": p.player_name,
                    "position": p.position,
                    "initial_hand": [str(card) for card in p.initial_hand],
                    "missing_suit": p.missing_suit,
                    "final_score": p.final_score,
                    "is_winner": p.is_winner,
                    "statistics": {
                        "draw_count": p.draw_count,
                        "discard_count": p.discard_count,
                        "peng_count": p.peng_count,
                        "gang_count": p.gang_count
                    }
                }
                for p in self.game_record.players
            ],
            "actions": [
                {
                    "sequence": action.sequence,
                    "timestamp": action.timestamp.isoformat(),
                    "player_id": action.player_id,
                    "action_type": action.action_type,
                    "card": str(action.card) if action.card else None,
                    "target_player": action.target_player,
                    "gang_type": action.gang_type,
                    "score_change": action.score_change
                }
                for action in self.game_record.actions
            ],
            "metadata": self.replay_metadata
        } 