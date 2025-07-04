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
        """递归检查标准胡牌 - 修复版本，尝试所有可能组合"""
        # 找到第一个非零牌
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return True  # 所有牌都处理完了
        
        count = tiles_array[start]
        
        # 尝试组成刻子
        if count >= 3:
            tiles_array[start] -= 3
            if WinValidator._check_standard_win_recursive(tiles_array, start):
                tiles_array[start] += 3
                return True
            tiles_array[start] += 3
        
        # 尝试组成顺子(只能在同花色内)
        if (start % 9 <= 6 and start + 2 < 27 and  # 确保同花色且索引有效
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
    """听牌验证器 - 使用正确的向听数算法"""
    
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
                
                # 计算剩余部分能组成多少面子和搭子
                melds, tatsu = TingValidator._count_melds_and_tatsu(tiles_array[:])
                
                # 计算向听数：需要4个面子，现有melds个面子和tatsu个搭子
                need_melds = 4 - melds
                shanten = max(0, need_melds - tatsu)
                
                min_shanten = min(min_shanten, shanten)
                tiles_array[i] += 2
        
        # 无雀头情况
        melds, tatsu = TingValidator._count_melds_and_tatsu(tiles_array[:])
        need_melds = 4 - melds
        shanten = max(1, need_melds - tatsu + 1)  # +1因为缺雀头
        min_shanten = min(min_shanten, shanten)
        
        return min_shanten
    
    @staticmethod
    def _count_melds_and_tatsu(tiles_array: List[int]) -> Tuple[int, int]:
        """统计能组成的面子数和搭子数"""
        # 尝试所有可能的面子组合，找到最优解
        best_melds = 0
        best_tatsu = 0
        
        # 使用递归尝试所有可能的面子组合
        melds, remaining = TingValidator._find_max_melds(tiles_array[:])
        best_melds = melds
        
        # 计算剩余牌的搭子数
        tatsu = TingValidator._count_tatsu(remaining)
        best_tatsu = tatsu
        
        return best_melds, best_tatsu
    
    @staticmethod
    def _find_max_melds(tiles_array: List[int]) -> Tuple[int, List[int]]:
        """找到最大面子数，返回(面子数, 剩余牌)"""
        # 找到第一个非零位置
        start = 0
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return 0, tiles_array  # 没有牌了
        
        best_melds = 0
        best_remaining = tiles_array[:]
        
        # 尝试组成刻子
        if tiles_array[start] >= 3:
            tiles_array[start] -= 3
            sub_melds, sub_remaining = TingValidator._find_max_melds(tiles_array[:])
            total_melds = 1 + sub_melds
            if total_melds > best_melds:
                best_melds = total_melds
                best_remaining = sub_remaining[:]
                best_remaining[start] += 3
            tiles_array[start] += 3
        
        # 尝试组成顺子
        if (start % 9 <= 6 and start + 2 < 27 and
            tiles_array[start] >= 1 and
            tiles_array[start + 1] >= 1 and
            tiles_array[start + 2] >= 1):
            
            tiles_array[start] -= 1
            tiles_array[start + 1] -= 1
            tiles_array[start + 2] -= 1
            
            sub_melds, sub_remaining = TingValidator._find_max_melds(tiles_array[:])
            total_melds = 1 + sub_melds
            if total_melds > best_melds:
                best_melds = total_melds
                best_remaining = sub_remaining[:]
                best_remaining[start] += 1
                best_remaining[start + 1] += 1
                best_remaining[start + 2] += 1
            
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
        
        # 跳过当前位置（作为孤张处理）
        tiles_array[start] -= 1
        sub_melds, sub_remaining = TingValidator._find_max_melds(tiles_array[:])
        if sub_melds > best_melds:
            best_melds = sub_melds
            best_remaining = sub_remaining[:]
            best_remaining[start] += 1
        tiles_array[start] += 1
        
        return best_melds, best_remaining
    
    @staticmethod
    def _count_tatsu(tiles_array: List[int]) -> int:
        """统计搭子数"""
        tatsu = 0
        tiles_copy = tiles_array[:]
        
        # 统计对子搭子
        for i in range(27):
            if tiles_copy[i] >= 2:
                tatsu += tiles_copy[i] // 2
                tiles_copy[i] %= 2
        
        # 统计两面搭子
        for i in range(27):
            if tiles_copy[i] >= 1:
                if (i % 9 <= 7 and i + 1 < 27 and tiles_copy[i + 1] >= 1):
                    pairs = min(tiles_copy[i], tiles_copy[i + 1])
                    tatsu += pairs
                    tiles_copy[i] -= pairs
                    tiles_copy[i + 1] -= pairs
        
        # 统计嵌张搭子
        for i in range(27):
            if tiles_copy[i] >= 1:
                if (i % 9 <= 6 and i + 2 < 27 and tiles_copy[i + 2] >= 1):
                    pairs = min(tiles_copy[i], tiles_copy[i + 2])
                    tatsu += pairs
                    tiles_copy[i] -= pairs
                    tiles_copy[i + 2] -= pairs
        
        return tatsu
    
    @staticmethod
    def _calculate_pairs_shanten(tiles_array: List[int]) -> int:
        """计算七对向听数"""
        pairs = 0
        
        for count in tiles_array:
            pairs += count // 2
        
        if pairs >= 7:
            return 0
        
        return 6 - pairs  # 7对 - 已有对数 - 1(因为0向听)


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