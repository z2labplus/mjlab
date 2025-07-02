#!/usr/bin/env python3
"""
最终正确的分析 - 基于麻将基本规则
"""

import json
from collections import Counter

def final_analysis(file_path: str):
    """基于麻将规则的最终分析"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("🎯 基于麻将规则的正确分析")
    print("=" * 60)
    
    actions = game_data.get('actions', [])
    final_hands = game_data.get('final_hand', {})
    known_initial = game_data.get('first_hand', {})
    
    # 关键洞察：每个玩家在游戏开始时都是13张牌
    # 游戏过程中的变化：摸1张，打1张（保持13张，除非碰杠）
    
    print("📋 麻将基本规则:")
    print("1. 每个玩家初始13张牌")
    print("2. 轮到自己：摸1张 → 打1张")  
    print("3. 碰牌：别人打的+自己手牌2张=3张展示，手牌-2")
    print("4. 杠牌：消耗手牌不同数量")
    print("5. 胡牌时手牌数 = 13 - 碰杠消耗数")
    
    deduced_results = {}
    
    for player_id in ['0', '1', '2', '3']:
        print(f"\n👤 玩家{player_id}详细分析:")
        
        if player_id in known_initial:
            print(f"  ✅ 已知初始手牌: {known_initial[player_id]} ({len(known_initial[player_id])}张)")
            deduced_results[player_id] = {
                'type': 'known',
                'initial_hand': known_initial[player_id]
            }
            continue
        
        # 获取数据
        final_data = final_hands.get(player_id, {})
        final_hand = final_data.get('hand', [])
        melds = final_data.get('melds', [])
        
        # 统计这个玩家的所有操作
        player_actions = [a for a in actions if a['player_id'] == int(player_id)]
        
        draws = [a['tile'] for a in player_actions if a['type'] == 'draw']
        discards = [a['tile'] for a in player_actions if a['type'] == 'discard']
        pengs = [a['tile'] for a in player_actions if a['type'] == 'peng']
        gangs = [a['tile'] for a in player_actions if a['type'] in ['gang', 'jiagang']]
        
        print(f"  📊 数据收集:")
        print(f"    最终手牌: {final_hand} ({len(final_hand)}张)")
        print(f"    已知摸牌: {draws} ({len(draws)}次)")
        print(f"    弃牌: {discards} ({len(discards)}次)")
        print(f"    碰牌: {pengs} ({len(pengs)}次)")
        print(f"    杠牌: {gangs} ({len(gangs)}次)")
        
        # 计算碰杠对手牌的影响
        meld_hand_reduction = 0  # 碰杠导致的手牌减少
        meld_consumption = []    # 碰杠消耗的具体牌
        
        for meld in melds:
            meld_type = meld['type']
            tile = meld['tile'][0]  # 碰杠的牌
            
            if meld_type == 'peng':
                meld_hand_reduction += 2  # 碰牌：手牌减少2张
                meld_consumption.extend([tile] * 2)
            elif meld_type == 'gang':
                meld_hand_reduction += 3  # 明杠：手牌减少3张  
                meld_consumption.extend([tile] * 3)
            elif meld_type == 'jiagang':
                meld_hand_reduction += 1  # 加杠：手牌减少1张
                meld_consumption.extend([tile] * 1)
        
        print(f"    碰杠影响: 手牌减少{meld_hand_reduction}张")
        print(f"    碰杠消耗: {meld_consumption}")
        
        # 关键计算：理论最终手牌数
        expected_final_hand_count = 13 - meld_hand_reduction
        actual_final_hand_count = len(final_hand)
        
        print(f"  🧮 手牌数验证:")
        print(f"    理论最终手牌: 13 - {meld_hand_reduction} = {expected_final_hand_count}张")
        print(f"    实际最终手牌: {actual_final_hand_count}张")
        
        if actual_final_hand_count == expected_final_hand_count:
            print(f"    ✅ 手牌数正确!")
        else:
            print(f"    ⚠️ 手牌数异常!")
        
        # 推导初始手牌的核心逻辑
        print(f"  🔍 推导逻辑:")
        print(f"    初始手牌 = 最终手牌 + 弃牌 + 碰杠消耗 - 摸牌")
        
        # 已知部分的计算
        initial_counter = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # 加上弃牌  
        for tile in discards:
            initial_counter[tile] += 1
            
        # 加上碰杠消耗
        for tile in meld_consumption:
            initial_counter[tile] += 1
        
        # 减去已知摸牌
        for tile in draws:
            initial_counter[tile] -= 1
        
        # 计算已知的初始手牌部分
        known_initial_tiles = []
        for tile, count in initial_counter.items():
            if count > 0:
                known_initial_tiles.extend([tile] * count)
            elif count < 0:
                print(f"    ⚠️ 警告: 牌'{tile}'出现负数，数据可能有误")
        
        known_initial_tiles.sort()
        
        # 估算未知摸牌数（基于弃牌数）
        # 麻将规律：每摸一张牌，通常会打一张牌（除了碰杠和胡牌的特殊情况）
        unknown_draws_estimate = len(discards) - len(draws)
        
        # 调整：考虑到一些特殊情况
        if unknown_draws_estimate < 0:
            unknown_draws_estimate = 0
        
        total_estimated = len(known_initial_tiles) + unknown_draws_estimate
        
        print(f"  🎯 推导结果:")
        print(f"    已知初始牌: {known_initial_tiles} ({len(known_initial_tiles)}张)")
        print(f"    估算未知摸牌: {unknown_draws_estimate}张")
        print(f"    估算总初始牌数: {len(known_initial_tiles)} + {unknown_draws_estimate} = {total_estimated}张")
        
        # 验证结果合理性
        if total_estimated == 13:
            print(f"    ✅ 总数正确，推导合理!")
            confidence = 0.8  # 较高置信度
        elif 10 <= total_estimated <= 16:
            print(f"    ⚠️ 总数接近13，基本合理")
            confidence = 0.6  # 中等置信度
        else:
            print(f"    ❌ 总数异常，可能有问题")
            confidence = 0.3  # 低置信度
        
        deduced_results[player_id] = {
            'type': 'deduced',
            'known_tiles': known_initial_tiles,
            'unknown_draws': unknown_draws_estimate,
            'total_estimated': total_estimated,
            'confidence': confidence,
            'final_hand_verification': actual_final_hand_count == expected_final_hand_count
        }
    
    return deduced_results

def create_final_complete_data(input_file: str, output_file: str):
    """创建最终的完整数据文件"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    # 进行最终分析
    deduced_results = final_analysis(game_data)
    
    # 创建完整的数据结构
    complete_data = {
        "game_info": game_data.get("game_info", {}),
        "mjtype": game_data.get("mjtype"),
        "misssuit": game_data.get("misssuit", {}),
        "dong": game_data.get("dong"),
        
        # 完整的初始手牌数据
        "complete_initial_hands": {},
        
        # 原始数据
        "actions": game_data.get("actions", []),
        "final_hand": game_data.get("final_hand", {}),
        
        # 推导信息
        "deduction_analysis": deduced_results,
        
        # 元数据
        "analysis_metadata": {
            "method": "基于麻将规则的逆向推导",
            "date": "2024",
            "confidence_levels": {
                "player_0": "100% (已知数据)",
                "player_1": f"{deduced_results.get('1', {}).get('confidence', 0)*100:.0f}% (推导)",
                "player_2": f"{deduced_results.get('2', {}).get('confidence', 0)*100:.0f}% (推导)", 
                "player_3": f"{deduced_results.get('3', {}).get('confidence', 0)*100:.0f}% (推导)"
            },
            "limitations": [
                "玩家1,2,3的摸牌内容在现实中不可知",
                "推导基于'弃牌数≈摸牌数'的假设",
                "存在多种可能的初始手牌组合",
                "置信度基于数据完整性和逻辑一致性"
            ]
        }
    }
    
    # 填入完整的初始手牌
    for player_id, result in deduced_results.items():
        if result['type'] == 'known':
            complete_data["complete_initial_hands"][player_id] = result['initial_hand']
        else:
            # 对于推导的玩家，提供最可能的初始手牌组合
            complete_data["complete_initial_hands"][player_id] = {
                "certain_tiles": result['known_tiles'],
                "uncertain_slots": result['unknown_draws'],
                "note": f"确定{len(result['known_tiles'])}张，不确定{result['unknown_draws']}张"
            }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 最终完整数据已保存到: {output_file}")
    print(f"\n📈 推导总结:")
    
    for player_id, result in deduced_results.items():
        if result['type'] == 'known':
            print(f"  玩家{player_id}: ✅ 已知 ({len(result['initial_hand'])}张)")
        else:
            confidence_pct = int(result['confidence'] * 100)
            print(f"  玩家{player_id}: 🔍 推导 ({len(result['known_tiles'])}张确定 + {result['unknown_draws']}张未知, 置信度{confidence_pct}%)")
    
    return complete_data

if __name__ == "__main__":
    # 进行最终正确的分析
    results = final_analysis('game_data_template_gang_fixed.json')
    
    # 创建最终完整数据
    complete_data = create_final_complete_data(
        'game_data_template_gang_fixed.json',
        'game_data_template_gang_all.json'
    )