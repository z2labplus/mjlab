#!/usr/bin/env python3
"""
简洁正确的手牌推导 - 专注于核心逻辑
"""

import json
from collections import Counter

def simple_deduction():
    """简洁的手牌推导"""
    
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("🎯 简洁正确的初始手牌推导")
    print("=" * 60)
    
    actions = game_data['actions']
    final_hands = game_data['final_hand']
    known_initial = game_data.get('first_hand', {})
    
    results = {}
    
    for player_id in ['0', '1', '2', '3']:
        print(f"\n👤 玩家{player_id}:")
        
        # 玩家0已知
        if player_id in known_initial:
            initial = known_initial[player_id]
            print(f"  ✅ 已知初始手牌: {initial} ({len(initial)}张)")
            results[player_id] = initial
            continue
        
        # 其他玩家需要推导
        final_data = final_hands[player_id]
        final_hand = final_data['hand']
        melds = final_data['melds']
        
        print(f"  📊 最终状态:")
        print(f"    手牌: {final_hand} ({len(final_hand)}张)")
        print(f"    明牌组合: {len(melds)}组")
        
        # 统计操作
        player_actions = [a for a in actions if a['player_id'] == int(player_id)]
        draws = [a for a in player_actions if a['type'] == 'draw']
        discards = [a for a in player_actions if a['type'] == 'discard']
        
        print(f"  📋 操作记录:")
        print(f"    摸牌: {len(draws)}次 {[a['tile'] for a in draws]}")
        print(f"    弃牌: {len(discards)}次 {[a['tile'] for a in discards]}")
        
        # 关键洞察：其他玩家的摸牌我们无法观察！
        # 但我们知道：初始13张 + 摸牌N张 - 弃牌N张 - 碰杠消耗 = 最终手牌
        
        # 计算碰杠消耗
        meld_consumption = []
        for meld in melds:
            if meld['type'] == 'peng':
                meld_consumption.extend([meld['tile'][0]] * 2)  # 碰消耗2张手牌
            elif meld['type'] == 'gang':
                meld_consumption.extend([meld['tile'][0]] * 3)  # 明杠消耗3张手牌
        
        print(f"    碰杠消耗: {meld_consumption}")
        
        # 核心推导公式：
        # 初始手牌 = 最终手牌 + 弃牌 + 碰杠消耗 - 已知摸牌 - 未知摸牌
        
        # 计算已知部分
        known_tiles = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            known_tiles[tile] += 1
        
        # 加上弃牌
        for action in discards:
            known_tiles[action['tile']] += 1
        
        # 加上碰杠消耗
        for tile in meld_consumption:
            known_tiles[tile] += 1
        
        # 减去已知摸牌
        for action in draws:
            known_tiles[action['tile']] -= 1
        
        # 转换为列表
        certain_tiles = []
        for tile, count in known_tiles.items():
            if count > 0:
                certain_tiles.extend([tile] * count)
            elif count < 0:
                print(f"    ⚠️ 牌'{tile}'出现负数，数据异常")
        
        certain_tiles.sort()
        
        # 估算未知摸牌数
        # 在现实中，我们无法确切知道，但可以基于弃牌数估算
        unknown_draws_estimate = len(discards) - len(draws)
        if unknown_draws_estimate < 0:
            unknown_draws_estimate = 0
        
        print(f"  🎯 推导结果:")
        print(f"    确定的牌: {certain_tiles} ({len(certain_tiles)}张)")
        print(f"    估算未知摸牌: {unknown_draws_estimate}张")
        print(f"    推导总数: {len(certain_tiles)} + {unknown_draws_estimate} = {len(certain_tiles) + unknown_draws_estimate}张")
        
        # 现实情况：我们只能确定部分牌，无法完全确定初始手牌
        results[player_id] = {
            'certain_tiles': certain_tiles,
            'unknown_draws': unknown_draws_estimate,
            'note': '现实中无法完全确定，因为不知道对方摸牌内容'
        }
    
    return results

def create_realistic_output():
    """创建符合现实的输出文件"""
    
    # 进行推导
    results = simple_deduction()
    
    # 读取原始数据
    with open('game_data_template_gang_fixed.json', 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 创建现实版本的完整数据
    realistic_complete = {
        "game_info": original_data['game_info'],
        "mjtype": original_data['mjtype'],
        "misssuit": original_data['misssuit'],
        "dong": original_data['dong'],
        
        # 初始手牌（现实版本）
        "initial_hands_realistic": {
            "0": {
                "type": "known",
                "tiles": results['0'],
                "confidence": "100%"
            },
            "1": {
                "type": "partially_deduced", 
                "certain_tiles": results['1']['certain_tiles'],
                "uncertain_count": results['1']['unknown_draws'],
                "confidence": "部分确定",
                "note": "无法知道对方的具体摸牌内容"
            },
            "2": {
                "type": "partially_deduced",
                "certain_tiles": results['2']['certain_tiles'], 
                "uncertain_count": results['2']['unknown_draws'],
                "confidence": "部分确定",
                "note": "无法知道对方的具体摸牌内容"
            },
            "3": {
                "type": "partially_deduced",
                "certain_tiles": results['3']['certain_tiles'],
                "uncertain_count": results['3']['unknown_draws'], 
                "confidence": "部分确定",
                "note": "无法知道对方的具体摸牌内容"
            }
        },
        
        # 原始游戏数据
        "actions": original_data['actions'],
        "final_hand": original_data['final_hand'],
        
        # 说明
        "explanation": {
            "reality_check": "在真实麻将游戏中，我们无法观察到其他玩家的摸牌",
            "what_we_can_deduce": "最终手牌 + 弃牌 + 碰杠消耗的牌",
            "what_we_cannot_deduce": "其他玩家摸到的具体牌面",
            "conclusion": "只能推导出'至少需要这些牌'，无法完全确定初始手牌"
        }
    }
    
    # 保存文件
    with open('game_data_template_gang_all.json', 'w', encoding='utf-8') as f:
        json.dump(realistic_complete, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 现实版本的完整数据已保存")
    print(f"\n📋 推导总结:")
    print(f"  玩家0: ✅ 完全已知 (13张)")
    print(f"  玩家1: 🔍 部分推导 ({len(results['1']['certain_tiles'])}张确定 + {results['1']['unknown_draws']}张未知)")
    print(f"  玩家2: 🔍 部分推导 ({len(results['2']['certain_tiles'])}张确定 + {results['2']['unknown_draws']}张未知)")  
    print(f"  玩家3: 🔍 部分推导 ({len(results['3']['certain_tiles'])}张确定 + {results['3']['unknown_draws']}张未知)")
    
    print(f"\n💡 结论:")
    print(f"  这就是现实情况 - 我们无法完全推导其他玩家的初始手牌！")
    print(f"  只能推导出他们'至少需要哪些牌'，但具体组合有多种可能。")

if __name__ == "__main__":
    create_realistic_output()