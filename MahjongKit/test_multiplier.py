#!/usr/bin/env python3
"""
测试倍数计算系统
验证各种番型的检测和倍数计算
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType, Meld, MeldType
from MahjongKit.multiplier_calculator import MultiplierCalculator, WinContext, FanPattern


def create_tiles(tiles_str: str):
    """从字符串创建牌列表"""
    return TilesConverter.string_to_tiles(tiles_str)


def create_meld(meld_type: MeldType, tiles_str: str):
    """创建副露"""
    tiles = create_tiles(tiles_str)
    return Meld(meld_type, tiles)


def test_basic_patterns():
    """测试基础番型"""
    print("=== 测试基础番型 ===")
    
    test_cases = [
        # 平胡
        {
            "name": "平胡",
            "tiles": "123456789m99s",
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 1,
            "expected_patterns": ["平胡"]
        },
        
        # 断么九
        {
            "name": "断么九", 
            "tiles": "2345678m2233s",
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 2,
            "expected_patterns": ["断么九"]
        },
        
        # 碰碰胡
        {
            "name": "碰碰胡",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.PENG, "222m"),
                create_meld(MeldType.PENG, "333s"),
                create_meld(MeldType.PENG, "444p"),
                create_meld(MeldType.PENG, "555m")
            ],
            "context": WinContext(),
            "expected_multiplier": 2,
            "expected_patterns": ["碰碰胡"]
        },
        
        # 七对
        {
            "name": "七对",
            "tiles": "11223344556677m",
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 4,
            "expected_patterns": ["七对"]
        },
        
        # 清一色
        {
            "name": "清一色",
            "tiles": "123456789m99m",
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 4,
            "expected_patterns": ["清一色"]
        },
        
        # 金钩钓
        {
            "name": "金钩钓",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.PENG, "111m"),
                create_meld(MeldType.PENG, "222m"),
                create_meld(MeldType.PENG, "333m"),
                create_meld(MeldType.PENG, "444m")
            ],
            "context": WinContext(),
            "expected_multiplier": 4,
            "expected_patterns": ["金钩钓"]
        }
    ]
    
    for case in test_cases:
        tiles = create_tiles(case["tiles"])
        result = MultiplierCalculator.calculate(tiles, case["melds"], case["context"])
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  副露: {len(case['melds'])}组")
        print(f"  期望倍数: {case['expected_multiplier']}")
        print(f"  实际倍数: {result['multiplier']}")
        print(f"  期望番型: {case['expected_patterns']}")
        print(f"  实际番型: {result['patterns']}")
        
        if result['multiplier'] == case['expected_multiplier']:
            print("  ✅ 倍数正确")
        else:
            print("  ❌ 倍数错误")
        
        if case['expected_patterns'][0] in result['patterns']:
            print("  ✅ 番型正确")
        else:
            print("  ❌ 番型错误")


def test_advanced_patterns():
    """测试高级番型"""
    print("\n=== 测试高级番型 ===")
    
    test_cases = [
        # 清七对
        {
            "name": "清七对",
            "tiles": "11223344556677m",
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 16,
            "expected_patterns": ["清七对"]
        },
        
        # 清碰
        {
            "name": "清碰",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.PENG, "111m"),
                create_meld(MeldType.PENG, "222m"),
                create_meld(MeldType.PENG, "333m"),
                create_meld(MeldType.PENG, "444m")
            ],
            "context": WinContext(),
            "expected_multiplier": 8,
            "expected_patterns": ["清碰"]
        },
        
        # 清金钩钓
        {
            "name": "清金钩钓",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.PENG, "111m"),
                create_meld(MeldType.PENG, "222m"),
                create_meld(MeldType.PENG, "333m"),
                create_meld(MeldType.PENG, "444m")
            ],
            "context": WinContext(),
            "expected_multiplier": 16,
            "expected_patterns": ["清金钩钓"]
        },
        
        # 龙七对
        {
            "name": "龙七对",
            "tiles": "11223344556666m",  # 有一组4张相同的牌
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 8,
            "expected_patterns": ["龙七对"]
        },
        
        # 双龙七对
        {
            "name": "双龙七对", 
            "tiles": "1122334455666m",  # 有两组4张相同的牌
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 16,
            "expected_patterns": ["双龙七对"]
        },
        
        # 将七对
        {
            "name": "将七对",
            "tiles": "22225555888822m",  # 全部是2、5、8
            "melds": [],
            "context": WinContext(),
            "expected_multiplier": 16,
            "expected_patterns": ["将七对"]
        }
    ]
    
    for case in test_cases:
        tiles = create_tiles(case["tiles"])
        result = MultiplierCalculator.calculate(tiles, case["melds"], case["context"])
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  期望倍数: {case['expected_multiplier']}")
        print(f"  实际倍数: {result['multiplier']}")
        print(f"  期望番型: {case['expected_patterns']}")
        print(f"  实际番型: {result['patterns']}")
        print(f"  详细信息: {result['details']}")
        
        if result['multiplier'] == case['expected_multiplier']:
            print("  ✅ 倍数正确")
        else:
            print("  ❌ 倍数错误")


def test_special_patterns():
    """测试特殊番型"""
    print("\n=== 测试特殊番型 ===")
    
    test_cases = [
        # 天胡
        {
            "name": "天胡",
            "tiles": "123456789m99s",
            "melds": [],
            "context": WinContext(is_tianhu=True),
            "expected_multiplier": 32,
            "expected_patterns": ["天胡"]
        },
        
        # 地胡
        {
            "name": "地胡",
            "tiles": "123456789m99s",
            "melds": [],
            "context": WinContext(is_dihu=True),
            "expected_multiplier": 32,
            "expected_patterns": ["地胡"]
        },
        
        # 八仙过海 (2个杠的金钩钓)
        {
            "name": "八仙过海",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.GANG, "1111m"),
                create_meld(MeldType.GANG, "2222m"),
                create_meld(MeldType.PENG, "333m"),
                create_meld(MeldType.PENG, "444m")
            ],
            "context": WinContext(),
            "expected_multiplier": 8,
            "expected_patterns": ["八仙过海"]
        },
        
        # 十二金钗 (3个杠的金钩钓)
        {
            "name": "十二金钗",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.GANG, "1111m"),
                create_meld(MeldType.GANG, "2222m"),
                create_meld(MeldType.GANG, "3333m"),
                create_meld(MeldType.PENG, "444m")
            ],
            "context": WinContext(),
            "expected_multiplier": 16,
            "expected_patterns": ["十二金钗"]
        },
        
        # 十八罗汉 (4个杠的金钩钓)
        {
            "name": "十八罗汉",
            "tiles": "99m",
            "melds": [
                create_meld(MeldType.GANG, "1111m"),
                create_meld(MeldType.GANG, "2222m"),
                create_meld(MeldType.GANG, "3333m"),
                create_meld(MeldType.GANG, "4444m")
            ],
            "context": WinContext(),
            "expected_multiplier": 64,
            "expected_patterns": ["十八罗汉"]
        }
    ]
    
    for case in test_cases:
        tiles = create_tiles(case["tiles"])
        result = MultiplierCalculator.calculate(tiles, case["melds"], case["context"])
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  副露: {len(case['melds'])}组")
        print(f"  期望倍数: {case['expected_multiplier']}")
        print(f"  实际倍数: {result['multiplier']}")
        print(f"  期望番型: {case['expected_patterns']}")
        print(f"  实际番型: {result['patterns']}")
        print(f"  详细信息: {result['details']}")
        
        if result['multiplier'] == case['expected_multiplier']:
            print("  ✅ 倍数正确")
        else:
            print("  ❌ 倍数错误")


def test_additional_multipliers():
    """测试附加倍数（自摸、杠上开花等）"""
    print("\n=== 测试附加倍数 ===")
    
    test_cases = [
        # 自摸
        {
            "name": "平胡自摸",
            "tiles": "123456789m99s",
            "melds": [],
            "context": WinContext(is_zimo=True),
            "expected_multiplier": 2,  # 1 * 2
            "expected_patterns": ["平胡", "自摸"]
        },
        
        # 七对自摸
        {
            "name": "七对自摸",
            "tiles": "11223344556677m",
            "melds": [],
            "context": WinContext(is_zimo=True),
            "expected_multiplier": 8,  # 4 * 2
            "expected_patterns": ["七对", "自摸"]
        },
        
        # 杠上开花
        {
            "name": "杠上开花",
            "tiles": "123456789m99s",
            "melds": [],
            "context": WinContext(is_gang_flower=True),
            "expected_multiplier": 2,  # 1 * 2
            "expected_patterns": ["平胡", "杠上开花"]
        },
        
        # 抢杠胡
        {
            "name": "抢杠胡",
            "tiles": "123456789m99s",
            "melds": [],
            "context": WinContext(is_rob_kong=True),
            "expected_multiplier": 2,  # 1 * 2
            "expected_patterns": ["平胡", "抢杠胡"]
        },
        
        # 多重附加倍数
        {
            "name": "七对自摸杠上开花",
            "tiles": "11223344556677m",
            "melds": [],
            "context": WinContext(is_zimo=True, is_gang_flower=True),
            "expected_multiplier": 16,  # 4 * 2 * 2
            "expected_patterns": ["七对", "自摸", "杠上开花"]
        }
    ]
    
    for case in test_cases:
        tiles = create_tiles(case["tiles"])
        result = MultiplierCalculator.calculate(tiles, case["melds"], case["context"])
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  期望倍数: {case['expected_multiplier']}")
        print(f"  实际倍数: {result['multiplier']}")
        print(f"  期望番型: {case['expected_patterns']}")
        print(f"  实际番型: {result['patterns']}")
        print(f"  详细信息: {result['details']}")
        
        if result['multiplier'] == case['expected_multiplier']:
            print("  ✅ 倍数正确")
        else:
            print("  ❌ 倍数错误")
        
        # 检查是否包含所有期望的番型
        all_patterns_found = all(p in result['patterns'] for p in case['expected_patterns'])
        if all_patterns_found:
            print("  ✅ 番型正确")
        else:
            print("  ❌ 番型错误")


def test_gen_calculation():
    """测试根数计算"""
    print("\n=== 测试根数计算 ===")
    
    test_cases = [
        # 1根（1组4张相同的牌）
        {
            "name": "1根",
            "tiles": "1111234567889m",
            "melds": [],
            "context": WinContext(),
            "expected_gen": 1,
            "expected_multiplier": 2  # 1 * 2^1
        },
        
        # 2根（2组4张相同的牌）
        {
            "name": "2根",
            "tiles": "11112222345678m",
            "melds": [],
            "context": WinContext(),
            "expected_gen": 2,
            "expected_multiplier": 4  # 1 * 2^2
        },
        
        # 杠产生的根
        {
            "name": "杠根",
            "tiles": "123456789m99s",
            "melds": [
                create_meld(MeldType.GANG, "1111p")
            ],
            "context": WinContext(),
            "expected_gen": 1,
            "expected_multiplier": 2  # 1 * 2^1
        },
        
        # 龙七对不计1根
        {
            "name": "龙七对不计1根",
            "tiles": "11223344556666m",  # 有1组4张相同的牌
            "melds": [],
            "context": WinContext(),
            "expected_gen": 0,  # 龙七对不计1根
            "expected_multiplier": 8  # 不受根数影响
        }
    ]
    
    for case in test_cases:
        tiles = create_tiles(case["tiles"])
        result = MultiplierCalculator.calculate(tiles, case["melds"], case["context"])
        
        print(f"\n{case['name']}:")
        print(f"  手牌: {case['tiles']}")
        print(f"  副露: {len(case['melds'])}组")
        print(f"  期望根数: {case['expected_gen']}")
        print(f"  实际根数: {result['details']['effective_gen_count']}")
        print(f"  期望倍数: {case['expected_multiplier']}")
        print(f"  实际倍数: {result['multiplier']}")
        print(f"  番型: {result['patterns']}")
        print(f"  详细信息: {result['details']}")
        
        if result['details']['effective_gen_count'] == case['expected_gen']:
            print("  ✅ 根数正确")
        else:
            print("  ❌ 根数错误")
        
        if result['multiplier'] == case['expected_multiplier']:
            print("  ✅ 倍数正确")
        else:
            print("  ❌ 倍数错误")


def test_exclusion_rules():
    """测试互斥规则"""
    print("\n=== 测试互斥规则 ===")
    
    # 清七对应该排除清一色和七对
    tiles = create_tiles("11223344556677m")
    result = MultiplierCalculator.calculate(tiles, [], WinContext())
    
    print(f"清七对测试:")
    print(f"  手牌: 11223344556677m")
    print(f"  倍数: {result['multiplier']}")
    print(f"  番型: {result['patterns']}")
    print(f"  主番型: {result['details']['main_pattern']}")
    
    # 应该是清七对(16倍)而不是清一色(4倍)+七对(4倍)
    if result['details']['main_pattern'] == "清七对" and result['multiplier'] == 16:
        print("  ✅ 互斥规则正确")
    else:
        print("  ❌ 互斥规则错误")


if __name__ == "__main__":
    print("血战到底麻将倍数计算系统测试")
    print("=" * 50)
    
    test_basic_patterns()
    test_advanced_patterns()
    test_special_patterns()
    test_additional_multipliers()
    test_gen_calculation()
    test_exclusion_rules()
    
    print("\n" + "=" * 50)
    print("测试完成")