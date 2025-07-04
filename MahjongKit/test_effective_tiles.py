#!/usr/bin/env python3
"""
Test effective tiles for the user's example
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType
from MahjongKit.simple_validator import SimpleValidator


def test_effective_tiles():
    """测试有效进张"""
    base_hand = "899m1233467999s"
    base_tiles = TilesConverter.string_to_tiles(base_hand)
    base_shanten = SimpleValidator.calculate_shanten(base_tiles)
    
    print(f"基础手牌: {base_hand}")
    print(f"基础向听数: {base_shanten}")
    print()
    
    effective_tiles = []
    
    print("测试各种进张:")
    for suit in SuitType:
        for value in range(1, 10):
            test_tile = Tile(suit, value)
            test_tiles = base_tiles + [test_tile]
            new_shanten = SimpleValidator.calculate_shanten(test_tiles)
            
            tile_str = str(test_tile)
            is_win = SimpleValidator.is_winning_hand(test_tiles)
            
            if is_win:
                print(f"  {tile_str}: 胡牌 (0向听)")
                effective_tiles.append(tile_str)
            elif new_shanten < base_shanten:
                print(f"  {tile_str}: {new_shanten}向听 (减少{base_shanten - new_shanten})")
                effective_tiles.append(tile_str)
    
    print(f"\n有效进张总结: {effective_tiles}")
    
    # 验证用户期望的有效进张
    expected_effective = ["7m", "9m", "2s", "5s", "8s"]
    print(f"用户期望: {expected_effective}")
    
    print("\n验证结果:")
    for tile_str in expected_effective:
        if tile_str in effective_tiles:
            print(f"  ✅ {tile_str} 确实是有效进张")
        else:
            print(f"  ❌ {tile_str} 不是有效进张")
    
    # 验证用户说的无效进张
    non_effective = ["3s"]
    print(f"\n用户说无效: {non_effective}")
    
    for tile_str in non_effective:
        if tile_str not in effective_tiles:
            print(f"  ✅ {tile_str} 确实不是有效进张")
        else:
            print(f"  ❌ {tile_str} 被算法识别为有效进张")


def test_specific_combinations():
    """测试具体的组合"""
    print("\n" + "="*50)
    print("=== 测试具体组合 ===")
    
    test_cases = [
        ("899m1233467999s7m", "加入7m后"),
        ("899m1233467999s9m", "加入9m后"), 
        ("899m1233467999s2s", "加入2s后"),
        ("899m1233467999s5s", "加入5s后"),
        ("899m1233467999s8s", "加入8s后"),
        ("899m1233467999s3s", "加入3s后"),
    ]
    
    for hand_str, description in test_cases:
        tiles = TilesConverter.string_to_tiles(hand_str)
        is_win = SimpleValidator.is_winning_hand(tiles)
        shanten = SimpleValidator.calculate_shanten(tiles)
        
        print(f"{description}: {hand_str}")
        if is_win:
            print(f"  ✅ 可以胡牌 (0向听)")
        else:
            print(f"  📊 {shanten}向听")
        print()


if __name__ == "__main__":
    test_effective_tiles()
    test_specific_combinations()