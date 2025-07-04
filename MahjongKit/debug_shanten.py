#!/usr/bin/env python3
"""
Debug版本 - 详细分析向听数计算
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType


def debug_analyze_hand(hand_str: str):
    """详细分析手牌结构"""
    print(f"\n=== 分析手牌: {hand_str} ===")
    tiles = TilesConverter.string_to_tiles(hand_str)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"总牌数: {sum(tiles_array)}")
    
    # 显示牌的分布
    print("牌的分布:")
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"  {value}{suit_char}: {count}张")
    
    # 尝试不同的雀头，手动分析
    print("\n尝试不同雀头的组合:")
    for i in range(27):
        if tiles_array[i] >= 2:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            
            # 移除雀头
            test_array = tiles_array[:]
            test_array[i] -= 2
            
            print(f"\n  雀头: {value}{suit_char}")
            remaining_tiles = sum(test_array)
            print(f"  剩余牌数: {remaining_tiles}")
            
            if remaining_tiles % 3 != 0:
                print(f"  ❌ 剩余牌数不是3的倍数，无法组成面子")
                continue
            
            needed_melds = remaining_tiles // 3
            print(f"  需要组成 {needed_melds} 个面子")
            
            # 手动检查能否组成面子
            melds_found = []
            temp_array = test_array[:]
            
            # 先找刻子
            for j in range(27):
                if temp_array[j] >= 3:
                    kotsu_count = temp_array[j] // 3
                    for k in range(kotsu_count):
                        suit_char2 = ['m', 's', 'p'][j // 9]
                        value2 = (j % 9) + 1
                        melds_found.append(f"刻子:{value2}{suit_char2}")
                    temp_array[j] %= 3
            
            # 再找顺子
            for j in range(27):
                if j % 9 <= 6 and j + 2 < 27:  # 确保同花色
                    while (temp_array[j] >= 1 and 
                           temp_array[j + 1] >= 1 and 
                           temp_array[j + 2] >= 1):
                        suit_char2 = ['m', 's', 'p'][j // 9]
                        value1 = (j % 9) + 1
                        value2 = (j % 9) + 2
                        value3 = (j % 9) + 3
                        melds_found.append(f"顺子:{value1}{value2}{value3}{suit_char2}")
                        temp_array[j] -= 1
                        temp_array[j + 1] -= 1
                        temp_array[j + 2] -= 1
            
            print(f"  找到的面子: {melds_found}")
            remaining_after_melds = sum(temp_array)
            print(f"  剩余未组成面子的牌: {remaining_after_melds}")
            
            if remaining_after_melds == 0:
                print(f"  ✅ 可以胡牌！")
                return True
            else:
                print(f"  ❌ 无法完全组成面子")
    
    return False


def manual_check_effective_tiles(base_hand: str):
    """手动检查有效进张"""
    print(f"\n=== 检查 {base_hand} 的有效进张 ===")
    
    base_tiles = TilesConverter.string_to_tiles(base_hand)
    base_is_win = debug_analyze_hand(base_hand)
    
    if base_is_win:
        print("基础手牌已经可以胡牌，是0向听")
        return
    
    print("\n测试各种进张:")
    effective_tiles = []
    
    for suit in SuitType:
        for value in range(1, 10):
            test_tile_str = f"{value}{suit.value}"
            test_hand = base_hand + test_tile_str
            
            print(f"\n--- 加入 {test_tile_str} ---")
            is_win = debug_analyze_hand(test_hand)
            
            if is_win:
                effective_tiles.append(test_tile_str)
                print(f"  ✅ {test_tile_str} 是有效进张")
    
    print(f"\n有效进张总结: {effective_tiles}")
    if effective_tiles:
        print(f"这是 1 向听（有 {len(effective_tiles)} 种有效进张）")
    else:
        print("这可能是 2+ 向听")


if __name__ == "__main__":
    # 测试简单的胡牌例子
    print("=== 测试简单胡牌例子 ===")
    debug_analyze_hand("123456789m99s")
    
    # 测试用户的例子
    print("\n" + "="*50)
    manual_check_effective_tiles("899m1233467999s")