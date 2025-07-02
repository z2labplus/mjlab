from enum import Enum
from typing import List, Optional, Dict, Set, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TileType(str, Enum):
    """麻将牌类型"""
    WAN = "wan"    # 万
    TIAO = "tiao"  # 条
    TONG = "tong"  # 筒


class MeldType(str, Enum):
    """面子类型"""
    PENG = "peng"  # 碰
    GANG = "gang"  # 杠
    CHI = "chi"    # 吃


class GangType(str, Enum):
    """杠牌类型"""
    MING_GANG = "ming_gang"  # 明杠（直杠）
    AN_GANG = "an_gang"      # 暗杠
    JIA_GANG = "jia_gang"    # 加杠


class Tile(BaseModel):
    """麻将牌"""
    type: TileType
    value: int = Field(..., ge=1, le=9)  # 1-9
    id: Optional[str] = None  # 牌的唯一标识
    
    def __str__(self) -> str:
        """转换为字符串表示"""
        type_map = {
            TileType.WAN: "万",
            TileType.TIAO: "条",
            TileType.TONG: "筒"
        }
        return f"{self.value}{type_map[self.type]}"
    
    @classmethod
    def from_code(cls, code: int) -> "Tile":
        """从数字编码创建麻将牌"""
        if 1 <= code <= 9:
            return cls(type=TileType.WAN, value=code)
        elif 11 <= code <= 19:
            return cls(type=TileType.TIAO, value=code - 10)
        elif 21 <= code <= 29:
            return cls(type=TileType.TONG, value=code - 20)
        else:
            raise ValueError(f"Invalid tile code: {code}")
    
    def to_code(self) -> int:
        """转换为数字编码"""
        if self.type == TileType.WAN:
            return self.value
        elif self.type == TileType.TIAO:
            return self.value + 10
        elif self.type == TileType.TONG:
            return self.value + 20
        else:
            raise ValueError(f"Invalid tile type: {self.type}")


class Meld(BaseModel):
    """面子"""
    id: Optional[str] = None  # 面子的唯一标识
    type: MeldType
    tiles: List[Tile]
    exposed: bool = True
    gang_type: Optional[GangType] = None  # 杠牌类型
    source_player: Optional[int] = None  # 来源玩家ID
    original_peng_id: Optional[str] = None  # 加杠时原碰牌ID
    timestamp: Optional[float] = Field(default_factory=lambda: datetime.now().timestamp())


class HandTiles(BaseModel):
    """玩家手牌"""
    tiles: Optional[List[Tile]] = None  # 允许为None（其他玩家的手牌）
    tile_count: Optional[int] = 0  # 手牌数量（用于其他玩家）
    melds: List[Meld] = []
    # 胜利状态相关字段
    is_winner: Optional[bool] = None
    win_type: Optional[str] = None  # "zimo"自摸 或 "dianpao"点炮
    win_tile: Optional[Tile] = None
    dianpao_player_id: Optional[int] = None  # 点炮玩家ID
    missing_suit: Optional[str] = None  # 定缺花色
    
    class Config:
        # 允许额外字段，保持向后兼容
        extra = "allow"


class PlayerAction(BaseModel):
    """玩家动作"""
    player_id: int
    action_type: Optional[str] = None  # 某些历史记录可能使用 'type' 字段
    type: Optional[str] = None  # 兼容旧格式
    tiles: Optional[List[Tile]] = []  # 改为可选，某些动作可能没有
    tile: Optional[Tile] = None  # 单个牌的动作
    source_player: Optional[int] = None  # 来源玩家
    source_player_id: Optional[int] = None  # 兼容字段
    timestamp: Optional[float] = Field(default_factory=lambda: datetime.now().timestamp())
    
    class Config:
        # 允许额外字段，保持向后兼容
        extra = "allow"


class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    player_hands: Dict[str, HandTiles] = {}
    current_player: int = 0
    discarded_tiles: List[Tile] = []
    player_discarded_tiles: Dict[str, List[Tile]] = {}
    actions_history: List[PlayerAction] = []
    game_started: bool = False
    last_action: Optional[Dict[str, Any]] = None
    show_all_hands: Optional[bool] = None  # 是否显示所有玩家手牌
    
    class Config:
        # 允许额外字段，保持向后兼容
        extra = "allow"
    
    def get_visible_tiles(self) -> List[Tile]:
        """获取所有可见的牌"""
        visible = []
        visible.extend(self.discarded_tiles)
        
        for hand in self.player_hands.values():
            for meld in hand.melds:
                if meld.exposed:
                    visible.extend(meld.tiles)
        
        return visible
    
    def calculate_remaining_tiles(self) -> int:
        """计算剩余牌数（包括所有已使用的牌）"""
        total_tiles = 108  # 标准麻将总牌数
        used_tiles = 0
        
        # 计算所有玩家手牌数量
        for hand in self.player_hands.values():
            # 使用tile_count字段，如果不存在则使用tiles长度
            if hand.tile_count is not None:
                used_tiles += hand.tile_count
            elif hand.tiles is not None:
                used_tiles += len(hand.tiles)
            
            # 计算碰牌杠牌数量
            for meld in hand.melds:
                used_tiles += len(meld.tiles)
        
        # 计算弃牌数量
        used_tiles += len(self.discarded_tiles)
        
        return max(0, total_tiles - used_tiles)

    def calculate_visible_remaining_tiles(self) -> int:
        """计算基于可见牌的剩余牌数"""
        total_tiles = 108
        used_tiles = 0
        
        # 计算所有玩家手牌数量
        for player_id, hand in self.player_hands.items():
            # 只计算"我"（player_id=0）的手牌
            if player_id == "0":
                if hand.tile_count is not None:
                    used_tiles += hand.tile_count
                elif hand.tiles is not None:
                    used_tiles += len(hand.tiles)
            
            # 计算碰牌杠牌数量
            for meld in hand.melds:
                if meld.type == MeldType.GANG and meld.gang_type == GangType.AN_GANG:
                    # 暗杠：只计算"我"的暗杠
                    if player_id == "0":
                        used_tiles += len(meld.tiles)
                else:
                    # 明牌（碰牌、明杠）：所有玩家的都要计算
                    used_tiles += len(meld.tiles)
        
        # 计算弃牌数量 - 所有玩家的弃牌都是可见的
        used_tiles += len(self.discarded_tiles)
        
        return max(0, total_tiles - used_tiles)

    def calculate_remaining_tiles_by_type(self) -> Dict[str, int]:
        """计算每种牌的剩余数量（基于可见牌）"""
        # 初始化每种牌的数量为4张
        remaining_counts = {}
        
        # 初始化万、条、筒 1-9 各4张
        for tile_type in [TileType.WAN, TileType.TIAO, TileType.TONG]:
            for value in range(1, 10):
                remaining_counts[f"{tile_type}-{value}"] = 4
        
        # 收集所有已使用的可见牌
        used_tiles = []
        
        # 收集玩家的手牌和碰杠牌
        for player_id, hand in self.player_hands.items():
            # 只收集"我"的手牌
            if player_id == "0" and hand.tiles is not None:
                used_tiles.extend(hand.tiles)
            
            # 收集所有玩家的碰杠牌（除了暗杠）
            for meld in hand.melds:
                if meld.type == MeldType.GANG and meld.gang_type == GangType.AN_GANG:
                    if player_id == "0":  # 只收集"我"的暗杠
                        used_tiles.extend(meld.tiles)
                else:  # 收集所有明牌
                    used_tiles.extend(meld.tiles)
        
        # 收集弃牌
        used_tiles.extend(self.discarded_tiles)
        
        # 更新剩余数量
        for tile in used_tiles:
            key = f"{tile.type}-{tile.value}"
            if key in remaining_counts:
                remaining_counts[key] = max(0, remaining_counts[key] - 1)
        
        return remaining_counts


class AnalysisResult(BaseModel):
    """分析结果"""
    recommended_discard: Optional[Tile] = None
    discard_scores: Dict[str, float] = {}
    listen_tiles: List[Tile] = []
    win_probability: float = 0.0
    remaining_tiles_count: Dict[int, int] = {}
    suggestions: List[str] = []


class GameRequest(BaseModel):
    """游戏请求"""
    game_state: GameState
    target_player: int = 0  # 目标玩家ID（通常是自己）


class GameResponse(BaseModel):
    """游戏响应"""
    success: bool
    analysis: Optional[AnalysisResult] = None
    message: str = "" 


# 操作相关模型
class TileOperationRequest(BaseModel):
    """牌操作请求"""
    player_id: int = Field(..., ge=0, le=3)
    operation_type: str  # discard, peng, gang, hand
    tile: Tile
    source_player_id: Optional[int] = None
    game_id: Optional[str] = None  # 添加游戏ID字段


class GameOperationResponse(BaseModel):
    """游戏操作响应"""
    success: bool
    message: str
    game_state: Optional[Dict] = None


class GameStateRequest(BaseModel):
    """游戏状态请求"""
    game_state: GameState


class ResetGameResponse(BaseModel):
    """重置游戏响应"""
    success: bool
    message: str