#!/usr/bin/env python3
"""
简化的手牌验证器 - 演示如何通过最终状态推导初始手牌
"""

def demonstrate_hand_reconstruction():
    """演示手牌重构的基本原理"""
    
    print("🎯 麻将手牌逆向推导原理演示")
    print("=" * 50)
    
    # 模拟一个简单的游戏过程
    print("📋 游戏过程:")
    
    # 假设的游戏数据
    game_data = {
        "initial_hand": ["1万", "2万", "3万", "4万", "5万", "6万", "7万", "8万", "9万", "1条", "2条", "3条", "4条"],
        "actions": [
            {"type": "draw", "card": "5条"},
            {"type": "discard", "card": "9万"},
            {"type": "draw", "card": "6条"},
            {"type": "discard", "card": "1万"},
            {"type": "peng", "card": "2条", "consumed_from_hand": ["2条", "2条"]},  # 碰牌消耗手牌中的2张2条
        ],
        "final_hand": ["2万", "3万", "4万", "5万", "6万", "7万", "8万", "3条", "4条", "5条", "6条"]  # 剩余11张（碰了3张2条）
    }
    
    print(f"1. 初始手牌 (13张): {game_data['initial_hand']}")
    print(f"2. 最终手牌 (11张): {game_data['final_hand']}")
    print("3. 操作过程:")
    
    # 统计操作
    drawn_cards = []
    discarded_cards = []
    melded_consumed = []
    
    for action in game_data['actions']:
        if action['type'] == 'draw':
            drawn_cards.append(action['card'])
            print(f"   摸牌: {action['card']}")
        elif action['type'] == 'discard':
            discarded_cards.append(action['card'])
            print(f"   弃牌: {action['card']}")
        elif action['type'] == 'peng':
            melded_consumed.extend(action['consumed_from_hand'])
            print(f"   碰牌: {action['card']} (消耗手牌: {action['consumed_from_hand']})")
    
    print("\n🧮 逆向推导过程:")
    print(f"   最终手牌: {game_data['final_hand']} ({len(game_data['final_hand'])}张)")
    print(f"   + 弃牌: {discarded_cards} ({len(discarded_cards)}张)")
    print(f"   + 碰杠消耗: {melded_consumed} ({len(melded_consumed)}张)")
    print(f"   - 摸牌: {drawn_cards} ({len(drawn_cards)}张)")
    
    # 计算推导结果
    reconstructed_hand = []
    reconstructed_hand.extend(game_data['final_hand'])
    reconstructed_hand.extend(discarded_cards)
    reconstructed_hand.extend(melded_consumed)
    
    # 减去摸牌
    for card in drawn_cards:
        if card in reconstructed_hand:
            reconstructed_hand.remove(card)
    
    reconstructed_hand.sort()
    
    print(f"\n✅ 推导结果:")
    print(f"   推导的初始手牌: {reconstructed_hand} ({len(reconstructed_hand)}张)")
    print(f"   实际的初始手牌: {sorted(game_data['initial_hand'])} ({len(game_data['initial_hand'])}张)")
    
    # 验证结果
    if sorted(reconstructed_hand) == sorted(game_data['initial_hand']):
        print("🎉 推导成功！完全匹配！")
    else:
        print("❌ 推导失败，存在差异")
    
    print("\n" + "=" * 50)
    print("💡 结论:")
    print("   在信息完整的情况下，完全可以通过最终状态逆向推导初始手牌！")
    print("   关键是要有：")
    print("   1. 准确的最终手牌")
    print("   2. 完整的操作记录")
    print("   3. 详细的牌面信息")

if __name__ == "__main__":
    demonstrate_hand_reconstruction()