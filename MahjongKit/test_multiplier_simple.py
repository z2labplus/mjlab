#!/usr/bin/env python3
"""
简化的倍数计算测试 - 验证核心功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType, Meld, MeldType
from MahjongKit.multiplier_calculator import MultiplierCalculator, WinContext


def test_basic_multipliers():
    """测试基础倍数计算"""
    print("=== 基础倍数计算测试 ===")
    
    test_cases = [
        # 平胡
        ("123456789m99s", [], WinContext(), 1, "平胡"),
        
        # 断么九  
        ("2345678m2233s", [], WinContext(), 2, "断么九"),
        
        # 七对
        ("11223344556677m", [], WinContext(), 4, "七对或清一色"),
        
        # 清一色
        ("123456789m99m", [], WinContext(), 4, "清一色"),
        
        # 自摸加倍
        ("123456789m99s", [], WinContext(is_zimo=True), 2, "平胡自摸"),
        
        # 天胡
        ("123456789m99s", [], WinContext(is_tianhu=True), 32, "天胡"),
        
        # 地胡
        ("123456789m99s", [], WinContext(is_dihu=True), 32, "地胡"),
    ]
    
    for tiles_str, melds, context, expected_multiplier, description in test_cases:
        tiles = TilesConverter.string_to_tiles(tiles_str)
        result = MultiplierCalculator.calculate(tiles, melds, context)
        
        print(f"\n{description}:")
        print(f"  手牌: {tiles_str}")
        print(f"  期望倍数: {expected_multiplier}")
        print(f"  实际倍数: {result['multiplier']}")
        print(f"  番型: {result['patterns']}")
        
        if result['multiplier'] == expected_multiplier:
            print("  ✅ 倍数正确")
        else:
            print("  ❌ 倍数错误")


def test_special_patterns():
    """测试特殊番型"""
    print("\n=== 特殊番型测试 ===")
    
    # 龙七对 - 有4张相同的牌
    tiles = TilesConverter.string_to_tiles("11223344556666m")
    result = MultiplierCalculator.calculate(tiles, [], WinContext())
    
    print(f"龙七对测试:")
    print(f"  手牌: 11223344556666m")
    print(f"  倍数: {result['multiplier']}")
    print(f"  番型: {result['patterns']}")
    print(f"  主番型: {result['details']['main_pattern']}")
    print(f"  根数: {result['details']['total_gen_count']}")
    
    # 检查是否正确识别4张相同的牌
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    gen_count = sum(1 for count in tiles_array if count == 4)
    print(f"  4张牌组数: {gen_count}")


def test_gen_calculation():
    """测试根数计算"""
    print("\n=== 根数计算测试 ===")
    
    # 1根测试
    tiles = TilesConverter.string_to_tiles("1111234567889m")
    result = MultiplierCalculator.calculate(tiles, [], WinContext())
    
    print(f"1根测试:")
    print(f"  手牌: 1111234567889m")
    print(f"  倍数: {result['multiplier']}")
    print(f"  番型: {result['patterns']}")
    print(f"  根数: {result['details']['total_gen_count']}")
    print(f"  有效根数: {result['details']['effective_gen_count']}")
    
    # 检查牌的分布
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    for i, count in enumerate(tiles_array):
        if count > 0:
            suit_char = ['m', 's', 'p'][i // 9]
            value = (i % 9) + 1
            print(f"    {value}{suit_char}: {count}张")


def test_exclusion_logic():
    """测试互斥逻辑"""
    print("\n=== 互斥逻辑测试 ===")
    
    # 清七对应该优先于清一色
    tiles = TilesConverter.string_to_tiles("11223344556677m")
    result = MultiplierCalculator.calculate(tiles, [], WinContext())
    
    print(f"清七对测试:")
    print(f"  手牌: 11223344556677m")
    print(f"  主番型: {result['details']['main_pattern']}")
    print(f"  倍数: {result['multiplier']}")
    
    # 手动检查是否符合各种番型
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    is_qidui = MultiplierCalculator._is_qidui(tiles_array, [], WinContext())
    is_qingyise = MultiplierCalculator._is_qingyise(tiles_array, [], WinContext())
    is_qing_qidui = MultiplierCalculator._is_qing_qidui(tiles_array, [], WinContext())
    
    print(f"  是否七对: {is_qidui}")
    print(f"  是否清一色: {is_qingyise}")
    print(f"  是否清七对: {is_qing_qidui}")


if __name__ == "__main__":
    print("血战到底麻将倍数计算系统 - 简化测试")
    print("=" * 50)
    
    test_basic_multipliers()
    test_special_patterns()
    test_gen_calculation()
    test_exclusion_logic()
    
    print("\n" + "=" * 50)
    print("测试完成")