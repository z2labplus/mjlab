#!/usr/bin/env python3
"""
SichuanMahjongKit Core Data Structures
血战到底麻将库核心数据结构
"""

from typing import List, Union, Optional, Dict, Any
from enum import Enum
import re


class SuitType(Enum):
    """花色类型"""
    WAN = 'm'      # 万
    TIAO = 's'     # 条
    TONG = 'p'     # 筒


class Tile:
    """单张麻将牌 - 参考日本库设计"""
    def __init__(self, suit: SuitType, value: int):
        if not isinstance(suit, SuitType):
            raise ValueError(f"Invalid suit type: {suit}")
        if not (1 <= value <= 9):
            raise ValueError(f"Invalid tile value: {value}")
        
        self.suit = suit
        self.value = value
        self.id = self._calculate_id()
    
    def _calculate_id(self) -> int:
        """计算牌的唯一ID (0-26)"""
        base = {'m': 0, 's': 9, 'p': 18}
        return base[self.suit.value] + (self.value - 1)
    
    def __str__(self) -> str:
        return f"{self.value}{self.suit.value}"
    
    def __repr__(self) -> str:
        return f"Tile({self.suit}, {self.value})"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, Tile) and self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __lt__(self, other) -> bool:
        return isinstance(other, Tile) and self.id < other.id
    
    @classmethod
    def from_string(cls, tile_str: str) -> 'Tile':
        """从字符串创建牌 例: '1m', '9s', '5p'"""
        if len(tile_str) != 2:
            raise ValueError(f"Invalid tile string: {tile_str}")
        
        value = int(tile_str[0])
        suit_char = tile_str[1]
        
        for suit in SuitType:
            if suit.value == suit_char:
                return cls(suit, value)
        
        raise ValueError(f"Invalid suit character: {suit_char}")
    
    @classmethod
    def from_chinese(cls, tile_str: str) -> 'Tile':
        """从中文字符串创建牌 例: '1万', '9条', '5筒'"""
        if len(tile_str) != 2:
            raise ValueError(f"Invalid Chinese tile string: {tile_str}")
        
        value = int(tile_str[0])
        suit_char = tile_str[1]
        
        suit_map = {'万': 'm', '条': 's', '筒': 'p'}
        if suit_char not in suit_map:
            raise ValueError(f"Invalid Chinese suit character: {suit_char}")
        
        return cls.from_string(f"{value}{suit_map[suit_char]}")


class TilesConverter:
    """牌的格式转换器 - 支持多种表示方法"""
    
    @staticmethod
    def string_to_tiles(tiles_string: str) -> List[Tile]:
        """
        字符串转Tile列表
        例: "123m456s789p" -> [Tile(WAN,1), Tile(WAN,2), ...]
        """
        tiles = []
        current_numbers = []
        
        for char in tiles_string:
            if char.isdigit():
                current_numbers.append(int(char))
            elif char in ['m', 's', 'p']:
                suit_type = SuitType(char)
                for num in current_numbers:
                    tiles.append(Tile(suit_type, num))
                current_numbers = []
        
        return sorted(tiles)
    
    @staticmethod
    def tiles_to_string(tiles: List[Tile]) -> str:
        """Tile列表转字符串表示"""
        # 按花色分组
        suits_tiles = {'m': [], 's': [], 'p': []}
        
        for tile in tiles:
            suits_tiles[tile.suit.value].append(tile.value)
        
        # 排序并构建字符串
        result = []
        for suit_char in ['m', 's', 'p']:
            if suits_tiles[suit_char]:
                suits_tiles[suit_char].sort()
                numbers = ''.join(str(v) for v in suits_tiles[suit_char])
                result.append(f"{numbers}{suit_char}")
        
        return ''.join(result)
    
    @staticmethod
    def string_to_27_array(tiles_string: str) -> List[int]:
        """
        字符串转27位频率数组
        例: "123m456s789p" -> [1,1,1,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0]
        """
        tiles_array = [0] * 27
        current_numbers = []
        
        for char in tiles_string:
            if char.isdigit():
                current_numbers.append(int(char))
            elif char in ['m', 's', 'p']:
                suit_type = SuitType(char)
                for num in current_numbers:
                    tile = Tile(suit_type, num)
                    tiles_array[tile.id] += 1
                current_numbers = []
        
        return tiles_array
    
    @staticmethod
    def tiles_to_27_array(tiles: List[Tile]) -> List[int]:
        """Tile列表转27位频率数组"""
        tiles_array = [0] * 27
        for tile in tiles:
            tiles_array[tile.id] += 1
        return tiles_array
    
    @staticmethod
    def array_27_to_string(tiles_array: List[int]) -> str:
        """27位数组转字符串表示"""
        result = []
        suits = [('m', 0), ('s', 9), ('p', 18)]
        
        for suit_char, offset in suits:
            suit_tiles = []
            for i in range(9):
                count = tiles_array[offset + i]
                suit_tiles.extend([str(i + 1)] * count)
            
            if suit_tiles:
                result.append(''.join(suit_tiles) + suit_char)
        
        return ''.join(result)
    
    @staticmethod
    def array_27_to_tiles(tiles_array: List[int]) -> List[Tile]:
        """27位数组转Tile列表"""
        tiles = []
        suits = [('m', 0), ('s', 9), ('p', 18)]
        
        for suit_char, offset in suits:
            suit_type = SuitType(suit_char)
            for i in range(9):
                count = tiles_array[offset + i]
                for _ in range(count):
                    tiles.append(Tile(suit_type, i + 1))
        
        return tiles
    
    @staticmethod
    def chinese_to_tiles(tiles_list: List[str]) -> List[Tile]:
        """中文牌列表转Tile列表 例: ['1万', '2条', '3筒']"""
        tiles = []
        for tile_str in tiles_list:
            tiles.append(Tile.from_chinese(tile_str))
        return sorted(tiles)


class MeldType(Enum):
    """副露类型"""
    PENG = "peng"        # 碰
    GANG = "gang"        # 明杠
    JIAGANG = "jiagang"  # 加杠


class Meld:
    """副露(碰、杠)"""
    def __init__(self, meld_type: MeldType, tiles: List[Tile], target_player: Optional[int] = None):
        self.meld_type = meld_type
        self.tiles = tiles
        self.target_player = target_player
        
        # 验证副露的有效性
        if meld_type == MeldType.PENG and len(tiles) != 3:
            raise ValueError("碰牌必须是3张相同的牌")
        elif meld_type in [MeldType.GANG, MeldType.JIAGANG] and len(tiles) != 4:
            raise ValueError("杠牌必须是4张相同的牌")
        
        if not all(tile == tiles[0] for tile in tiles):
            raise ValueError("副露的牌必须完全相同")
    
    def __str__(self) -> str:
        return f"{self.meld_type.value}:{TilesConverter.tiles_to_string(self.tiles)}"
    
    def __repr__(self) -> str:
        return f"Meld({self.meld_type}, {self.tiles}, {self.target_player})"
    
    def is_kong(self) -> bool:
        """是否为杭"""
        return self.meld_type in [MeldType.GANG, MeldType.JIAGANG]
    
    def get_suit(self) -> SuitType:
        """获取花色"""
        return self.tiles[0].suit
    
    def get_value(self) -> int:
        """获取牌值"""
        return self.tiles[0].value
    
    @property
    def type(self) -> MeldType:
        """副露类型属性（兼容性）"""
        return self.meld_type


class PlayerState:
    """玩家状态"""
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand_tiles: List[Tile] = []
        self.melds: List[Meld] = []
        self.discards: List[Tile] = []
        self.missing_suit: Optional[SuitType] = None
        self.is_ting = False
        self.is_winning = False
        self.winning_tile: Optional[Tile] = None
        self.is_self_draw = False
    
    def add_tile(self, tile: Tile):
        """添加手牌"""
        self.hand_tiles.append(tile)
        self.hand_tiles.sort()
    
    def remove_tile(self, tile: Tile) -> bool:
        """移除手牌"""
        if tile in self.hand_tiles:
            self.hand_tiles.remove(tile)
            return True
        return False
    
    def add_meld(self, meld: Meld):
        """添加副露"""
        self.melds.append(meld)
    
    def add_discard(self, tile: Tile):
        """添加弃牌"""
        self.discards.append(tile)
    
    def set_missing_suit(self, suit: SuitType):
        """设置定缺花色"""
        self.missing_suit = suit
    
    def get_hand_27_array(self) -> List[int]:
        """获取手牌的27位数组表示"""
        return TilesConverter.tiles_to_27_array(self.hand_tiles)
    
    def get_all_tiles_count(self) -> int:
        """获取所有牌的数量(手牌+副露)"""
        meld_count = sum(len(meld.tiles) for meld in self.melds)
        return len(self.hand_tiles) + meld_count
    
    def is_flower_pig(self) -> bool:
        """检查是否为花猪(有三门花色)"""
        suits = set()
        for tile in self.hand_tiles:
            suits.add(tile.suit)
        for meld in self.melds:
            for tile in meld.tiles:
                suits.add(tile.suit)
        return len(suits) >= 3
    
    def __str__(self) -> str:
        hand_str = TilesConverter.tiles_to_string(self.hand_tiles)
        meld_str = " ".join(str(meld) for meld in self.melds)
        return f"Player{self.player_id}: {hand_str} | {meld_str}"


if __name__ == "__main__":
    # 测试代码
    print("=== SichuanMahjongKit Core Test ===")
    
    # 测试Tile创建
    tile1 = Tile(SuitType.WAN, 1)
    tile2 = Tile.from_string("1m")
    tile3 = Tile.from_chinese("1万")
    
    print(f"Tile test: {tile1} == {tile2} == {tile3}: {tile1 == tile2 == tile3}")
    
    # 测试TilesConverter
    tiles_str = "123m456s789p"
    tiles = TilesConverter.string_to_tiles(tiles_str)
    print(f"String to tiles: {tiles_str} -> {tiles}")
    
    back_str = TilesConverter.tiles_to_string(tiles)
    print(f"Tiles to string: {tiles} -> {back_str}")
    
    # 测试27位数组
    array27 = TilesConverter.string_to_27_array(tiles_str)
    print(f"27-array: {array27}")
    
    # 测试PlayerState
    player = PlayerState(0)
    for tile in tiles:
        player.add_tile(tile)
    
    print(f"Player state: {player}")
    print(f"Hand 27-array: {player.get_hand_27_array()}")