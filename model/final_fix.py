#!/usr/bin/env python3
"""
最终修复 - 发现根本问题
"""

import json
from collections import Counter

def analyze_fundamental_issue():
    """分析根本问题"""
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("🔍 根本问题分析")
    print("=" * 60)
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    
    # 重新理解数据结构
    print("关键发现:")
    print("1. 这个数据记录的是一个麻将牌谱")
    print("2. 只有玩家0的摸牌被记录了")
    print("3. 其他玩家的摸牌在现实中是隐藏的")
    print("4. 但是，我们需要理解：每个玩家实际上都摸了牌！")
    
    # 分析每个玩家的轮次
    print(f"\n🔄 轮次分析:")
    
    # 统计每个玩家的弃牌轮次
    player_discard_rounds = {0: [], 1: [], 2: [], 3: []}
    
    for action in actions:
        if action['type'] == 'discard':
            player_id = action['player_id']
            player_discard_rounds[player_id].append(action['sequence'])
    
    for player_id in [0, 1, 2, 3]:
        rounds = player_discard_rounds[player_id]
        print(f"  玩家{player_id}: 弃牌{len(rounds)}轮")
    
    # 关键洞察：在真实麻将中
    print(f"\n💡 关键洞察:")
    print("在真实麻将游戏中：")
    print("- 除了第一轮弃牌（使用初始手牌），每次弃牌前都要摸牌")
    print("- 即：弃牌轮数 ≈ 摸牌次数（除了一些特殊情况）")
    print("- 碰杠后的弃牌不需要摸牌")
    
    # 重新计算
    print(f"\n🧮 重新计算:")
    
    for player_id in [1, 2, 3]:  # 跳过玩家0
        final_data = final_hands[str(player_id)]
        final_hand = final_data['hand']
        melds = final_data['melds']
        
        # 统计操作
        player_actions = [a for a in actions if a['player_id'] == player_id]
        discards = [a for a in player_actions if a['type'] == 'discard']
        pengs = [a for a in player_actions if a['type'] == 'peng']
        
        print(f"\n  👤 玩家{player_id}:")
        print(f"    最终手牌: {len(final_hand)}张")
        print(f"    弃牌次数: {len(discards)}次")
        print(f"    碰牌次数: {len(pengs)}次")
        
        # 计算碰杠后的手牌减少
        meld_reduction = 0
        for meld in melds:
            if meld['type'] == 'peng':
                meld_reduction += 2
        
        print(f"    碰杠手牌减少: {meld_reduction}张")
        
        # 关键！重新理解弃牌-摸牌关系
        # 第一次弃牌：用初始手牌
        # 后续弃牌：摸牌后弃牌
        # 碰牌后弃牌：不摸牌
        
        # 估算实际摸牌次数 = 弃牌次数 - 1 - 碰牌后的弃牌次数
        
        # 简化：假设除了第一次弃牌，其他都是摸牌后弃牌
        estimated_draws = len(discards) - 1  # 减去第一次弃牌
        
        if estimated_draws < 0:
            estimated_draws = 0
            
        print(f"    估算摸牌次数: {len(discards)} - 1 = {estimated_draws}次")
        
        # 验证手牌数量关系
        # 13(初始) + 摸牌 - 弃牌 - 碰杠消耗 = 最终手牌
        theoretical_final = 13 + estimated_draws - len(discards) - meld_reduction
        
        print(f"    理论最终手牌: 13 + {estimated_draws} - {len(discards)} - {meld_reduction} = {theoretical_final}张")
        print(f"    实际最终手牌: {len(final_hand)}张")
        
        if theoretical_final == len(final_hand):
            print(f"    ✅ 数量匹配!")
        else:
            diff = len(final_hand) - theoretical_final
            print(f"    ⚠️ 差异: {diff}张")
            # 调整估算
            adjusted_draws = estimated_draws + diff
            print(f"    调整后摸牌: {adjusted_draws}次")

def create_final_correct_data():
    """创建最终正确的数据"""
    
    analyze_fundamental_issue()
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print(f"\n🔧 创建最终正确数据")
    print("=" * 60)
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    known_initial = game_data.get('first_hand', {})
    
    results = {}
    
    for player_id in ['0', '1', '2', '3']:
        print(f"\n👤 玩家{player_id}:")
        
        if player_id in known_initial:
            initial = known_initial[player_id]
            print(f"  ✅ 已知初始手牌: {len(initial)}张")
            results[player_id] = {
                'type': 'known',
                'tiles': initial,
                'count': len(initial)
            }
            continue
        
        final_data = final_hands[player_id]
        final_hand = final_data['hand'] 
        melds = final_data['melds']
        
        # 统计操作
        player_actions = [a for a in actions if a['player_id'] == int(player_id)]
        discards = [a for a in player_actions if a['type'] == 'discard']
        recorded_draws = [a for a in player_actions if a['type'] == 'draw']
        
        # 计算碰杠消耗和手牌减少
        meld_consumption = []
        meld_reduction = 0
        
        for meld in melds:
            if meld['type'] == 'peng':
                meld_reduction += 2
                meld_consumption.extend([meld['tile'][0]] * 2)
        
        # 关键修正：基于手牌数量平衡来推导
        # 13(初始) + 摸牌 - 弃牌 - 碰杠消耗 = 最终手牌
        # 推导：摸牌 = 最终手牌 + 弃牌 + 碰杠消耗 - 13
        
        total_draws_needed = len(final_hand) + len(discards) + meld_reduction - 13
        unknown_draws = total_draws_needed - len(recorded_draws)
        
        print(f"  📊 平衡计算:")
        print(f"    需要总摸牌: {len(final_hand)} + {len(discards)} + {meld_reduction} - 13 = {total_draws_needed}")
        print(f"    已知摸牌: {len(recorded_draws)}")
        print(f"    未知摸牌: {unknown_draws}")
        
        # 推导已知的初始手牌部分
        initial_counter = Counter()
        
        # 最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
            
        # 弃牌
        for action in discards:
            initial_counter[action['tile']] += 1
            
        # 碰杠消耗
        for tile in meld_consumption:
            initial_counter[tile] += 1
            
        # 减去已知摸牌
        for action in recorded_draws:
            initial_counter[action['tile']] -= 1
        
        # 已知部分
        known_tiles = []
        for tile, count in initial_counter.items():
            if count > 0:
                known_tiles.extend([tile] * count)
        
        known_tiles.sort()
        
        print(f"  🎯 推导结果:")
        print(f"    已知初始牌: {len(known_tiles)}张")
        print(f"    未知摸牌: {unknown_draws}张") 
        print(f"    总计: {len(known_tiles)} + {unknown_draws} = {len(known_tiles) + unknown_draws}张")
        
        # 这次应该等于13
        if len(known_tiles) + unknown_draws == 13:
            print(f"    ✅ 总数正确!")
        else:
            print(f"    ⚠️ 仍有问题")
        
        results[player_id] = {
            'type': 'partially_deduced',
            'known_tiles': known_tiles,
            'unknown_draws': unknown_draws,
            'total_count': len(known_tiles) + unknown_draws
        }
    
    # 保存最终正确的数据
    final_data = {
        "game_info": game_data['game_info'],
        "mjtype": game_data['mjtype'],
        "misssuit": game_data['misssuit'], 
        "dong": game_data['dong'],
        
        "final_correct_initial_hands": results,
        
        "actions": game_data['actions'],
        "final_hand": game_data['final_hand'],
        
        "analysis_notes": {
            "method": "基于手牌数量平衡的推导",
            "formula": "初始13张 + 摸牌 - 弃牌 - 碰杠消耗 = 最终手牌",
            "confidence": "玩家0: 100%, 其他玩家: 部分确定",
            "limitation": "其他玩家的摸牌内容无法确定"
        }
    }
    
    with open('game_data_template_gang_all.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 最终正确数据已保存!")
    print(f"\n📋 最终总结:")
    
    for player_id, result in results.items():
        if result['type'] == 'known':
            print(f"  玩家{player_id}: ✅ 已知 ({result['count']}张)")
        else:
            print(f"  玩家{player_id}: 🔍 推导 ({len(result['known_tiles'])}张已知 + {result['unknown_draws']}张未知 = {result['total_count']}张)")

if __name__ == "__main__":
    create_final_correct_data()