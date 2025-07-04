#!/usr/bin/env python3
"""
Debug the simple validator
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType
from MahjongKit.simple_validator import SimpleValidator


def debug_shanten_calculation(hand_str: str):
    """详细调试向听数计算"""
    print(f"\n=== 调试手牌: {hand_str} ===")
    tiles = TilesConverter.string_to_tiles(hand_str)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"总牌数: {sum(tiles_array)}")
    print("牌分布:", end=" ")
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"{value}{suit_char}:{count}", end=" ")
    print()
    
    # 尝试标准胡牌向听数计算
    print("\n尝试不同雀头位置:")
    min_shanten = 99
    
    for i in range(27):
        if tiles_array[i] >= 2:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            
            # 移除雀头
            tiles_array[i] -= 2
            remaining_count = sum(tiles_array)
            
            print(f"\n雀头 {value}{suit_char}:")
            print(f"  剩余牌数: {remaining_count}")
            
            if remaining_count % 3 != 0:
                print("  ❌ 剩余牌数不是3的倍数")
                tiles_array[i] += 2
                continue
            
            # 计算面子和搭子
            test_array = tiles_array[:]
            melds, tatsu = SimpleValidator._count_melds_and_tatsu(test_array)
            
            print(f"  面子数: {melds}, 搭子数: {tatsu}")
            
            need_melds = remaining_count // 3
            shanten = max(0, need_melds - melds - tatsu)
            print(f"  需要面子: {need_melds}, 向听数: {shanten}")
            
            min_shanten = min(min_shanten, shanten)
            tiles_array[i] += 2
    
    print(f"\n最小向听数: {min_shanten}")
    
    # 验证算法结果
    actual_shanten = SimpleValidator.calculate_shanten(tiles)
    print(f"算法计算结果: {actual_shanten}")


def debug_melds_and_tatsu(tiles_array):
    """调试面子和搭子计算"""
    print("调试面子和搭子计算:")
    original_array = tiles_array[:]
    
    # 显示初始状态
    print("初始牌:", end=" ")
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"{value}{suit_char}:{count}", end=" ")
    print()
    
    melds = 0
    
    # 组成刻子
    print("组成刻子:")
    for i in range(27):
        if tiles_array[i] >= 3:
            kotsu_count = tiles_array[i] // 3
            if kotsu_count > 0:
                suit_char = ['m', 's', 'p'][i // 9]
                value = (i % 9) + 1
                print(f"  {value}{suit_char}: {kotsu_count}个刻子")
                melds += kotsu_count
                tiles_array[i] %= 3
    
    print(f"刻子总数: {melds}")
    
    # 组成顺子
    print("组成顺子:")
    shuntsu_count = 0
    for i in range(27):
        if i % 9 <= 6:  # 确保同花色
            while (i + 2 < 27 and
                   tiles_array[i] >= 1 and
                   tiles_array[i + 1] >= 1 and
                   tiles_array[i + 2] >= 1):
                suit_char = ['m', 's', 'p'][i // 9]
                value1 = (i % 9) + 1
                value2 = (i % 9) + 2
                value3 = (i % 9) + 3
                print(f"  {value1}{value2}{value3}{suit_char}: 1个顺子")
                melds += 1
                shuntsu_count += 1
                tiles_array[i] -= 1
                tiles_array[i + 1] -= 1
                tiles_array[i + 2] -= 1
    
    print(f"顺子总数: {shuntsu_count}")
    print(f"面子总数: {melds}")
    
    # 显示剩余牌
    print("剩余牌:", end=" ")
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"{value}{suit_char}:{count}", end=" ")
    print()
    
    # 统计搭子
    tatsu = 0
    
    # 对子搭子
    print("对子搭子:")
    for i in range(27):
        if tiles_array[i] >= 2:
            pair_count = tiles_array[i] // 2
            if pair_count > 0:
                suit_char = ['m', 's', 'p'][i // 9]
                value = (i % 9) + 1
                print(f"  {value}{suit_char}: {pair_count}个对子搭子")
                tatsu += pair_count
                tiles_array[i] %= 2
    
    # 两面搭子
    print("两面搭子:")
    for i in range(27):
        if tiles_array[i] >= 1:
            if i % 9 <= 7 and i + 1 < 27 and tiles_array[i + 1] >= 1:
                pairs = min(tiles_array[i], tiles_array[i + 1])
                if pairs > 0:
                    suit_char = ['m', 's', 'p'][i // 9]
                    value1 = (i % 9) + 1
                    value2 = (i % 9) + 2
                    print(f"  {value1}{value2}{suit_char}: {pairs}个两面搭子")
                    tatsu += pairs
                    tiles_array[i] -= pairs
                    tiles_array[i + 1] -= pairs
    
    # 嵌张搭子
    print("嵌张搭子:")
    for i in range(27):
        if tiles_array[i] >= 1:
            if i % 9 <= 6 and i + 2 < 27 and tiles_array[i + 2] >= 1:
                pairs = min(tiles_array[i], tiles_array[i + 2])
                if pairs > 0:
                    suit_char = ['m', 's', 'p'][i // 9]
                    value1 = (i % 9) + 1
                    value3 = (i % 9) + 3
                    print(f"  {value1}_{value3}{suit_char}: {pairs}个嵌张搭子")
                    tatsu += pairs
                    tiles_array[i] -= pairs
                    tiles_array[i + 2] -= pairs
    
    print(f"搭子总数: {tatsu}")
    
    # 显示最终剩余
    print("最终剩余:", end=" ")
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"{value}{suit_char}:{count}", end=" ")
    print()
    
    return melds, tatsu


if __name__ == "__main__":
    # 测试用户的例子
    debug_shanten_calculation("899m1233467999s")
    
    # 单独测试面子搭子计算
    print("\n" + "="*50)
    tiles = TilesConverter.string_to_tiles("899m1233467999s")
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    tiles_array[26] -= 2  # 移除99s作为雀头
    debug_melds_and_tatsu(tiles_array)