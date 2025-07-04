#!/usr/bin/env python3
"""
Fixed and simplified validator for Sichuan Mahjong
简单可靠的麻将验证器
"""

from typing import List, Set, Tuple, Optional, Dict, Any
from .core import Tile, TilesConverter, SuitType, PlayerState, MeldType


class WinValidator:
    """胡牌验证器 - 血战到底规则"""
    
    @staticmethod
    def is_winning_hand(tiles: List[Tile], melds: List = None) -> bool:
        """检查是否为胡牌手牌"""
        if melds is None:
            melds = []
        
        # 检查花色限制
        suits = set(tile.suit for tile in tiles)
        for meld in melds:
            for tile in meld.tiles:
                suits.add(tile.suit)
        if len(suits) > 2:
            return False
        
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 检查七对
        if WinValidator._is_seven_pairs(tiles_array):
            return True
        
        # 检查标准胡牌
        return WinValidator._is_standard_win(tiles_array)
    
    @staticmethod
    def _is_seven_pairs(tiles_array: List[int]) -> bool:
        """检查七对"""
        pairs = 0
        for count in tiles_array:
            if count == 2:
                pairs += 1
            elif count != 0:
                return False
        return pairs == 7
    
    @staticmethod
    def _is_standard_win(tiles_array: List[int]) -> bool:
        """检查标准胡牌 - 尝试所有雀头位置"""
        for i in range(27):
            if tiles_array[i] >= 2:
                # 尝试这个位置作为雀头
                tiles_array[i] -= 2
                if WinValidator._can_form_melds(tiles_array, 0):
                    tiles_array[i] += 2
                    return True
                tiles_array[i] += 2
        return False
    
    @staticmethod
    def _can_form_melds(tiles_array: List[int], start: int) -> bool:
        """检查剩余牌能否完全组成面子"""
        # 跳过空位置
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return True  # 所有牌都处理完了
        
        count = tiles_array[start]
        
        # 尝试刻子
        if count >= 3:
            tiles_array[start] -= 3
            if WinValidator._can_form_melds(tiles_array, start):
                tiles_array[start] += 3
                return True
            tiles_array[start] += 3
        
        # 尝试顺子（确保同花色）
        if (start % 9 <= 6 and  # 确保不跨花色
            start + 2 < 27 and
            tiles_array[start] >= 1 and
            tiles_array[start + 1] >= 1 and
            tiles_array[start + 2] >= 1):
            
            tiles_array[start] -= 1
            tiles_array[start + 1] -= 1
            tiles_array[start + 2] -= 1
            
            if WinValidator._can_form_melds(tiles_array, start):
                tiles_array[start] += 1
                tiles_array[start + 1] += 1
                tiles_array[start + 2] += 1
                return True
            
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
        
        return False
    
    @staticmethod
    def get_winning_tiles(tiles: List[Tile], melds: List = None) -> List[Tile]:
        """获取听牌的胡牌张"""
        if melds is None:
            melds = []
        
        winning_tiles = []
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                if WinValidator.is_winning_hand(test_tiles, melds):
                    winning_tiles.append(test_tile)
        
        return winning_tiles


class TingValidator:
    """听牌验证器 - 使用正确的向听数算法"""
    
    @staticmethod
    def calculate_shanten(tiles: List[Tile], melds: List = None) -> int:
        """计算向听数"""
        if melds is None:
            melds = []
        
        # 检查花色限制
        suits = set(tile.suit for tile in tiles)
        for meld in melds:
            for tile in meld.tiles:
                suits.add(tile.suit)
        if len(suits) > 2:
            return 99
        
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 如果已经胡牌
        if WinValidator._is_standard_win(tiles_array) or WinValidator._is_seven_pairs(tiles_array):
            return 0
        
        # 计算标准胡牌向听数
        standard_shanten = TingValidator._calculate_standard_shanten(tiles_array)
        
        # 计算七对向听数
        pairs_shanten = TingValidator._calculate_pairs_shanten(tiles_array)
        
        return min(standard_shanten, pairs_shanten)
    
    @staticmethod
    def _calculate_standard_shanten(tiles_array: List[int]) -> int:
        """计算标准胡牌向听数"""
        min_shanten = 99
        
        # 尝试每个位置作为雀头
        for i in range(27):
            if tiles_array[i] >= 2:
                tiles_array[i] -= 2
                
                # 检查剩余牌数是否为3的倍数
                remaining_count = sum(tiles_array)
                if remaining_count % 3 != 0:
                    tiles_array[i] += 2
                    continue
                
                # 使用递归算法准确计算最大面子数
                melds = TingValidator._find_max_melds_recursive(tiles_array[:], 0)
                needed_melds = remaining_count // 3
                
                # 正确的公式：需要的面子数 - 已组成的面子数
                shanten = needed_melds - melds
                min_shanten = min(min_shanten, shanten)
                tiles_array[i] += 2
        
        return min_shanten
    
    @staticmethod
    def _find_max_melds_recursive(tiles_array: List[int], start: int) -> int:
        """递归找到最大面子数"""
        # 跳过空位置
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return 0  # 没有牌了
        
        max_melds = 0
        
        # 尝试组成刻子
        if tiles_array[start] >= 3:
            tiles_array[start] -= 3
            melds = 1 + TingValidator._find_max_melds_recursive(tiles_array, start)
            max_melds = max(max_melds, melds)
            tiles_array[start] += 3
        
        # 尝试组成顺子
        if (start % 9 <= 6 and start + 2 < 27 and
            tiles_array[start] >= 1 and
            tiles_array[start + 1] >= 1 and
            tiles_array[start + 2] >= 1):
            
            tiles_array[start] -= 1
            tiles_array[start + 1] -= 1
            tiles_array[start + 2] -= 1
            
            melds = 1 + TingValidator._find_max_melds_recursive(tiles_array, start)
            max_melds = max(max_melds, melds)
            
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
        
        # 跳过当前位置（作为孤张）
        melds = TingValidator._find_max_melds_recursive(tiles_array, start + 1)
        max_melds = max(max_melds, melds)
        
        return max_melds
    
    @staticmethod
    def _calculate_pairs_shanten(tiles_array: List[int]) -> int:
        """计算七对向听数"""
        pairs = 0
        for count in tiles_array:
            pairs += count // 2
        
        return max(0, 6 - pairs)  # 需要7对，已有pairs对