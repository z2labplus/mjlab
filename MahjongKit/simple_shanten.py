#!/usr/bin/env python3
"""
简化但准确的向听数计算器
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import List, Dict, Tuple
from MahjongKit.core import Tile, TilesConverter, SuitType


class SimpleShantenCalculator:
    """简化的向听数计算器"""
    
    @staticmethod
    def calculate_shanten(tiles: List[Tile]) -> int:
        """计算向听数"""
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 计算标准型向听数
        standard_shanten = SimpleShantenCalculator._calculate_standard_shanten(tiles_array)
        
        # 计算七对型向听数
        pairs_shanten = SimpleShantenCalculator._calculate_pairs_shanten(tiles_array)
        
        return min(standard_shanten, pairs_shanten)
    
    @staticmethod
    def _calculate_standard_shanten(tiles_array: List[int]) -> int:
        """计算标准型向听数 - 尝试所有可能的雀头"""
        min_shanten = 99
        
        # 尝试每个位置作为雀头
        for i in range(27):
            if tiles_array[i] >= 2:
                # 设置雀头
                tiles_copy = tiles_array[:]
                tiles_copy[i] -= 2
                
                # 计算剩余部分的向听数
                shanten = SimpleShantenCalculator._calculate_body_shanten(tiles_copy)
                min_shanten = min(min_shanten, shanten)
        
        # 也尝试没有雀头的情况
        shanten = SimpleShantenCalculator._calculate_body_shanten(tiles_array) + 1
        min_shanten = min(min_shanten, shanten)
        
        return min_shanten
    
    @staticmethod
    def _calculate_body_shanten(tiles_array: List[int]) -> int:
        """计算去掉雀头后的向听数"""
        return SimpleShantenCalculator._min_shanten_recursive(tiles_array, 0, 0, 0)
    
    @staticmethod
    def _min_shanten_recursive(tiles_array: List[int], pos: int, melds: int, tatsu: int) -> int:
        """递归计算最小向听数"""
        # 跳过空位置
        while pos < 27 and tiles_array[pos] == 0:
            pos += 1
        
        if pos >= 27:
            # 所有牌都处理完了
            need_melds = 4 - melds
            if need_melds <= 0:
                return 0
            return max(0, need_melds - tatsu)
        
        count = tiles_array[pos]
        min_shanten = 99
        
        # 尝试刻子
        for kotsu in range(count // 3 + 1):
            tiles_array[pos] -= kotsu * 3
            remaining = tiles_array[pos]
            
            # 尝试对子(搭子)
            for pairs in range(remaining // 2 + 1):
                tiles_array[pos] -= pairs * 2
                final_remaining = tiles_array[pos]
                
                # 检查两面搭子
                two_sided = 0
                if (final_remaining > 0 and pos % 9 <= 7 and pos + 1 < 27 and 
                    tiles_array[pos + 1] > 0):
                    # 可以形成两面搭子
                    tiles_array[pos] -= 1
                    tiles_array[pos + 1] -= 1
                    two_sided = 1
                    
                    shanten = SimpleShantenCalculator._min_shanten_recursive(
                        tiles_array, pos, melds + kotsu, tatsu + pairs + two_sided
                    )
                    min_shanten = min(min_shanten, shanten)
                    
                    tiles_array[pos] += 1
                    tiles_array[pos + 1] += 1
                
                # 检查嵌张搭子
                if (final_remaining > 0 and pos % 9 <= 6 and pos + 2 < 27 and 
                    tiles_array[pos + 2] > 0):
                    # 可以形成嵌张搭子
                    tiles_array[pos] -= 1
                    tiles_array[pos + 2] -= 1
                    
                    shanten = SimpleShantenCalculator._min_shanten_recursive(
                        tiles_array, pos, melds + kotsu, tatsu + pairs + 1
                    )
                    min_shanten = min(min_shanten, shanten)
                    
                    tiles_array[pos] += 1
                    tiles_array[pos + 2] += 1
                
                # 不形成搭子，直接递归
                shanten = SimpleShantenCalculator._min_shanten_recursive(
                    tiles_array, pos + 1, melds + kotsu, tatsu + pairs
                )
                min_shanten = min(min_shanten, shanten)
                
                tiles_array[pos] += pairs * 2
            
            tiles_array[pos] += kotsu * 3
        
        # 尝试顺子（如果在同花色内且位置允许）
        if pos % 9 <= 6 and pos + 2 < 27:
            max_shuntsu = min(tiles_array[pos], tiles_array[pos + 1], tiles_array[pos + 2])
            
            for shuntsu in range(1, max_shuntsu + 1):
                tiles_array[pos] -= shuntsu
                tiles_array[pos + 1] -= shuntsu  
                tiles_array[pos + 2] -= shuntsu
                
                shanten = SimpleShantenCalculator._min_shanten_recursive(
                    tiles_array, pos, melds + shuntsu, tatsu
                )
                min_shanten = min(min_shanten, shanten)
                
                tiles_array[pos] += shuntsu
                tiles_array[pos + 1] += shuntsu
                tiles_array[pos + 2] += shuntsu
        
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
    def get_effective_tiles(tiles: List[Tile]) -> List[Tuple[str, int]]:
        """获取有效进张"""
        current_shanten = SimpleShantenCalculator.calculate_shanten(tiles)
        effective_tiles = []
        
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                new_shanten = SimpleShantenCalculator.calculate_shanten(test_tiles)
                
                if new_shanten < current_shanten:
                    effective_tiles.append((str(test_tile), new_shanten))
        
        return effective_tiles


if __name__ == "__main__":
    print("=== SimpleShantenCalculator Test ===")
    
    # 测试用户的例子
    test_hand = "4899m1233467999s"
    tiles = TilesConverter.string_to_tiles(test_hand)
    
    print(f"测试手牌: {test_hand}")
    shanten = SimpleShantenCalculator.calculate_shanten(tiles)
    print(f"向听数: {shanten}")
    
    # 测试打出4m后
    tiles_after = TilesConverter.string_to_tiles("899m1233467999s")
    
    print(f"\n打出4m后: {TilesConverter.tiles_to_string(tiles_after)}")
    shanten_after = SimpleShantenCalculator.calculate_shanten(tiles_after)
    print(f"向听数: {shanten_after}")
    
    # 有效进张
    effective = SimpleShantenCalculator.get_effective_tiles(tiles_after)
    print(f"有效进张: {effective}")
    
    # 测试具体进张
    test_tiles = [
        ("7m", "899m1233467999s"),  # 7m -> 7899m1233467999s
        ("9m", "899m1233467999s"),  # 9m -> 899m1233467999s9m  
        ("2s", "899m1233467999s"),  # 2s -> 899m12233467999s
        ("5s", "899m1233467999s"),  # 5s -> 899m123345679999s
        ("8s", "899m1233467999s"),  # 8s -> 899m12334678999s
    ]
    
    print("\n具体进张测试:")
    for tile_str, base_hand in test_tiles:
        base_tiles = TilesConverter.string_to_tiles(base_hand)
        tile = Tile.from_string(tile_str)
        new_tiles = base_tiles + [tile]
        new_shanten = SimpleShantenCalculator.calculate_shanten(new_tiles)
        print(f"  加入{tile_str}: {new_shanten}向听")