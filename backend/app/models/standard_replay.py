"""
标准化牌谱格式的数据模型
支持新格式文件 model/first_hand/sample_mahjong_game_final.json
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class StandardActionType(str, Enum):
    """标准格式的动作类型"""
    DRAW = "draw"           # 摸牌
    DISCARD = "discard"     # 弃牌
    PENG = "peng"          # 碰牌
    GANG = "gang"          # 杠牌
    JIAGANG = "jiagang"    # 加杠
    HU = "hu"              # 胡牌
    ZIMO = "zimo"          # 自摸
    PASS = "pass"          # 过牌

class InitialHandData(BaseModel):
    """初始手牌数据"""
    tiles: List[str] = Field(..., description="牌的中文字符串列表，如['1万','2条']")
    count: int = Field(..., description="牌的数量")
    source: str = Field(..., description="数据来源：known/deduced")
    note: str = Field(..., description="备注说明")

class StandardGameAction(BaseModel):
    """标准格式的游戏动作"""
    sequence: int = Field(..., description="动作序号")
    player_id: int = Field(..., description="玩家ID")
    type: StandardActionType = Field(..., description="动作类型")
    tile: Optional[str] = Field(None, description="相关的牌，中文字符串")
    target_player: Optional[int] = Field(None, description="目标玩家(碰杠时)")
    gang_type: Optional[str] = Field(None, description="杠牌类型")

class MeldData(BaseModel):
    """面子数据（碰、杠等）"""
    type: str = Field(..., description="面子类型：peng/gang/jiagang")
    tile: List[str] = Field(..., description="牌列表")

class FinalHandData(BaseModel):
    """最终手牌数据"""
    hand: List[str] = Field(default_factory=list, description="最终手牌")
    melds: List[MeldData] = Field(default_factory=list, description="面子列表")

class GameInfo(BaseModel):
    """游戏基本信息"""
    game_id: str = Field(..., description="游戏ID")
    description: str = Field(default="", description="游戏描述")
    source: str = Field(default="", description="数据来源")
    version: str = Field(default="", description="版本信息")
    original_file: Optional[str] = Field(None, description="原始文件路径")

class StandardReplayData(BaseModel):
    """标准化牌谱数据模型"""
    game_info: GameInfo = Field(..., description="游戏基本信息")
    mjtype: str = Field(default="xuezhan_daodi", description="麻将类型")
    misssuit: Dict[str, str] = Field(default_factory=dict, description="定缺信息")
    dong: str = Field(default="0", description="庄家")
    game_settings: Dict[str, Any] = Field(default_factory=dict, description="游戏设置")
    initial_hands: Dict[str, InitialHandData] = Field(..., description="初始手牌")
    actions: List[StandardGameAction] = Field(default_factory=list, description="游戏动作序列")
    final_hands: Dict[str, FinalHandData] = Field(default_factory=dict, description="最终手牌")

class TileConverter:
    """牌面转换工具"""
    
    @staticmethod
    def chinese_to_english_suit(chinese_tile: str) -> tuple:
        """
        将中文牌名转换为英文格式
        例：'1万' -> ('wan', 1)
        """
        if not chinese_tile or len(chinese_tile) < 2:
            raise ValueError(f"无效的牌名: {chinese_tile}")
        
        # 解析数字和花色
        try:
            value = int(chinese_tile[0])
        except ValueError:
            raise ValueError(f"无效的牌值: {chinese_tile[0]}")
        
        suit_char = chinese_tile[1]
        suit_mapping = {
            '万': 'wan',
            '条': 'tiao', 
            '筒': 'tong'
        }
        
        suit = suit_mapping.get(suit_char)
        if not suit:
            raise ValueError(f"无效的花色: {suit_char}")
        
        return suit, value
    
    @staticmethod
    def english_to_chinese_tile(suit: str, value: int) -> str:
        """
        将英文格式转换为中文牌名
        例：('wan', 1) -> '1万'
        """
        suit_mapping = {
            'wan': '万',
            'tiao': '条',
            'tong': '筒'
        }
        
        chinese_suit = suit_mapping.get(suit, suit)
        return f"{value}{chinese_suit}"
    
    @staticmethod
    def to_mahjong_card_dict(chinese_tile: str, card_id: int = None) -> Dict[str, Any]:
        """
        将中文牌名转换为后台MahjongCard格式的字典
        """
        suit, value = TileConverter.chinese_to_english_suit(chinese_tile)
        
        if card_id is None:
            # 生成唯一ID
            card_id = hash(f"{suit}_{value}_{chinese_tile}") % 100000
        
        return {
            "id": card_id,
            "suit": suit,
            "value": value,
            "display_name": chinese_tile
        }