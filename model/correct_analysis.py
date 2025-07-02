#!/usr/bin/env python3
"""
正确分析麻将牌谱 - 考虑轮次和摸牌规律
"""

import json
from collections import Counter

def analyze_turns_and_draws(file_path: str):
    """分析轮次和摸牌规律"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    actions = game_data.get('actions', [])
    
    print("🎯 轮次分析")
    print("=" * 60)
    
    # 分析每个玩家在每个轮次的操作
    turns = []
    current_turn = {'player': 0, 'actions': []}
    
    for action in actions:
        player_id = action['player_id']
        action_type = action['type']
        
        if action_type == 'draw':
            # 摸牌标志着新的轮次开始
            if current_turn['actions']:
                turns.append(current_turn)
            current_turn = {'player': player_id, 'actions': [action]}
        elif action_type in ['peng', 'gang', 'jiagang', 'hu', 'zimo']:
            # 特殊操作可能改变轮次
            current_turn['actions'].append(action)
            if action_type in ['peng', 'gang', 'jiagang']:
                # 碰杠后轮次转移到操作玩家
                turns.append(current_turn)
                current_turn = {'player': player_id, 'actions': []}
        else:
            # 普通弃牌
            current_turn['actions'].append(action)
    
    if current_turn['actions']:
        turns.append(current_turn)
    
    print(f"总轮次数: {len(turns)}")
    
    # 统计每个玩家应该摸牌的次数
    expected_draws = {0: 0, 1: 0, 2: 0, 3: 0}
    actual_draws = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # 计算实际摸牌次数
    for action in actions:
        if action['type'] == 'draw':
            actual_draws[action['player_id']] += 1
    
    print(f"\n📊 摸牌统计:")
    for player_id in [0, 1, 2, 3]:
        print(f"  玩家{player_id}: 实际摸牌 {actual_draws[player_id]} 次")
    
    # 分析问题
    print(f"\n⚠️ 问题分析:")
    print("在麻将游戏中，除了玩家0，其他玩家的摸牌没有记录！")
    print("这是现实情况：我们不知道其他玩家摸到的具体牌面。")
    
    return turns, actual_draws

def estimate_missing_draws(game_data: dict) -> dict:
    """估算缺失的摸牌次数"""
    
    actions = game_data.get('actions', [])
    final_hands = game_data.get('final_hand', {})
    
    # 统计每个玩家的操作
    player_stats = {}
    
    for player_id in ['1', '2', '3']:  # 除了玩家0
        stats = {
            'discards': 0,
            'pengs': 0,
            'gangs': 0,
            'final_hand_count': len(final_hands.get(player_id, {}).get('hand', [])),
            'meld_count': len(final_hands.get(player_id, {}).get('melds', []))
        }
        
        for action in actions:
            if action['player_id'] == int(player_id):
                if action['type'] == 'discard':
                    stats['discards'] += 1
                elif action['type'] == 'peng':
                    stats['pengs'] += 1
                elif action['type'] in ['gang', 'jiagang']:
                    stats['gangs'] += 1
        
        # 估算摸牌次数
        # 基本规律：弃牌次数 ≈ 摸牌次数（除了第一次弃牌和特殊情况）
        estimated_draws = stats['discards']
        
        # 调整：碰杠会影响手牌数量
        meld_consumption = 0
        for meld in final_hands.get(player_id, {}).get('melds', []):
            if meld['type'] == 'peng':
                meld_consumption += 2  # 碰牌消耗2张手牌
            elif meld['type'] == 'gang':
                meld_consumption += 3  # 明杠消耗3张手牌
            elif meld['type'] == 'jiagang':
                meld_consumption += 1  # 加杠消耗1张手牌
        
        stats['meld_consumption'] = meld_consumption
        stats['estimated_draws'] = estimated_draws
        
        player_stats[player_id] = stats
    
    return player_stats

def correct_deduction(game_data: dict) -> dict:
    """正确的推导方法"""
    
    print("\n🔧 修正推导方法")
    print("=" * 60)
    
    final_hands = game_data.get('final_hand', {})
    actions = game_data.get('actions', [])
    known_initial = game_data.get('first_hand', {})
    
    deduced_hands = {}
    
    for player_id in ['0', '1', '2', '3']:
        print(f"\n👤 玩家{player_id}分析:")
        
        if player_id in known_initial:
            print(f"  ✅ 已知初始手牌: {known_initial[player_id]}")
            deduced_hands[player_id] = known_initial[player_id]
            continue
        
        # 获取最终状态
        final_data = final_hands.get(player_id, {})
        final_hand = final_data.get('hand', [])
        melds = final_data.get('melds', [])
        
        # 统计操作
        player_actions = [a for a in actions if a['player_id'] == int(player_id)]
        draws = [a for a in player_actions if a['type'] == 'draw']
        discards = [a for a in player_actions if a['type'] == 'discard']
        
        print(f"  📊 操作统计:")
        print(f"    最终手牌: {len(final_hand)}张")
        print(f"    弃牌: {len(discards)}次")
        print(f"    已知摸牌: {len(draws)}次")
        print(f"    碰杠: {len(melds)}次")
        
        # 计算碰杠消耗
        meld_consumption = []
        for meld in melds:
            meld_type = meld['type']
            if meld_type == 'peng':
                meld_consumption.extend([meld['tile'][0]] * 2)
            elif meld_type == 'gang':
                meld_consumption.extend([meld['tile'][0]] * 3)
            elif meld_type == 'jiagang':
                meld_consumption.extend([meld['tile'][0]] * 1)
        
        # 由于没有记录其他玩家的摸牌，我们假设：
        # 估算摸牌次数 = 弃牌次数 + 调整
        estimated_draws = len(discards)
        
        print(f"  🔍 推导策略:")
        print(f"    假设摸牌次数 ≈ 弃牌次数 = {estimated_draws}次")
        print(f"    已知摸牌: {[a['tile'] for a in draws]}")
        print(f"    弃牌: {[a['tile'] for a in discards]}")
        print(f"    碰杠消耗: {meld_consumption}")
        
        # 计算"至少需要的牌"
        initial_counter = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # 加上弃牌
        for action in discards:
            initial_counter[action['tile']] += 1
        
        # 加上碰杠消耗
        for tile in meld_consumption:
            initial_counter[tile] += 1
        
        # 减去已知摸牌
        for action in draws:
            initial_counter[action['tile']] -= 1
        
        known_tiles = []
        for tile, count in initial_counter.items():
            if count > 0:
                known_tiles.extend([tile] * count)
        
        known_tiles.sort()
        unknown_draw_count = estimated_draws - len(draws)
        
        print(f"  🎯 推导结果:")
        print(f"    已知必须有的牌: {known_tiles} ({len(known_tiles)}张)")
        print(f"    未知摸牌需求: {unknown_draw_count}张")
        print(f"    总计: {len(known_tiles)} + {unknown_draw_count} = {len(known_tiles) + unknown_draw_count}张")
        
        if len(known_tiles) + unknown_draw_count == 13:
            print(f"    ✅ 数量正确!")
        else:
            print(f"    ⚠️ 数量异常，可能数据不完整")
        
        deduced_hands[player_id] = {
            'known_tiles': known_tiles,
            'unknown_draws': unknown_draw_count,
            'estimated_total': len(known_tiles) + unknown_draw_count
        }
    
    return deduced_hands

def create_realistic_complete_data(input_file: str, output_file: str):
    """创建符合现实的完整数据"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    # 进行正确的推导
    deduced_hands = correct_deduction(game_data)
    
    # 更新数据格式以符合现实
    realistic_data = game_data.copy()
    realistic_data['deduced_initial_hands'] = deduced_hands
    
    # 添加说明
    realistic_data['deduction_notes'] = {
        "method": "现实情况推导",
        "limitations": [
            "玩家1,2,3的摸牌内容未知",
            "只能推导出'至少需要的牌'",
            "存在多种可能的初始手牌组合"
        ],
        "accuracy": {
            "player_0": "100% (已知)",
            "player_1": "部分准确 (未知摸牌影响)",
            "player_2": "部分准确 (未知摸牌影响)", 
            "player_3": "部分准确 (未知摸牌影响)"
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(realistic_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 现实情况的完整数据已保存到: {output_file}")
    
    return realistic_data

if __name__ == "__main__":
    # 分析轮次和摸牌
    turns, draws = analyze_turns_and_draws('game_data_template_gang_fixed.json')
    
    # 估算缺失摸牌
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    missing_stats = estimate_missing_draws(game_data)
    
    print(f"\n📈 其他玩家估算:")
    for player_id, stats in missing_stats.items():
        print(f"  玩家{player_id}: 弃牌{stats['discards']}次, 估算摸牌{stats['estimated_draws']}次")
    
    # 正确推导
    deduced = correct_deduction(game_data)
    
    # 创建完整数据
    create_realistic_complete_data(
        'game_data_template_gang_fixed.json',
        'game_data_template_gang_all.json'
    )