#!/usr/bin/env python3
"""
麻将初始手牌推导器使用示例
展示如何使用推导器来补全不完整的牌谱
"""

from mahjong_initial_hand_deducer import MahjongInitialHandDeducer
import json

def example_1_basic_usage():
    """示例1: 基本使用方法"""
    print("=" * 60)
    print("示例1: 基本使用方法")
    print("=" * 60)
    
    # 使用默认测试文件
    input_file = "game_data_template_gang_fixed.json"
    output_file = "example1_output.json"
    
    # 创建推导器实例
    deducer = MahjongInitialHandDeducer(input_file)
    
    # 运行推导
    result = deducer.run_deduction(output_file)
    
    print(f"推导完成，结果保存到: {output_file}")
    return result

def example_2_analyze_specific_player():
    """示例2: 分析特定玩家的推导过程"""
    print("\n" + "=" * 60)
    print("示例2: 分析特定玩家的推导过程")
    print("=" * 60)
    
    # 创建推导器实例
    deducer = MahjongInitialHandDeducer("game_data_template_gang_fixed.json")
    
    # 分析玩家1的详细信息
    player_id = 1
    print(f"\n详细分析玩家{player_id}:")
    
    # 获取各个组成部分
    final_hands = deducer.game_data['final_hand']
    final_hand = final_hands[str(player_id)]['hand']
    
    peng_self_tiles = deducer.get_peng_self_tiles(player_id)
    peng_followed_discards = deducer.get_peng_followed_discards(player_id)
    gang_self_tiles = deducer.get_gang_self_tiles(player_id)
    
    print(f"  最终手牌: {final_hand}")
    print(f"  碰牌中自己的牌: {peng_self_tiles}")
    print(f"  碰牌后的出牌: {peng_followed_discards}")
    print(f"  杠牌中自己的牌: {gang_self_tiles}")
    
    # 执行推导
    deduced_hand = deducer.deduce_initial_hand(player_id)
    print(f"  推导结果: {deduced_hand}")
    
    return deduced_hand

def example_3_batch_processing():
    """示例3: 批量处理多个文件"""
    print("\n" + "=" * 60)
    print("示例3: 批量处理概念（仅演示）")
    print("=" * 60)
    
    # 模拟批量处理多个文件的场景
    files_to_process = ["game_data_template_gang_fixed.json"]  # 在实际使用中可以是多个文件
    
    results = {}
    for input_file in files_to_process:
        print(f"\n处理文件: {input_file}")
        
        try:
            deducer = MahjongInitialHandDeducer(input_file)
            output_file = f"batch_output_{input_file}"
            result = deducer.run_deduction(output_file)
            results[input_file] = {"status": "success", "output": output_file}
        except Exception as e:
            print(f"处理失败: {e}")
            results[input_file] = {"status": "failed", "error": str(e)}
    
    print("\n批量处理结果:")
    for file, result in results.items():
        print(f"  {file}: {result['status']}")
        if result['status'] == 'success':
            print(f"    输出: {result['output']}")
    
    return results

def example_4_validate_formula():
    """示例4: 验证推导公式的正确性"""
    print("\n" + "=" * 60)
    print("示例4: 验证推导公式")
    print("=" * 60)
    
    deducer = MahjongInitialHandDeducer("game_data_template_gang_fixed.json")
    
    print("推导公式: 最初的手牌 = 最后的手牌 + 碰牌中自己的牌 + 碰牌后的出牌 + 杠牌中自己的牌")
    print("\n各个组件说明:")
    print("1. 最后的手牌: 游戏结束时的手牌")
    print("2. 碰牌中自己的牌: 碰牌操作中消耗的自己的牌（每次碰牌消耗2张）")
    print("3. 碰牌后的出牌: 碰牌之后立即出的牌") 
    print("4. 杠牌中自己的牌: 杠牌操作中消耗的自己的牌（明杠3张，加杠1张）")
    
    # 对所有未知玩家进行推导验证
    for player_id in [1, 2, 3]:
        print(f"\n验证玩家{player_id}:")
        deduced_hand = deducer.deduce_initial_hand(player_id)
        
        if len(deduced_hand) == 13:
            print(f"  ✅ 公式验证通过，推导出13张初始手牌")
        else:
            print(f"  ⚠️ 公式可能需要调整，推导出{len(deduced_hand)}张手牌")

def create_sample_incomplete_data():
    """创建一个示例的不完整牌谱数据"""
    print("\n" + "=" * 60)
    print("创建示例不完整牌谱")
    print("=" * 60)
    
    # 读取完整数据
    with open("game_data_template_gang_fixed.json", 'r', encoding='utf-8') as f:
        complete_data = json.load(f)
    
    # 创建不完整版本（只保留玩家0的初始手牌）
    incomplete_data = {
        "game_info": {
            "game_id": "incomplete_sample",
            "description": "不完整的牌谱示例（只知道玩家0的初始手牌）"
        },
        "first_hand": {
            "0": complete_data["first_hand"]["0"]  # 只保留玩家0
        },
        "actions": complete_data["actions"],
        "final_hand": complete_data["final_hand"]
    }
    
    # 保存不完整数据
    incomplete_file = "incomplete_sample.json"
    with open(incomplete_file, 'w', encoding='utf-8') as f:
        json.dump(incomplete_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 创建不完整牌谱示例: {incomplete_file}")
    print(f"包含内容:")
    print(f"  - 玩家0的初始手牌: {len(incomplete_data['first_hand']['0'])}张")
    print(f"  - 游戏动作序列: {len(incomplete_data['actions'])}个动作")
    print(f"  - 所有玩家的最终手牌")
    
    return incomplete_file

def main():
    """主函数：运行所有示例"""
    print("🎯 麻将初始手牌推导器使用示例")
    print("基于公式：最初的手牌 = 最后的手牌 + 碰牌中自己的牌 + 碰牌后的出牌 + 杠牌中自己的牌")
    
    # 运行所有示例
    try:
        example_1_basic_usage()
        example_2_analyze_specific_player() 
        example_3_batch_processing()
        example_4_validate_formula()
        
        # 创建示例数据
        incomplete_file = create_sample_incomplete_data()
        
        # 使用示例数据进行推导
        print(f"\n使用创建的不完整数据进行推导:")
        deducer = MahjongInitialHandDeducer(incomplete_file)
        deducer.run_deduction("from_incomplete_sample.json")
        
        print("\n🎉 所有示例运行完成！")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")

if __name__ == "__main__":
    main()