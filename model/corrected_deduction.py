#!/usr/bin/env python3
"""
修正版推导脚本 - 考虑麻将的14张瞬间状态
"""

import json
from collections import Counter

def analyze_mahjong_logic():
    """分析麻将逻辑问题"""
    
    print("🎯 麻将逻辑分析")
    print("=" * 50)
    print("麻将基本规律:")
    print("1. 开局: 每人13张")
    print("2. 轮次: 摸1张(瞬间14张) → 打1张(回到13张)")
    print("3. 假设: 出牌 = 刚摸的牌")
    print("")
    print("问题:")
    print("- 如果出牌 = 刚摸牌，相当于'过手即打'")
    print("- 这种情况下，摸到的牌对初始手牌没有净影响")
    print("- 初始手牌仍应该是13张")
    print("")
    print("两种理解方式:")
    print("方案A: 初始13张 (摸到即打，无净影响)")
    print("方案B: 初始14张 (把第一次摸牌算入初始)")
    
    return True

def corrected_deduction_v1():
    """修正方案A: 初始13张，摸到即打"""
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("\n🔧 方案A: 初始13张推导")
    print("=" * 50)
    print("逻辑: 如果出牌=刚摸牌，则摸牌对手牌构成无净影响")
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    known_initial = game_data['first_hand']['0']
    
    results_v1 = {'0': known_initial}
    
    for player_id in [1, 2, 3]:
        print(f"\n👤 玩家{player_id} (方案A):")
        
        player_actions = [a for a in actions if a['player_id'] == player_id]
        final_data = final_hands[str(player_id)]
        final_hand = final_data['hand']
        melds = final_data.get('melds', [])
        
        # 只统计非"摸到即打"的弃牌
        discards = [a for a in player_actions if a['type'] == 'discard']
        
        # 计算碰杠消耗
        meld_consumption = []
        for meld in melds:
            if meld['type'] == 'peng':
                meld_consumption.extend([meld['tile'][0]] * 2)
        
        print(f"  最终手牌: {len(final_hand)}张")
        print(f"  总弃牌: {len(discards)}次")
        print(f"  碰杠消耗: {len(meld_consumption)}张")
        
        # 假设: 如果都是摸到即打，那么初始手牌 = 最终手牌 + 碰杠消耗
        initial_counter = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # 加上碰杠消耗
        for tile in meld_consumption:
            initial_counter[tile] += 1
        
        # 关键: 不加弃牌，因为假设这些都是摸到即打
        
        deduced_tiles = []
        for tile, count in initial_counter.items():
            deduced_tiles.extend([tile] * count)
        
        deduced_tiles.sort()
        print(f"  推导初始: {deduced_tiles} ({len(deduced_tiles)}张)")
        
        results_v1[str(player_id)] = deduced_tiles
    
    return results_v1

def corrected_deduction_v2():
    """修正方案B: 考虑14张瞬间状态"""
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("\n🔧 方案B: 考虑14张瞬间状态")
    print("=" * 50)
    print("逻辑: 第一次弃牌时是14张状态(13初始+1摸牌)")
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    known_initial = game_data['first_hand']['0']
    
    results_v2 = {'0': known_initial}
    
    for player_id in [1, 2, 3]:
        print(f"\n👤 玩家{player_id} (方案B):")
        
        player_actions = [a for a in actions if a['player_id'] == player_id]
        final_data = final_hands[str(player_id)]
        final_hand = final_data['hand']
        melds = final_data.get('melds', [])
        
        discards = [a for a in player_actions if a['type'] == 'discard']
        
        # 计算碰杠消耗
        meld_consumption = []
        for meld in melds:
            if meld['type'] == 'peng':
                meld_consumption.extend([meld['tile'][0]] * 2)
        
        print(f"  最终手牌: {len(final_hand)}张")
        print(f"  总弃牌: {len(discards)}次")
        print(f"  碰杠消耗: {len(meld_consumption)}张")
        
        # 方案B逻辑:
        # 假设第一次弃牌 = 第一次摸牌
        # 初始手牌 = 最终手牌 + 碰杠消耗 + 第一次弃牌
        
        initial_counter = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # 加上碰杠消耗
        for tile in meld_consumption:
            initial_counter[tile] += 1
        
        # 加上第一次弃牌(假设这是第一次摸牌)
        if discards:
            first_discard = discards[0]['tile']
            initial_counter[first_discard] += 1
            print(f"  第一次弃牌: {first_discard} (假设为第一次摸牌)")
        
        deduced_tiles = []
        for tile, count in initial_counter.items():
            deduced_tiles.extend([tile] * count)
        
        deduced_tiles.sort()
        print(f"  推导初始: {deduced_tiles} ({len(deduced_tiles)}张)")
        
        results_v2[str(player_id)] = deduced_tiles
    
    return results_v2

def create_both_versions():
    """创建两个版本的结果"""
    
    analyze_mahjong_logic()
    
    results_v1 = corrected_deduction_v1()
    results_v2 = corrected_deduction_v2()
    
    print("\n📊 两种方案对比:")
    print("=" * 50)
    
    for player_id in ['0', '1', '2', '3']:
        v1_count = len(results_v1[player_id])
        v2_count = len(results_v2[player_id]) if player_id != '0' else len(results_v2[player_id])
        
        if player_id == '0':
            print(f"玩家{player_id}: ✅ 真实已知 ({v1_count}张)")
        else:
            print(f"玩家{player_id}: 方案A={v1_count}张, 方案B={v2_count}张")
    
    # 用户选择哪种方案
    print(f"\n🤔 您认为哪种更合理?")
    print(f"方案A: 初始13张 (摸到即打无净影响)")
    print(f"方案B: 初始实际手牌+第一次摸牌")
    
    # 我推荐方案A，但生成两个文件让用户选择
    
    # 生成方案A的all.json
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    all_v1 = {
        "game_info": {
            "game_id": "real_game_v1",
            "description": "方案A: 初始13张推导",
            "logic": "摸到即打无净影响"
        },
        "initial_hands": {},
        "actions": game_data['actions'],
        "final_hands": game_data['final_hand']
    }
    
    all_v2 = {
        "game_info": {
            "game_id": "real_game_v2", 
            "description": "方案B: 考虑14张瞬间状态",
            "logic": "第一次弃牌=第一次摸牌"
        },
        "initial_hands": {},
        "actions": game_data['actions'],
        "final_hands": game_data['final_hand']
    }
    
    for player_id in ['0', '1', '2', '3']:
        all_v1['initial_hands'][player_id] = {
            "tiles": results_v1[player_id],
            "count": len(results_v1[player_id])
        }
        
        all_v2['initial_hands'][player_id] = {
            "tiles": results_v2[player_id],
            "count": len(results_v2[player_id])
        }
    
    # 根据分析，方案B更合理：考虑14张瞬间状态
    with open('all.json', 'w', encoding='utf-8') as f:
        json.dump(all_v2, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已生成 all.json (采用方案B: 考虑14张瞬间状态)")
    print(f"💡 推荐理由: 第一次弃牌=第一次摸牌，更符合'出牌=最近摸牌'的假设")

if __name__ == "__main__":
    create_both_versions()