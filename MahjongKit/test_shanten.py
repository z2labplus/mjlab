#!/usr/bin/env python3
"""
手动验证向听数计算
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType


def manual_analyze_hand(hand_str: str):
    """手动分析手牌"""
    print(f"分析手牌: {hand_str}")
    tiles = TilesConverter.string_to_tiles(hand_str)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"牌数统计:")
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"  {value}{suit_char}: {count}张")
    
    print(f"总牌数: {sum(tiles_array)}")
    return tiles_array


def test_win_combinations(hand_str: str):
    """测试是否能胡牌"""
    print(f"\n测试胡牌组合: {hand_str}")
    tiles_array = TilesConverter.string_to_tiles(hand_str)
    
    # 简单的胡牌检查：尝试不同的雀头位置
    tiles_27 = TilesConverter.tiles_to_27_array(tiles_array)
    
    for i in range(27):
        if tiles_27[i] >= 2:
            # 尝试这个位置做雀头
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            
            # 移除雀头
            test_array = tiles_27[:]
            test_array[i] -= 2
            
            # 检查剩余部分能否组成面子
            if can_form_melds(test_array):
                print(f"  ✅ 可以胡牌，雀头: {value}{suit_char}")
                return True
    
    print(f"  ❌ 无法胡牌")
    return False


def can_form_melds(tiles_array):
    """检查是否能组成面子"""
    # 简化的检查：递归尝试移除面子
    return try_remove_melds(tiles_array, 0)


def try_remove_melds(tiles_array, start):
    """递归尝试移除面子"""
    # 找到第一个非零位置
    while start < 27 and tiles_array[start] == 0:
        start += 1
    
    if start >= 27:
        return True  # 所有牌都处理完了
    
    count = tiles_array[start]
    
    # 尝试刻子
    if count >= 3:
        tiles_array[start] -= 3
        if try_remove_melds(tiles_array, start):
            tiles_array[start] += 3
            return True
        tiles_array[start] += 3
    
    # 尝试顺子（同花色内）
    if (start % 9 <= 6 and start + 2 < 27 and
        tiles_array[start] >= 1 and 
        tiles_array[start + 1] >= 1 and 
        tiles_array[start + 2] >= 1):
        
        tiles_array[start] -= 1
        tiles_array[start + 1] -= 1
        tiles_array[start + 2] -= 1
        
        if try_remove_melds(tiles_array, start):
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
            return True
        
        tiles_array[start] += 1
        tiles_array[start + 1] += 1
        tiles_array[start + 2] += 1
    
    return False


if __name__ == "__main__":
    print("=== 手动向听数验证 ===")
    
    # 测试用户的例子
    print("1. 用户的原始例子:")
    manual_analyze_hand("4899m1233467999s")
    
    print("\n2. 打出4m后:")
    hand_after = "899m1233467999s"
    manual_analyze_hand(hand_after)
    
    print("\n3. 测试各种进张后是否能胡牌:")
    
    test_hands = [
        "7899m1233467999s",  # 加入7m
        "8999m1233467999s",  # 加入9m  
        "899m12233467999s",  # 加入2s
        "899m123345679999s", # 加入5s
        "899m12334678999s",  # 加入8s
        "899m123334679999s", # 加入3s (用户说不是有效进张)
    ]
    
    for hand in test_hands:
        test_win_combinations(hand)
    
    print("\n4. 测试一个明确的听牌例子:")
    test_win_combinations("123456789m99s")  # 应该听牌
    
    print("\n5. 测试一个明确的非听牌例子:")
    test_win_combinations("13579m13579s")   # 应该不能胡牌