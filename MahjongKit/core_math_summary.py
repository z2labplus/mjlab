#!/usr/bin/env python3
"""
四川麻将核心数学工具 - 直接回答用户问题
1. 如何判断胡牌？
2. 什么是有效进张？
3. 用什么数学工具？
"""

def main_concepts():
    print("=" * 80)
    print("🎯 四川麻将核心数学工具解答")
    print("=" * 80)
    
    print("\n🔢 **核心数据结构：27位频率数组**")
    print("   位置  0-8:  1万-9万")
    print("   位置  9-17: 1条-9条") 
    print("   位置 18-26: 1筒-9筒")
    print("   值：该位置牌的数量(0-4)")
    
    print("\n   示例：[1,1,1,1,1,1,1,1,1, 2,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0,0]")
    print("        ↑ 万字1-9各1张     ↑ 1条2张        ↑ 无筒子")
    
    print("\n🏆 **胡牌判断的两个条件**")
    print("\n   条件1：标准胡牌 (4面子+1对子)")
    print("   算法：")
    print("   ┌─ 枚举每个位置作为对子")
    print("   ├─ 移除对子后，递归检查剩余牌")
    print("   ├─ 尝试组成刻子(3张相同)")
    print("   ├─ 尝试组成顺子(连续3张)")
    print("   └─ 检查是否正好组成4个面子")
    
    print("\n   条件2：七对胡牌 (7个对子)")
    print("   算法：")
    print("   ┌─ 统计数组中值为2的位置(1对)")
    print("   ├─ 统计数组中值为4的位置(2对)")
    print("   ├─ 检查其他位置是否为0")
    print("   └─ 总对数 = 2的个数 + 4的个数×2 = 7")
    
    print("\n🎯 **有效进张的定义与计算**")
    print("\n   定义：摸到后能让向听数减少的牌")
    print("   向听数：距离听牌还需要的牌数")
    
    print("\n   计算步骤：")
    print("   ┌─ 1. 计算当前向听数")
    print("   ├─ 2. 遍历所有可能的牌(27种)")
    print("   ├─ 3. 模拟摸到每张牌后的向听数")
    print("   ├─ 4. 如果新向听数 < 当前向听数")
    print("   └─ 5. 该牌就是有效进张")
    
    print("\n📊 **实际代码示例**")
    
    # 胡牌检测核心代码
    print("\n   胡牌检测代码：")
    print("""
def is_winning(tiles_array):
    # 方法1：检查标准胡牌
    for i in range(27):
        if tiles_array[i] >= 2:  # 尝试作为对子
            temp = tiles_array.copy()
            temp[i] -= 2
            if check_4_melds(temp):
                return True
    
    # 方法2：检查七对
    pairs = sum(1 for x in tiles_array if x == 2)
    quads = sum(1 for x in tiles_array if x == 4)
    others = sum(1 for x in tiles_array if x not in [0,2,4])
    return others == 0 and pairs + quads*2 == 7
""")
    
    # 有效进张计算代码
    print("\n   有效进张计算代码：")
    print("""
def get_effective_draws(tiles_array):
    current_shanten = calculate_shanten(tiles_array)
    effective = []
    
    for i in range(27):  # 遍历27种牌
        if tiles_array[i] < 4:  # 该牌还有剩余
            tiles_array[i] += 1  # 模拟摸到
            new_shanten = calculate_shanten(tiles_array)
            
            if new_shanten < current_shanten:
                effective.append(i)  # 这是有效进张
            
            tiles_array[i] -= 1  # 恢复原状态
    
    return effective
""")
    
    print("\n💡 **关键优化技巧**")
    print("\n   1. 预计算：提前计算所有可能的面子组合")
    print("   2. 位运算：使用位操作加速数组比较")
    print("   3. 剪枝：提前终止不可能的递归分支")
    print("   4. 缓存：记住已计算的向听数结果")
    
    print("\n🔄 **算法复杂度分析**")
    print("   • 27位数组操作：O(1)")
    print("   • 胡牌检测：O(27×递归深度) ≈ O(100)")
    print("   • 有效进张计算：O(27×向听数计算) ≈ O(2700)")
    print("   • 实际性能：毫秒级响应")
    
    print("\n🎲 **实战应用场景**")
    print("   ✅ 实时胡牌判断：每次摸牌/碰牌/杠牌后")
    print("   ✅ 出牌建议：计算弃牌后的向听数变化")
    print("   ✅ 听牌检测：向听数为0时的胡牌张计算")
    print("   ✅ AI决策：基于有效进张数量评估牌力")
    
    print("\n" + "=" * 80)
    print("✅ 总结：27位数组+递归算法+向听数计算 = 完整的麻将数学工具包")
    print("=" * 80)


def practical_examples():
    """实用示例"""
    print("\n🧪 **实用计算示例**")
    
    examples = [
        {
            "name": "听牌状态",
            "hand": [1,1,1,1,1,1,1,1,0, 0,0,0,0,0,0,0,0,0, 2,0,0,0,0,0,0,0,0],
            "description": "123456788万 + 11筒，听9万"
        },
        {
            "name": "一向听",
            "hand": [1,1,1,1,1,1,1,0,0, 1,1,1,0,0,0,0,0,0, 2,0,0,0,0,0,0,0,0],
            "description": "1234567万123条11筒，一向听"
        },
        {
            "name": "七对听牌",
            "hand": [2,2,2,2,2,2,0,0,0, 0,0,0,0,0,0,0,0,0, 2,0,0,0,0,0,0,0,0],
            "description": "112233445566万11筒，听7万"
        }
    ]
    
    for ex in examples:
        print(f"\n📋 {ex['name']}：{ex['description']}")
        hand = ex['hand']
        
        # 统计基本信息
        total_tiles = sum(hand)
        suits_used = 0
        if any(hand[0:9]): suits_used += 1
        if any(hand[9:18]): suits_used += 1  
        if any(hand[18:27]): suits_used += 1
        
        print(f"   总牌数: {total_tiles}张")
        print(f"   使用花色: {suits_used}门")
        print(f"   27位数组: {hand}")
        
        # 分析结构
        pairs = sum(1 for x in hand if x == 2)
        triplets = sum(1 for x in hand if x == 3)
        quads = sum(1 for x in hand if x == 4)
        
        print(f"   对子: {pairs}个, 刻子: {triplets}个, 杠子: {quads}个")
        
        # 判断胡牌类型
        if pairs + quads*2 == 7 and all(x in [0,2,4] for x in hand):
            print("   ✅ 七对胡牌")
        elif total_tiles == 14:
            print("   🎯 可能的标准胡牌")
        else:
            print("   ❌ 未完成状态")


if __name__ == "__main__":
    main_concepts()
    practical_examples()