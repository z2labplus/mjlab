#!/usr/bin/env python3
"""
精确的向听数计算器
基于日本麻将库的算法重新实现
"""

from typing import List, Dict, Tuple
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType


class ShantenCalculator:
    """精确的向听数计算器"""
    
    @staticmethod
    def calculate_shanten(tiles: List[Tile]) -> int:
        """
        计算向听数
        使用更精确的算法，参考日本麻将库实现
        """
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 计算标准型向听数
        standard_shanten = ShantenCalculator._calculate_standard_shanten(tiles_array)
        
        # 计算七对型向听数  
        pairs_shanten = ShantenCalculator._calculate_pairs_shanten(tiles_array)
        
        return min(standard_shanten, pairs_shanten)
    
    @staticmethod
    def _calculate_standard_shanten(tiles_array: List[int]) -> int:
        """计算标准型向听数"""
        min_shanten = 99
        
        # 尝试每个位置作为雀头(对子)
        for i in range(27):
            if tiles_array[i] >= 2:
                # 取出雀头
                tiles_array[i] -= 2
                
                # 计算剩余部分的向听数
                melds, tatsu, isolated = ShantenCalculator._analyze_melds_and_tatsu(tiles_array, 0)
                shanten = ShantenCalculator._calculate_shanten_from_analysis(melds, tatsu, isolated)
                
                min_shanten = min(min_shanten, shanten)
                
                # 还原雀头
                tiles_array[i] += 2
        
        return min_shanten
    
    @staticmethod
    def _analyze_melds_and_tatsu(tiles_array: List[int], start: int) -> Tuple[int, int, int]:
        """
        分析面子、搭子和孤立牌
        返回: (完成面子数, 搭子数, 孤立牌数)
        """
        # 找到第一个非零位置
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return (0, 0, 0)
        
        count = tiles_array[start]
        best_melds, best_tatsu, best_isolated = (0, 0, count)
        
        # 尝试刻子
        if count >= 3:
            for kotsu in range(count // 3 + 1):
                tiles_array[start] -= kotsu * 3
                
                remaining = tiles_array[start]
                
                # 处理剩余的牌
                for pairs in range(remaining // 2 + 1):
                    tiles_array[start] -= pairs * 2
                    
                    for singles in range(min(2, tiles_array[start]) + 1):
                        tiles_array[start] -= singles
                        
                        # 递归处理后续
                        next_melds, next_tatsu, next_isolated = ShantenCalculator._analyze_melds_and_tatsu(tiles_array, start + 1)
                        
                        # 计算搭子贡献
                        tatsu_contribution = 0
                        if pairs > 0:
                            tatsu_contribution += pairs  # 对子搭子
                        if singles == 1:
                            # 检查是否能形成两面或边张搭子
                            if (start % 9 <= 7 and start + 1 < 27 and tiles_array[start + 1] > 0):
                                tatsu_contribution += 1  # 两面搭子
                            elif (start % 9 <= 6 and start + 2 < 27 and tiles_array[start + 2] > 0):
                                tatsu_contribution += 1  # 嵌张搭子
                        
                        total_melds = kotsu + next_melds
                        total_tatsu = tatsu_contribution + next_tatsu
                        total_isolated = singles + next_isolated
                        
                        if (total_melds, -total_tatsu, total_isolated) < (best_melds, -best_tatsu, best_isolated):
                            best_melds, best_tatsu, best_isolated = total_melds, total_tatsu, total_isolated
                        
                        tiles_array[start] += singles
                    
                    tiles_array[start] += pairs * 2
                
                tiles_array[start] += kotsu * 3
        
        # 尝试顺子（只在同花色内）
        if start % 9 <= 6 and start + 2 < 27:
            max_shuntsu = min(count, tiles_array[start + 1], tiles_array[start + 2])
            
            for shuntsu in range(max_shuntsu + 1):
                if shuntsu > 0:
                    tiles_array[start] -= shuntsu
                    tiles_array[start + 1] -= shuntsu
                    tiles_array[start + 2] -= shuntsu
                
                # 递归处理当前位置的剩余牌
                remaining_melds, remaining_tatsu, remaining_isolated = ShantenCalculator._analyze_melds_and_tatsu(tiles_array, start)
                
                total_melds = shuntsu + remaining_melds
                total_tatsu = remaining_tatsu
                total_isolated = remaining_isolated
                
                if (total_melds, -total_tatsu, total_isolated) < (best_melds, -best_tatsu, best_isolated):
                    best_melds, best_tatsu, best_isolated = total_melds, total_tatsu, total_isolated
                
                if shuntsu > 0:
                    tiles_array[start] += shuntsu
                    tiles_array[start + 1] += shuntsu
                    tiles_array[start + 2] += shuntsu
        
        return (best_melds, best_tatsu, best_isolated)
    
    @staticmethod
    def _calculate_shanten_from_analysis(melds: int, tatsu: int, isolated: int) -> int:
        """根据面子、搭子、孤立牌分析计算向听数"""
        need_melds = 4 - melds
        
        if need_melds <= tatsu:
            # 搭子足够
            return max(0, need_melds - 1)
        else:
            # 搭子不够，需要更多进张
            return need_melds + max(0, need_melds - tatsu - 1)
    
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
        
        need_pairs = 7 - pairs
        return max(0, need_pairs - singles)
    
    @staticmethod
    def get_effective_tiles(tiles: List[Tile]) -> List[Tuple[Tile, int]]:
        """
        获取有效进张牌
        返回: [(进张牌, 进张后向听数), ...]
        """
        current_shanten = ShantenCalculator.calculate_shanten(tiles)
        effective_tiles = []
        
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                new_shanten = ShantenCalculator.calculate_shanten(test_tiles)
                
                if new_shanten < current_shanten:
                    effective_tiles.append((test_tile, new_shanten))
        
        return effective_tiles
    
    @staticmethod
    def analyze_hand_structure(tiles: List[Tile]) -> Dict[str, any]:
        """分析手牌结构"""
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 找最佳分解
        best_analysis = None
        min_shanten = 99
        
        # 尝试每个雀头位置
        for i in range(27):
            if tiles_array[i] >= 2:
                tiles_array[i] -= 2
                
                melds, tatsu, isolated = ShantenCalculator._analyze_melds_and_tatsu(tiles_array, 0)
                shanten = ShantenCalculator._calculate_shanten_from_analysis(melds, tatsu, isolated)
                
                if shanten < min_shanten:
                    min_shanten = shanten
                    tile = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 1)
                    best_analysis = {
                        'shanten': shanten,
                        'jantou': tile,  # 雀头
                        'melds': melds,
                        'tatsu': tatsu,
                        'isolated': isolated
                    }
                
                tiles_array[i] += 2
        
        return best_analysis or {'shanten': min_shanten}


if __name__ == "__main__":
    # 测试代码
    print("=== ShantenCalculator Test ===")
    
    # 测试用户提到的手牌
    test_hand = "4899m1233467999s"
    tiles = TilesConverter.string_to_tiles(test_hand)
    
    print(f"测试手牌: {test_hand}")
    shanten = ShantenCalculator.calculate_shanten(tiles)
    print(f"向听数: {shanten}")
    
    # 分析结构
    analysis = ShantenCalculator.analyze_hand_structure(tiles)
    print(f"详细分析: {analysis}")
    
    # 有效进张
    effective = ShantenCalculator.get_effective_tiles(tiles)
    print(f"有效进张: {[(str(tile), new_shanten) for tile, new_shanten in effective]}")
    
    # 测试打出4m后
    tiles_after_discard = [t for t in tiles if str(t) != "4m"]
    tiles_after_discard = tiles_after_discard[:-1]  # 移除一张4m
    
    print(f"\n打出4m后手牌: {TilesConverter.tiles_to_string(tiles_after_discard)}")
    shanten_after = ShantenCalculator.calculate_shanten(tiles_after_discard)
    print(f"向听数: {shanten_after}")
    
    effective_after = ShantenCalculator.get_effective_tiles(tiles_after_discard)
    print(f"有效进张: {[(str(tile), new_shanten) for tile, new_shanten in effective_after]}")