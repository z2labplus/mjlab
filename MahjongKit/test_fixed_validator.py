#!/usr/bin/env python3
"""
测试修复后的向听数计算
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType
from MahjongKit.validator import WinValidator, TingValidator


def test_shanten_calculation():
    """测试向听数计算"""
    print("=== 测试向听数计算 ===")
    
    # 测试用户的例子
    test_cases = [
        ("4899m1233467999s", "原始手牌"),
        ("899m1233467999s", "打出4m后"),
        ("7899m1233467999s", "加入7m后"), 
        ("8999m1233467999s", "加入9m后"),
        ("899m12233467999s", "加入2s后"),
        ("899m12334567999s", "加入5s后"),
        ("899m123346789999s", "加入8s后"),
        ("899m12333467999s", "加入3s后"),
    ]
    
    for hand_str, description in test_cases:
        tiles = TilesConverter.string_to_tiles(hand_str)
        shanten = TingValidator.calculate_shanten(tiles)
        is_win = WinValidator.is_winning_hand(tiles)
        
        print(f"{description}: {hand_str}")
        print(f"  向听数: {shanten}, 胡牌: {is_win}")
        
        if is_win:
            print(f"  ✅ 可以胡牌")
        elif shanten == 0:
            winning_tiles = WinValidator.get_winning_tiles(tiles)
            print(f"  🎯 听牌，胡牌张: {[str(tile) for tile in winning_tiles]}")
        elif shanten == 1:
            print(f"  📈 一向听")
        else:
            print(f"  📊 {shanten}向听")
        print()
    
    # 测试确定胡牌的例子
    print("\n=== 测试确定胡牌例子 ===")
    win_cases = [
        "123456789m99s",  # 明确胡牌
        "11122233344455s", # 七对
    ]
    
    for hand_str in win_cases:
        tiles = TilesConverter.string_to_tiles(hand_str)
        shanten = TingValidator.calculate_shanten(tiles)
        is_win = WinValidator.is_winning_hand(tiles)
        print(f"{hand_str}: 向听={shanten}, 胡牌={is_win}")


def test_effective_tiles():
    """测试有效进张"""
    print("\n=== 测试有效进张 ===")
    
    base_hand = "899m1233467999s"
    tiles = TilesConverter.string_to_tiles(base_hand)
    shanten = TingValidator.calculate_shanten(tiles)
    
    print(f"基础手牌: {base_hand}")
    print(f"向听数: {shanten}")
    
    # 计算有效进张
    effective_tiles = []
    
    for suit in SuitType:
        for value in range(1, 10):
            test_tile = Tile(suit, value)
            test_tiles = tiles + [test_tile]
            new_shanten = TingValidator.calculate_shanten(test_tiles)
            
            if new_shanten < shanten:
                effective_tiles.append(str(test_tile))
    
    print(f"有效进张: {effective_tiles}")
    
    # 验证用户说的有效进张
    expected_effective = ["7m", "9m", "2s", "5s", "8s"]
    print(f"用户期望: {expected_effective}")
    
    for tile_str in expected_effective:
        if tile_str in effective_tiles:
            print(f"  ✅ {tile_str} 确实是有效进张")
        else:
            print(f"  ❌ {tile_str} 不是有效进张")
    
    # 验证用户说的无效进张
    non_effective = ["3s"]
    print(f"用户说无效: {non_effective}")
    
    for tile_str in non_effective:
        if tile_str not in effective_tiles:
            print(f"  ✅ {tile_str} 确实不是有效进张")
        else:
            print(f"  ❌ {tile_str} 被识别为有效进张")


if __name__ == "__main__":
    test_shanten_calculation()
    test_effective_tiles()