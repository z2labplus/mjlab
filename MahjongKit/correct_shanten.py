#!/usr/bin/env python3
"""
正确的向听数计算器
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import List, Dict, Tuple
from MahjongKit.core import Tile, TilesConverter, SuitType


class CorrectShantenCalculator:
    """正确的向听数计算器"""
    
    @staticmethod
    def calculate_shanten(tiles: List[Tile]) -> int:
        """计算向听数"""
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 计算标准型向听数
        standard_shanten = CorrectShantenCalculator._calculate_standard_shanten(tiles_array[:])
        
        # 计算七对型向听数
        pairs_shanten = CorrectShantenCalculator._calculate_pairs_shanten(tiles_array[:])
        
        return min(standard_shanten, pairs_shanten)
    
    @staticmethod
    def is_winning_hand(tiles: List[Tile]) -> bool:
        """检查是否为胡牌"""
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 检查标准胡牌
        if CorrectShantenCalculator._is_standard_win(tiles_array[:]):
            return True
        
        # 检查七对
        if CorrectShantenCalculator._is_seven_pairs(tiles_array[:]):
            return True
        
        return False
    
    @staticmethod
    def _is_standard_win(tiles_array: List[int]) -> bool:
        """检查标准胡牌"""
        # 尝试每个位置作为雀头
        for i in range(27):
            if tiles_array[i] >= 2:
                tiles_array[i] -= 2
                if CorrectShantenCalculator._can_form_melds(tiles_array, 0):
                    tiles_array[i] += 2
                    return True
                tiles_array[i] += 2
        
        return False
    
    @staticmethod
    def _can_form_melds(tiles_array: List[int], start: int) -> bool:
        """检查是否能组成面子"""
        # 跳过空位置
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return True  # 所有牌都处理完
        
        count = tiles_array[start]
        
        # 尝试刻子
        if count >= 3:
            tiles_array[start] -= 3
            if CorrectShantenCalculator._can_form_melds(tiles_array, start):
                tiles_array[start] += 3
                return True
            tiles_array[start] += 3
        
        # 尝试顺子（必须在同花色内）
        if (start % 9 <= 6 and  # 确保不跨花色
            start + 2 < 27 and  # 确保索引有效
            tiles_array[start] >= 1 and
            tiles_array[start + 1] >= 1 and
            tiles_array[start + 2] >= 1):
            
            tiles_array[start] -= 1
            tiles_array[start + 1] -= 1
            tiles_array[start + 2] -= 1
            
            if CorrectShantenCalculator._can_form_melds(tiles_array, start):
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
        """检查七对"""
        pairs = 0
        for count in tiles_array:
            if count == 2:
                pairs += 1
            elif count != 0:
                return False
        return pairs == 7
    
    @staticmethod
    def _calculate_standard_shanten(tiles_array: List[int]) -> int:
        """计算标准型向听数"""
        min_shanten = 99
        
        # 尝试每个位置作为雀头
        for i in range(27):
            if tiles_array[i] >= 2:
                tiles_array[i] -= 2
                shanten = CorrectShantenCalculator._calculate_melds_shanten(tiles_array, 0, 0, 0)
                min_shanten = min(min_shanten, shanten)
                tiles_array[i] += 2
        
        # 无雀头的情况
        shanten = CorrectShantenCalculator._calculate_melds_shanten(tiles_array, 0, 0, 0) + 1
        min_shanten = min(min_shanten, shanten)
        
        return min_shanten
    
    @staticmethod
    def _calculate_melds_shanten(tiles_array: List[int], start: int, melds: int, tatsu: int) -> int:
        """计算面子部分的向听数"""
        # 跳过空位置
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            need_melds = 4 - melds
            return max(0, need_melds - tatsu)
        
        count = tiles_array[start]
        min_shanten = 99
        
        # 尝试刻子
        max_kotsu = count // 3
        for kotsu in range(max_kotsu + 1):
            tiles_array[start] -= kotsu * 3
            remaining = tiles_array[start]
            
            # 尝试对子搭子
            max_pairs = remaining // 2
            for pairs in range(max_pairs + 1):
                tiles_array[start] -= pairs * 2
                final_remaining = tiles_array[start]
                
                new_tatsu = tatsu + pairs
                
                # 处理剩余单张
                if final_remaining == 1:
                    # 检查能否形成搭子
                    if (start % 9 <= 7 and start + 1 < 27 and tiles_array[start + 1] > 0):
                        # 两面搭子
                        tiles_array[start] -= 1
                        tiles_array[start + 1] -= 1
                        shanten = CorrectShantenCalculator._calculate_melds_shanten(
                            tiles_array, start, melds + kotsu, new_tatsu + 1)
                        min_shanten = min(min_shanten, shanten)
                        tiles_array[start] += 1
                        tiles_array[start + 1] += 1
                    
                    if (start % 9 <= 6 and start + 2 < 27 and tiles_array[start + 2] > 0):
                        # 嵌张搭子
                        tiles_array[start] -= 1
                        tiles_array[start + 2] -= 1
                        shanten = CorrectShantenCalculator._calculate_melds_shanten(
                            tiles_array, start, melds + kotsu, new_tatsu + 1)
                        min_shanten = min(min_shanten, shanten)
                        tiles_array[start] += 1
                        tiles_array[start + 2] += 1
                    
                    # 作为孤立牌
                    shanten = CorrectShantenCalculator._calculate_melds_shanten(
                        tiles_array, start + 1, melds + kotsu, new_tatsu)
                    min_shanten = min(min_shanten, shanten)
                else:
                    # 没有剩余单张
                    shanten = CorrectShantenCalculator._calculate_melds_shanten(
                        tiles_array, start + 1, melds + kotsu, new_tatsu)
                    min_shanten = min(min_shanten, shanten)
                
                tiles_array[start] += pairs * 2
            
            tiles_array[start] += kotsu * 3
        
        # 尝试顺子
        if start % 9 <= 6 and start + 2 < 27:
            max_shuntsu = min(tiles_array[start], tiles_array[start + 1], tiles_array[start + 2])
            for shuntsu in range(1, max_shuntsu + 1):
                tiles_array[start] -= shuntsu
                tiles_array[start + 1] -= shuntsu
                tiles_array[start + 2] -= shuntsu
                
                shanten = CorrectShantenCalculator._calculate_melds_shanten(
                    tiles_array, start, melds + shuntsu, tatsu)
                min_shanten = min(min_shanten, shanten)
                
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
            pairs += count // 2
            if count % 2 == 1:
                singles += 1
        
        if pairs >= 7:
            return 0
        
        return 7 - pairs
    
    @staticmethod
    def get_effective_tiles(tiles: List[Tile]) -> List[str]:
        """获取有效进张"""
        current_shanten = CorrectShantenCalculator.calculate_shanten(tiles)
        effective_tiles = []
        
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                new_shanten = CorrectShantenCalculator.calculate_shanten(test_tiles)
                
                if new_shanten < current_shanten:
                    effective_tiles.append(str(test_tile))
        
        return effective_tiles


if __name__ == "__main__":
    print("=== CorrectShantenCalculator Test ===")
    
    # 测试明确的胡牌例子
    print("1. 测试明确胡牌例子:")
    win_hand = "123456789m99s"
    tiles = TilesConverter.string_to_tiles(win_hand)
    is_win = CorrectShantenCalculator.is_winning_hand(tiles)
    shanten = CorrectShantenCalculator.calculate_shanten(tiles)
    print(f"  {win_hand}: 胡牌={is_win}, 向听={shanten}")
    
    # 测试用户的例子
    print("\n2. 测试用户例子:")
    user_hand = "4899m1233467999s"
    tiles = TilesConverter.string_to_tiles(user_hand)
    shanten = CorrectShantenCalculator.calculate_shanten(tiles)
    print(f"  {user_hand}: 向听={shanten}")
    
    # 打出4m后
    after_discard = "899m1233467999s"
    tiles = TilesConverter.string_to_tiles(after_discard)
    shanten = CorrectShantenCalculator.calculate_shanten(tiles)
    effective = CorrectShantenCalculator.get_effective_tiles(tiles)
    print(f"  {after_discard}: 向听={shanten}")
    print(f"  有效进张: {effective}")
    
    # 测试具体进张
    print("\n3. 测试具体进张:")
    test_hands = [
        "7899m1233467999s",  # 加7m
        "8999m1233467999s",  # 加9m
        "899m12233467999s",  # 加2s
        "899m12334567999s",  # 加5s
        "899m123346789999s", # 加8s
        "899m12333467999s",  # 加3s
    ]
    
    for hand in test_hands:
        tiles = TilesConverter.string_to_tiles(hand)
        is_win = CorrectShantenCalculator.is_winning_hand(tiles)
        shanten = CorrectShantenCalculator.calculate_shanten(tiles)
        print(f"  {hand}: 胡牌={is_win}, 向听={shanten}")