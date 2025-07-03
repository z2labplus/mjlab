#!/usr/bin/env python3
"""
SichuanMahjongKit Win Validator
血战到底麻将库胡牌验证器
"""

from typing import List, Set, Tuple, Optional, Dict, Any
from collections import Counter
from .core import Tile, TilesConverter, SuitType, PlayerState, MeldType


class WinValidator:
    """胡牌验证器 - 血战到底规则"""
    
    @staticmethod
    def is_winning_hand(tiles: List[Tile], melds: List = None) -> bool:
        """
        检查是否为胡牌手牌
        血战到底规则: 手牌不超过2门花色才能胡牌
        """
        if melds is None:
            melds = []
        
        # 检查花色数量限制
        if not WinValidator._check_suit_limit(tiles, melds):
            return False
        
        # 转换为27位数组进行胡牌检查
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 检查是否为标准胡牌或七对
        return (WinValidator._is_standard_win(tiles_array) or 
                WinValidator._is_seven_pairs(tiles_array))
    
    @staticmethod
    def _check_suit_limit(tiles: List[Tile], melds: List) -> bool:
        """检查花色限制 - 不超过2门花色"""
        suits = set()
        
        # 统计手牌花色
        for tile in tiles:
            suits.add(tile.suit)
        
        # 统计副露花色
        for meld in melds:
            for tile in meld.tiles:
                suits.add(tile.suit)
        
        return len(suits) <= 2
    
    @staticmethod
    def _is_standard_win(tiles_array: List[int]) -> bool:
        """检查是否为标准胡牌(4面子+1对子)"""
        # 递归检查是否能组成标准胡牌
        return WinValidator._check_standard_win_recursive(tiles_array, 0)
    
    @staticmethod
    def _check_standard_win_recursive(tiles_array: List[int], start: int) -> bool:
        """递归检查标准胡牌"""
        # 找到第一个非零牌
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return True  # 所有牌都处理完了
        
        count = tiles_array[start]
        
        # 尝试组成对子
        if count >= 2:
            tiles_array[start] -= 2
            if WinValidator._check_standard_win_recursive(tiles_array, start):
                tiles_array[start] += 2
                return True
            tiles_array[start] += 2
        
        # 尝试组成刻子
        if count >= 3:
            tiles_array[start] -= 3
            if WinValidator._check_standard_win_recursive(tiles_array, start):
                tiles_array[start] += 3
                return True
            tiles_array[start] += 3
        
        # 尝试组成顺子(只能在同花色内)
        if (start % 9 <= 6 and  # 不能跨花色
            tiles_array[start] >= 1 and
            tiles_array[start + 1] >= 1 and
            tiles_array[start + 2] >= 1):
            
            tiles_array[start] -= 1
            tiles_array[start + 1] -= 1
            tiles_array[start + 2] -= 1
            
            if WinValidator._check_standard_win_recursive(tiles_array, start):
                tiles_array[start] += 1
                tiles_array[start + 1] += 1
                tiles_array[start + 2] += 1
                return True
            
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
        
        return False
    
    @staticmethod
    def _is_seven_pairs(tiles_array: List[int]) -> bool:
        """检查是否为七对"""
        pairs = 0
        for count in tiles_array:
            if count == 2:
                pairs += 1
            elif count != 0:
                return False
        return pairs == 7
    
    @staticmethod
    def get_winning_tiles(tiles: List[Tile], melds: List = None) -> List[Tile]:
        """
        获取听牌的胡牌张
        返回所有可能的胡牌张
        """
        if melds is None:
            melds = []
        
        winning_tiles = []
        
        # 遍历所有可能的牌(1-9万, 1-9条, 1-9筒)
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                
                if WinValidator.is_winning_hand(test_tiles, melds):
                    winning_tiles.append(test_tile)
        
        return winning_tiles
    
    @staticmethod
    def is_ting(tiles: List[Tile], melds: List = None) -> bool:
        """检查是否为听牌状态"""
        if melds is None:
            melds = []
        
        return len(WinValidator.get_winning_tiles(tiles, melds)) > 0
    
    @staticmethod
    def get_ting_info(tiles: List[Tile], melds: List = None) -> Dict[str, Any]:
        """获取听牌信息"""
        if melds is None:
            melds = []
        
        winning_tiles = WinValidator.get_winning_tiles(tiles, melds)
        
        return {
            "is_ting": len(winning_tiles) > 0,
            "winning_tiles": winning_tiles,
            "winning_count": len(winning_tiles),
            "winning_tiles_str": [str(tile) for tile in winning_tiles]
        }


class TingValidator:
    """听牌验证器 - 专门用于听牌分析"""
    
    @staticmethod
    def calculate_shanten(tiles: List[Tile], melds: List = None) -> int:
        """
        计算向听数
        0 = 听牌, 1 = 一向听, 2 = 二向听, 等等
        """
        if melds is None:
            melds = []
        
        # 检查花色限制
        if not WinValidator._check_suit_limit(tiles, melds):
            return 99  # 花猪状态，无法胡牌
        
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 计算标准胡牌向听数
        standard_shanten = TingValidator._calculate_standard_shanten(tiles_array)
        
        # 计算七对向听数
        pairs_shanten = TingValidator._calculate_pairs_shanten(tiles_array)
        
        return min(standard_shanten, pairs_shanten)
    
    @staticmethod
    def _calculate_standard_shanten(tiles_array: List[int]) -> int:
        """计算标准胡牌向听数"""
        min_shanten = 99
        
        # 尝试每个位置作为将牌
        for i in range(27):
            if tiles_array[i] >= 2:
                # 移除将牌
                tiles_array[i] -= 2
                
                # 递归计算剩余部分的向听数
                shanten = TingValidator._calculate_melds_shanten(tiles_array, 0, 0, 0)
                min_shanten = min(min_shanten, shanten)
                
                # 恢复将牌
                tiles_array[i] += 2
        
        return min_shanten
    
    @staticmethod
    def _calculate_melds_shanten(tiles_array: List[int], start: int, melds: int, tatsu: int) -> int:
        """递归计算面子向听数"""
        # 找到第一个非零牌
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            # 需要4个面子
            need_melds = 4 - melds
            return max(0, need_melds - tatsu)
        
        count = tiles_array[start]
        min_shanten = 99
        
        # 尝试不同的组合方式
        for shuntsu in range(min(count, (tiles_array[start + 1] if start + 1 < 27 and start % 9 <= 6 else 0),
                                (tiles_array[start + 2] if start + 2 < 27 and start % 9 <= 6 else 0)) + 1):
            if start % 9 <= 6 and start + 2 < 27:
                tiles_array[start] -= shuntsu
                tiles_array[start + 1] -= shuntsu
                tiles_array[start + 2] -= shuntsu
            
            remaining = tiles_array[start]
            
            for kotsu in range(remaining // 3 + 1):
                tiles_array[start] -= kotsu * 3
                
                for tatsu_add in range(min(2, tiles_array[start]) + 1):
                    if tatsu_add == 2:
                        # 对子搭子
                        tiles_array[start] -= 2
                        shanten = TingValidator._calculate_melds_shanten(
                            tiles_array, start + 1, melds + shuntsu + kotsu, tatsu + tatsu_add
                        )
                        tiles_array[start] += 2
                    elif tatsu_add == 1:
                        # 两面搭子或边张搭子
                        tiles_array[start] -= 1
                        tatsu_bonus = 0
                        if start % 9 <= 7 and start + 1 < 27 and tiles_array[start + 1] > 0:
                            tatsu_bonus = 1
                        elif start % 9 <= 6 and start + 2 < 27 and tiles_array[start + 2] > 0:
                            tatsu_bonus = 1
                        
                        shanten = TingValidator._calculate_melds_shanten(
                            tiles_array, start + 1, melds + shuntsu + kotsu, tatsu + tatsu_bonus
                        )
                        tiles_array[start] += 1
                    else:
                        # 不组成搭子
                        shanten = TingValidator._calculate_melds_shanten(
                            tiles_array, start + 1, melds + shuntsu + kotsu, tatsu
                        )
                    
                    min_shanten = min(min_shanten, shanten)
                
                tiles_array[start] += kotsu * 3
            
            if start % 9 <= 6 and start + 2 < 27:
                tiles_array[start] += shuntsu
                tiles_array[start + 1] += shuntsu
                tiles_array[start + 2] += shuntsu
        
        return min_shanten
    
    @staticmethod
    def _calculate_pairs_shanten(tiles_array: List[int]) -> int:
        """计算七对向听数"""
        pairs = 0
        singles = 0
        
        for count in tiles_array:
            if count >= 2:
                pairs += count // 2
                if count % 2 == 1:
                    singles += 1
            elif count == 1:
                singles += 1
        
        if pairs >= 7:
            return 0
        
        need_pairs = 7 - pairs
        available_singles = singles
        
        return max(0, need_pairs - available_singles)


if __name__ == "__main__":
    # 测试代码
    print("=== WinValidator Test ===")
    
    # 测试胡牌检查
    tiles_str = "123456789m11s"  # 一万到九万 + 一条对子
    tiles = TilesConverter.string_to_tiles(tiles_str)
    
    print(f"Testing tiles: {tiles_str}")
    print(f"Is winning: {WinValidator.is_winning_hand(tiles)}")
    
    # 测试听牌
    ting_tiles_str = "12345678m11s"  # 缺九万
    ting_tiles = TilesConverter.string_to_tiles(ting_tiles_str)
    
    print(f"Testing ting tiles: {ting_tiles_str}")
    ting_info = WinValidator.get_ting_info(ting_tiles)
    print(f"Ting info: {ting_info}")
    
    # 测试向听数
    shanten = TingValidator.calculate_shanten(ting_tiles)
    print(f"Shanten: {shanten}")