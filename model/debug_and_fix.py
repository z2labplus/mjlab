#!/usr/bin/env python3
"""
调试并修复手牌推导问题
"""

import json
from collections import Counter

def debug_player_actions():
    """调试玩家操作，找出问题所在"""
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("🔍 调试分析 - 找出推导错误的原因")
    print("=" * 60)
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    
    # 分析玩家1的问题
    print("\n👤 玩家1详细调试:")
    
    final_data = final_hands['1']
    final_hand = final_data['hand']
    melds = final_data['melds']
    
    print(f"最终手牌: {final_hand} ({len(final_hand)}张)")
    print(f"明牌组合: {melds}")
    
    # 统计玩家1的所有操作
    player1_actions = [a for a in actions if a['player_id'] == 1]
    
    draws = []
    discards = []
    pengs = []
    
    for action in player1_actions:
        if action['type'] == 'draw':
            draws.append(action['tile'])
        elif action['type'] == 'discard':
            discards.append(action['tile'])
        elif action['type'] == 'peng':
            pengs.append(action['tile'])
    
    print(f"摸牌操作: {draws} ({len(draws)}次)")
    print(f"弃牌操作: {discards} ({len(discards)}次)")
    print(f"碰牌操作: {pengs} ({len(pengs)}次)")
    
    # 关键问题：我之前的逻辑错误！
    print(f"\n🔍 问题分析:")
    print(f"错误假设: 弃牌次数 = 摸牌次数")
    print(f"实际情况: 玩家1弃牌{len(discards)}次，但摸牌{len(draws)}次")
    print(f"这说明有{len(discards) - len(draws)}次摸牌没有记录")
    
    # 重新思考：麻将的基本规律
    print(f"\n💡 正确的思考:")
    print(f"1. 每个玩家开局13张牌")
    print(f"2. 正常轮次：摸1张 → 打1张")
    print(f"3. 碰牌：手牌减少2张，但不摸牌")
    print(f"4. 最终手牌数 = 13 - 碰杠消耗的手牌数")
    
    # 验证最终手牌数
    meld_consumption = 0
    for meld in melds:
        if meld['type'] == 'peng':
            meld_consumption += 2  # 碰牌消耗2张手牌
    
    expected_final = 13 - meld_consumption
    actual_final = len(final_hand)
    
    print(f"\n📊 手牌数验证:")
    print(f"预期最终手牌: 13 - {meld_consumption} = {expected_final}张")
    print(f"实际最终手牌: {actual_final}张")
    
    if expected_final == actual_final:
        print(f"✅ 手牌数正确!")
    else:
        print(f"❌ 手牌数异常!")
        
    return draws, discards, pengs, meld_consumption

def correct_deduction_logic():
    """正确的推导逻辑"""
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("\n🔧 修正后的推导逻辑")
    print("=" * 60)
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    known_initial = game_data.get('first_hand', {})
    
    # 关键洞察：在麻将中，除了第一次出牌，每次出牌前都要摸牌
    # 但其他玩家的摸牌我们看不到！
    
    # 重新分析：计算每个玩家实际应该摸了多少次牌
    
    results = {}
    
    for player_id in ['0', '1', '2', '3']:
        print(f"\n👤 玩家{player_id}修正分析:")
        
        if player_id in known_initial:
            print(f"  ✅ 已知初始手牌: {known_initial[player_id]} ({len(known_initial[player_id])}张)")
            results[player_id] = known_initial[player_id]
            continue
        
        final_data = final_hands[player_id]
        final_hand = final_data['hand']
        melds = final_data['melds']
        
        # 统计操作
        player_actions = [a for a in actions if a['player_id'] == int(player_id)]
        recorded_draws = [a for a in player_actions if a['type'] == 'draw']
        discards = [a for a in player_actions if a['type'] == 'discard']
        
        # 计算碰杠消耗
        meld_consumption_tiles = []
        meld_hand_reduction = 0
        
        for meld in melds:
            if meld['type'] == 'peng':
                meld_hand_reduction += 2
                meld_consumption_tiles.extend([meld['tile'][0]] * 2)
            elif meld['type'] == 'gang':
                meld_hand_reduction += 3
                meld_consumption_tiles.extend([meld['tile'][0]] * 3)
            elif meld['type'] == 'jiagang':
                meld_hand_reduction += 1
                meld_consumption_tiles.extend([meld['tile'][0]] * 1)
        
        print(f"  📊 数据:")
        print(f"    最终手牌: {len(final_hand)}张")
        print(f"    弃牌: {len(discards)}次")
        print(f"    记录的摸牌: {len(recorded_draws)}次")
        print(f"    碰杠消耗手牌: {meld_hand_reduction}张")
        
        # 关键修正：麻将规则
        # 初始13张 + 总摸牌数 - 总弃牌数 - 碰杠消耗 = 最终手牌数
        # 推导：总摸牌数 = 最终手牌数 + 总弃牌数 + 碰杠消耗 - 13
        
        expected_total_draws = len(final_hand) + len(discards) + meld_hand_reduction - 13
        unknown_draws = expected_total_draws - len(recorded_draws)
        
        print(f"  🧮 摸牌计算:")
        print(f"    理论总摸牌数: {len(final_hand)} + {len(discards)} + {meld_hand_reduction} - 13 = {expected_total_draws}")
        print(f"    已知摸牌: {len(recorded_draws)}次")
        print(f"    未知摸牌: {unknown_draws}次")
        
        # 现在用正确的公式推导初始手牌
        # 初始手牌 = 最终手牌 + 弃牌 + 碰杠消耗 - 总摸牌
        initial_counter = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # 加上弃牌
        for action in discards:
            initial_counter[action['tile']] += 1
        
        # 加上碰杠消耗
        for tile in meld_consumption_tiles:
            initial_counter[tile] += 1
        
        # 减去已知摸牌
        for action in recorded_draws:
            initial_counter[action['tile']] -= 1
        
        # 计算已知的初始手牌部分
        known_initial_tiles = []
        for tile, count in initial_counter.items():
            if count > 0:
                known_initial_tiles.extend([tile] * count)
            elif count < 0:
                print(f"    ⚠️ 牌'{tile}'计算为负数")
        
        known_initial_tiles.sort()
        
        print(f"  🎯 修正结果:")
        print(f"    已知初始牌: {len(known_initial_tiles)}张")
        print(f"    未知摸牌需求: {unknown_draws}张")
        print(f"    总计: {len(known_initial_tiles)} + {unknown_draws} = {len(known_initial_tiles) + unknown_draws}张")
        
        if len(known_initial_tiles) + unknown_draws == 13:
            print(f"    ✅ 总数正确!")
        else:
            print(f"    ❌ 总数仍然异常")
        
        results[player_id] = {
            'known_tiles': known_initial_tiles,
            'unknown_draws': unknown_draws,
            'total': len(known_initial_tiles) + unknown_draws
        }
    
    return results

def create_fixed_output():
    """创建修正后的输出文件"""
    
    # 先调试
    debug_player_actions()
    
    # 用正确逻辑推导
    results = correct_deduction_logic()
    
    # 读取原始数据
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 创建修正后的完整数据
    fixed_complete = {
        "game_info": original_data['game_info'],
        "mjtype": original_data['mjtype'], 
        "misssuit": original_data['misssuit'],
        "dong": original_data['dong'],
        
        # 修正后的初始手牌
        "corrected_initial_hands": {
            "0": {
                "type": "known",
                "tiles": results['0'],
                "count": len(results['0']) if isinstance(results['0'], list) else 13
            },
            "1": {
                "type": "partially_deduced",
                "known_tiles": results['1']['known_tiles'],
                "unknown_count": results['1']['unknown_draws'],
                "total_count": results['1']['total']
            },
            "2": {
                "type": "partially_deduced", 
                "known_tiles": results['2']['known_tiles'],
                "unknown_count": results['2']['unknown_draws'],
                "total_count": results['2']['total']
            },
            "3": {
                "type": "partially_deduced",
                "known_tiles": results['3']['known_tiles'], 
                "unknown_count": results['3']['unknown_draws'],
                "total_count": results['3']['total']
            }
        },
        
        "actions": original_data['actions'],
        "final_hand": original_data['final_hand'],
        
        "fix_notes": {
            "problem": "之前的推导逻辑错误：误以为弃牌数=摸牌数",
            "correction": "使用麻将基本规则：初始13张 + 摸牌 - 弃牌 - 碰杠消耗 = 最终手牌",
            "reality": "其他玩家的摸牌内容仍然未知，但总数应该是13张"
        }
    }
    
    # 保存修正后的文件
    with open('game_data_template_gang_all.json', 'w', encoding='utf-8') as f:
        json.dump(fixed_complete, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 修正后的数据已保存")
    print(f"\n📋 修正总结:")
    
    for player_id, result in results.items():
        if isinstance(result, list):
            print(f"  玩家{player_id}: ✅ 已知 ({len(result)}张)")
        else:
            print(f"  玩家{player_id}: 🔍 推导 ({len(result['known_tiles'])}张已知 + {result['unknown_draws']}张未知 = {result['total']}张)")

if __name__ == "__main__":
    create_fixed_output()