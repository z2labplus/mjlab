#!/usr/bin/env python3
"""
四川麻将核心数学算法解析
详细解释27位数组、胡牌判断、有效进张计算
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from MahjongKit.core import Tile, TilesConverter, SuitType
from MahjongKit.fixed_validator import WinValidator, TingValidator
from typing import List, Set, Tuple


def explain_27_array_representation():
    """解释27位数组表示法"""
    print("=" * 70)
    print("🔢 四川麻将的数学表示：27位频率数组")
    print("=" * 70)
    
    print("\n📊 数组结构：")
    print("  索引  0-8:  1万-9万")
    print("  索引  9-17: 1条-9条") 
    print("  索引 18-26: 1筒-9筒")
    print("  每个位置存储该牌的数量(0-4张)")
    
    print("\n🎴 示例手牌分析：")
    example_hand = "123456789m11s"
    tiles = TilesConverter.string_to_tiles(example_hand)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"  手牌: {example_hand}")
    print(f"  27位数组: {tiles_array}")
    
    print("\n📋 数组解读：")
    suit_names = ['万', '条', '筒']
    for suit_idx, suit_name in enumerate(suit_names):
        start = suit_idx * 9
        end = start + 9
        suit_array = tiles_array[start:end]
        print(f"  {suit_name}: {suit_array}")
        
        # 详细解释每个位置
        for i, count in enumerate(suit_array):
            if count > 0:
                print(f"    {i+1}{suit_name}: {count}张")
    
    return tiles_array


def explain_winning_conditions():
    """解释胡牌条件"""
    print(f"\n" + "=" * 70)
    print("🏆 胡牌条件数学判断")
    print("=" * 70)
    
    print("\n🎯 四川麻将胡牌的两种基本形式：")
    print("  1. 标准胡牌：4个面子 + 1个对子 (3*4 + 2 = 14张)")
    print("  2. 七对胡牌：7个对子 (2*7 = 14张)")
    
    print("\n🔍 面子类型：")
    print("  • 顺子：连续的3张牌 (如 123万)")
    print("  • 刻子：3张相同的牌 (如 777条)")
    print("  • 杠子：4张相同的牌 (如 5555筒)")
    print("  • 对子：2张相同的牌 (如 99万)")
    
    # 标准胡牌算法示例
    print("\n🧮 标准胡牌检测算法：")
    
    def check_standard_win_demo(tiles_array: List[int]) -> bool:
        """标准胡牌检测演示"""
        print("  步骤1：枚举所有可能的对子位置")
        print("  步骤2：移除对子后，检查剩余牌能否组成4个面子")
        print("  步骤3：递归检查面子组合")
        
        # 尝试每个位置作为对子
        for i in range(27):
            if tiles_array[i] >= 2:
                print(f"    尝试 {get_tile_name(i)} 作为对子")
                
                # 复制数组并移除对子
                test_array = tiles_array.copy()
                test_array[i] -= 2
                
                # 检查剩余牌能否组成面子
                if check_melds_recursive(test_array, 0, 0):
                    print(f"    ✅ 找到胜利组合！对子：{get_tile_name(i)}")
                    return True
                else:
                    print(f"    ❌ {get_tile_name(i)} 作为对子不可行")
        
        return False
    
    def check_melds_recursive(tiles_array: List[int], start_pos: int, meld_count: int) -> bool:
        """递归检查面子组合"""
        # 跳过空位置
        while start_pos < 27 and tiles_array[start_pos] == 0:
            start_pos += 1
        
        # 检查完所有牌
        if start_pos >= 27:
            return meld_count == 4  # 需要4个面子
        
        # 尝试组成刻子
        if tiles_array[start_pos] >= 3:
            tiles_array[start_pos] -= 3
            if check_melds_recursive(tiles_array, start_pos, meld_count + 1):
                tiles_array[start_pos] += 3
                return True
            tiles_array[start_pos] += 3
        
        # 尝试组成顺子（同花色相邻）
        if (start_pos % 9 <= 6 and  # 不超出花色边界
            start_pos + 2 < 27 and  # 不超出数组边界
            tiles_array[start_pos] >= 1 and
            tiles_array[start_pos + 1] >= 1 and
            tiles_array[start_pos + 2] >= 1):
            
            tiles_array[start_pos] -= 1
            tiles_array[start_pos + 1] -= 1
            tiles_array[start_pos + 2] -= 1
            
            if check_melds_recursive(tiles_array, start_pos, meld_count + 1):
                tiles_array[start_pos] += 1
                tiles_array[start_pos + 1] += 1
                tiles_array[start_pos + 2] += 1
                return True
            
            tiles_array[start_pos] += 1
            tiles_array[start_pos + 1] += 1
            tiles_array[start_pos + 2] += 1
        
        return False
    
    # 七对检测算法
    print("\n🎭 七对胡牌检测算法：")
    
    def check_seven_pairs_demo(tiles_array: List[int]) -> bool:
        """七对检测演示"""
        print("  检查逻辑：")
        print("  1. 统计对子数量（count == 2的位置）")
        print("  2. 统计四张数量（count == 4的位置，算作2对）")
        print("  3. 总对子数 = 2的位置数 + 4的位置数*2")
        print("  4. 检查是否等于7对")
        
        pairs = 0
        for i, count in enumerate(tiles_array):
            if count == 2:
                pairs += 1
                print(f"    {get_tile_name(i)}: 2张 → +1对")
            elif count == 4:
                pairs += 2
                print(f"    {get_tile_name(i)}: 4张 → +2对")
            elif count != 0:
                print(f"    {get_tile_name(i)}: {count}张 → 不符合七对要求")
                return False
        
        result = pairs == 7
        print(f"  总对子数: {pairs}, 七对要求: 7 → {'✅ 胡牌' if result else '❌ 未胡'}")
        return result
    
    # 测试示例
    print("\n🧪 胡牌检测测试：")
    
    test_cases = [
        ("123456789m99s", "标准胡牌"),
        ("11223344556677m", "七对胡牌"),
        ("1112345678999m", "1万刻子胡牌"),
        ("12345678m1122s", "未胡牌")
    ]
    
    for hand_str, desc in test_cases:
        print(f"\n  测试: {hand_str} ({desc})")
        tiles = TilesConverter.string_to_tiles(hand_str)
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        is_win = WinValidator.is_winning_hand(tiles)
        print(f"  结果: {'✅ 胡牌' if is_win else '❌ 未胡'}")


def explain_effective_draws():
    """解释有效进张概念"""
    print(f"\n" + "=" * 70)
    print("🎯 有效进张计算原理")
    print("=" * 70)
    
    print("\n📖 有效进张定义：")
    print("  摸到后能让向听数减少的牌称为有效进张")
    print("  向听数 = 距离胡牌还需要多少张牌")
    
    print("\n🔢 向听数计算逻辑：")
    print("  1. 胡牌状态：向听数 = 0")
    print("  2. 听牌状态：向听数 = 0（摸到胡牌张即可胡）")
    print("  3. 一向听：向听数 = 1（再摸1张有用牌即可听牌）")
    print("  4. 二向听：向听数 = 2（需要2张有用牌）")
    
    def calculate_effective_draws_demo(hand_str: str):
        """有效进张计算演示"""
        print(f"\n🧮 有效进张计算示例：{hand_str}")
        
        tiles = TilesConverter.string_to_tiles(hand_str)
        current_shanten = TingValidator.calculate_shanten(tiles)
        
        print(f"  当前向听数: {current_shanten}")
        
        if current_shanten == 0:
            print("  已听牌，计算胡牌张：")
            winning_tiles = []
            for suit in SuitType:
                for value in range(1, 10):
                    test_tile = Tile(suit, value)
                    test_tiles = tiles + [test_tile]
                    if WinValidator.is_winning_hand(test_tiles):
                        winning_tiles.append(test_tile)
            
            print(f"  胡牌张: {[str(t) for t in winning_tiles]}")
            print(f"  胡牌张数量: {len(winning_tiles)}")
            return winning_tiles
        
        else:
            print("  计算有效进张：")
            effective_tiles = []
            
            for suit in SuitType:
                for value in range(1, 10):
                    test_tile = Tile(suit, value)
                    test_tiles = tiles + [test_tile]
                    new_shanten = TingValidator.calculate_shanten(test_tiles)
                    
                    if new_shanten < current_shanten:
                        effective_tiles.append(test_tile)
                        print(f"    {test_tile}: {current_shanten} → {new_shanten} 向听")
            
            print(f"  有效进张: {[str(t) for t in effective_tiles]}")
            print(f"  有效进张数量: {len(effective_tiles)}")
            print(f"  实际可摸张数: {len(effective_tiles) * 4}张")
            return effective_tiles
    
    # 测试不同向听数的手牌
    test_hands = [
        "123456789m9s",    # 听牌
        "123456789m99",    # 一向听
        "12345678m123s",   # 二向听
        "1234567m1234s"    # 三向听
    ]
    
    for hand in test_hands:
        calculate_effective_draws_demo(hand)


def explain_advanced_algorithms():
    """解释高级算法优化"""
    print(f"\n" + "=" * 70)
    print("⚡ 高级算法优化技巧")
    print("=" * 70)
    
    print("\n🚀 性能优化策略：")
    
    print("\n1. 🔄 位操作优化：")
    print("   • 使用位运算加速数组操作")
    print("   • 预计算常用组合模式")
    print("   • 缓存中间计算结果")
    
    print("\n2. 🧠 启发式剪枝：")
    print("   • 提前终止不可能的递归分支")
    print("   • 优先尝试概率高的组合")
    print("   • 使用记忆化避免重复计算")
    
    print("\n3. 📊 概率计算：")
    print("   • 蒙特卡洛模拟")
    print("   • 剩余牌数统计")
    print("   • 对手手牌推测")
    
    def demonstrate_optimization():
        """演示优化技巧"""
        print("\n🔧 实际优化示例：")
        
        # 预计算的顺子模式
        shun_patterns = [
            [1, 1, 1, 0, 0, 0, 0, 0, 0],  # 123
            [0, 1, 1, 1, 0, 0, 0, 0, 0],  # 234
            [0, 0, 1, 1, 1, 0, 0, 0, 0],  # 345
            # ... 其他模式
        ]
        
        print("  预计算顺子模式，加速匹配")
        print("  使用位运算检查模式匹配")
        print("  缓存向听数计算结果")
        
        # 概率权重
        print("\n📈 进张概率权重：")
        print("  • 中张(4-6)权重高：更容易组成顺子")
        print("  • 边张(1,9)权重低：组合选择有限")
        print("  • 孤立牌权重最低：难以利用")
    
    demonstrate_optimization()


def get_tile_name(index: int) -> str:
    """根据索引获取牌名"""
    suit_names = ['万', '条', '筒']
    suit_idx = index // 9
    value = (index % 9) + 1
    return f"{value}{suit_names[suit_idx]}"


def comprehensive_demo():
    """综合演示"""
    print(f"\n" + "=" * 70)
    print("🎯 综合演示：实际应用")
    print("=" * 70)
    
    print("\n🎴 实战分析：复杂手牌")
    complex_hand = "1123456m4567s88p"
    
    tiles = TilesConverter.string_to_tiles(complex_hand)
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    
    print(f"  手牌: {complex_hand}")
    print(f"  27位数组: {tiles_array}")
    
    # 胡牌检测
    is_winning = WinValidator.is_winning_hand(tiles)
    print(f"  是否胡牌: {'✅ 是' if is_winning else '❌ 否'}")
    
    # 向听数计算
    shanten = TingValidator.calculate_shanten(tiles)
    print(f"  向听数: {shanten}")
    
    # 有效进张分析
    if shanten > 0:
        print("  分析有效进张...")
        effective_count = 0
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = tiles + [test_tile]
                new_shanten = TingValidator.calculate_shanten(test_tiles)
                if new_shanten < shanten:
                    effective_count += 1
        
        print(f"  有效进张种类: {effective_count}")
        print(f"  实际可摸张数: {effective_count * 4}张")
    
    print("\n💡 关键洞察：")
    print("  • 27位数组是四川麻将的核心数据结构")
    print("  • 胡牌检测=递归面子匹配+七对检查")
    print("  • 有效进张=能减少向听数的牌")
    print("  • 算法优化=位运算+缓存+启发式剪枝")


if __name__ == "__main__":
    # 执行完整的教学演示
    tiles_array = explain_27_array_representation()
    explain_winning_conditions()
    explain_effective_draws()
    explain_advanced_algorithms()
    comprehensive_demo()
    
    print(f"\n" + "=" * 70)
    print("🎓 四川麻将数学原理讲解完成！")
    print("   掌握了27位数组、胡牌算法、有效进张的核心概念")
    print("=" * 70)