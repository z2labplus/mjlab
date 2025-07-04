#!/usr/bin/env python3
"""
诊断向听数计算问题
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType
from MahjongKit.validator import WinValidator, TingValidator


def diagnose_win_check():
    """诊断胡牌检查"""
    print("=== 诊断胡牌检查 ===")
    
    # 测试最简单的胡牌例子
    simple_win = "123456789m99s"
    tiles = TilesConverter.string_to_tiles(simple_win)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"测试手牌: {simple_win}")
    print(f"牌数统计: {sum(tiles_array)}")
    
    # 手动检查胡牌
    print("\n手动检查胡牌逻辑:")
    
    # 尝试99s作为雀头
    test_array = tiles_array[:]
    test_array[26] -= 2  # 移除99s
    
    print(f"移除雀头99s后剩余牌数: {sum(test_array)}")
    print("剩余牌分布:")
    for i, count in enumerate(test_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"  {value}{suit_char}: {count}张")
    
    # 检查剩余部分能否组成面子
    print("\n检查能否组成面子:")
    can_form = WinValidator._check_standard_win_recursive(test_array, 0)
    print(f"递归检查结果: {can_form}")
    
    # 逐步模拟递归过程
    print("\n模拟递归过程:")
    simulate_recursive_check(test_array[:], 0, 1)


def simulate_recursive_check(tiles_array, start, depth):
    """模拟递归检查过程"""
    indent = "  " * depth
    print(f"{indent}深度{depth}: 从位置{start}开始")
    
    # 找到第一个非零位置
    while start < 27 and tiles_array[start] == 0:
        start += 1
    
    if start >= 27:
        print(f"{indent}所有牌都处理完，返回True")
        return True
    
    count = tiles_array[start]
    suit_char = ['m', 's', 'p'][start // 9]
    value = (start % 9) + 1
    
    print(f"{indent}处理 {value}{suit_char}: {count}张")
    
    if depth > 5:  # 防止无限递归
        print(f"{indent}递归深度过深，停止")
        return False
    
    # 尝试刻子
    if count >= 3:
        print(f"{indent}尝试刻子 {value}{suit_char}")
        tiles_array[start] -= 3
        if simulate_recursive_check(tiles_array, start, depth + 1):
            print(f"{indent}刻子成功")
            tiles_array[start] += 3
            return True
        tiles_array[start] += 3
        print(f"{indent}刻子失败")
    
    # 尝试顺子
    if (start % 9 <= 6 and start + 2 < 27 and
        tiles_array[start] >= 1 and
        tiles_array[start + 1] >= 1 and
        tiles_array[start + 2] >= 1):
        
        value2 = (start % 9) + 2
        value3 = (start % 9) + 3
        print(f"{indent}尝试顺子 {value}{value2}{value3}{suit_char}")
        
        tiles_array[start] -= 1
        tiles_array[start + 1] -= 1
        tiles_array[start + 2] -= 1
        
        if simulate_recursive_check(tiles_array, start, depth + 1):
            print(f"{indent}顺子成功")
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
            return True
        
        tiles_array[start] += 1
        tiles_array[start + 1] += 1
        tiles_array[start + 2] += 1
        print(f"{indent}顺子失败")
    
    print(f"{indent}无法处理，返回False")
    return False


def diagnose_shanten_calculation():
    """诊断向听数计算"""
    print("\n=== 诊断向听数计算 ===")
    
    # 测试用户的例子
    hand = "899m1233467999s"
    tiles = TilesConverter.string_to_tiles(hand)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"测试手牌: {hand}")
    print(f"总牌数: {sum(tiles_array)}")
    
    # 手动计算向听数
    print("\n手动计算向听数:")
    
    # 尝试99m作为雀头
    test_array = tiles_array[:]
    test_array[7] -= 2  # 移除99m (8万的索引是7)
    
    print(f"雀头99m，剩余牌数: {sum(test_array)}")
    print("剩余牌分布:")
    for i, count in enumerate(test_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"  {value}{suit_char}: {count}张")
    
    # 计算面子和搭子
    melds, tatsu = TingValidator._count_melds_and_tatsu(test_array[:])
    print(f"面子数: {melds}, 搭子数: {tatsu}")
    
    need_melds = 4 - melds
    shanten = max(0, need_melds - tatsu)
    print(f"需要面子: {need_melds}, 向听数: {shanten}")


if __name__ == "__main__":
    diagnose_win_check()
    diagnose_shanten_calculation()