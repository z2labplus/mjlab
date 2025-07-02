#!/usr/bin/env python3
"""
分析真实麻将牌谱，推导玩家初始手牌
"""

import json
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

def analyze_mahjong_game(file_path: str):
    """分析麻将游戏牌谱"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    print("🎯 麻将牌谱分析")
    print("=" * 60)
    
    # 基本信息
    print(f"游戏类型: {game_data.get('mjtype', '未知')}")
    print(f"庄家: 玩家{game_data.get('dong', '未知')}")
    print(f"缺门: {game_data.get('misssuit', {})}")
    
    # 已知的初始手牌
    first_hands = game_data.get('first_hand', {})
    print(f"\n📋 已知初始手牌:")
    for player_id, hand in first_hands.items():
        print(f"  玩家{player_id}: {hand} ({len(hand)}张)")
    
    # 最终状态
    final_hands = game_data.get('final_hand', {})
    print(f"\n🎴 最终手牌状态:")
    for player_id, data in final_hands.items():
        print(f"  玩家{player_id}:")
        print(f"    手牌: {data.get('hand', [])} ({len(data.get('hand', []))}张)")
        if 'melds' in data:
            for meld in data['melds']:
                print(f"    {meld['type']}: {meld['tile']}")
        if 'pao_tile' in data:
            print(f"    点炮: {data['pao_tile']}")
        if 'self_win_tile' in data:
            print(f"    自摸: {data['self_win_tile']}")
    
    # 分析操作序列
    actions = game_data.get('actions', [])
    print(f"\n🔄 操作序列分析 (共{len(actions)}步):")
    
    # 统计每个玩家的操作
    player_actions = defaultdict(list)
    for action in actions:
        player_id = str(action['player_id'])
        player_actions[player_id].append(action)
    
    for player_id in ['0', '1', '2', '3']:
        if player_id in player_actions:
            print(f"\n  玩家{player_id}的操作:")
            actions_list = player_actions[player_id]
            
            # 统计操作类型
            draw_count = len([a for a in actions_list if a['type'] == 'draw'])
            discard_count = len([a for a in actions_list if a['type'] == 'discard'])
            peng_count = len([a for a in actions_list if a['type'] == 'peng'])
            gang_count = len([a for a in actions_list if a['type'] in ['gang', 'jiagang']])
            
            print(f"    摸牌: {draw_count}次, 弃牌: {discard_count}次, 碰: {peng_count}次, 杠: {gang_count}次")
            
            # 详细操作
            for action in actions_list[:10]:  # 显示前10个操作
                seq = action['sequence']
                action_type = action['type']
                tile = action.get('tile', '')
                target = action.get('target_player', '')
                
                if action_type == 'draw':
                    print(f"    第{seq}步: 摸牌 {tile}")
                elif action_type == 'discard':
                    print(f"    第{seq}步: 弃牌 {tile}")
                elif action_type in ['peng', 'gang', 'jiagang']:
                    print(f"    第{seq}步: {action_type} {tile} (来自玩家{target})")
                elif action_type in ['hu', 'zimo']:
                    print(f"    第{seq}步: {action_type} {tile}")
            
            if len(actions_list) > 10:
                print(f"    ... 还有{len(actions_list) - 10}个操作")
    
    return game_data

def deduce_initial_hands(game_data: Dict) -> Dict:
    """推导玩家初始手牌"""
    
    print("\n" + "=" * 60)
    print("🧮 开始推导初始手牌")
    
    # 已知初始手牌
    known_initial = game_data.get('first_hand', {})
    final_hands = game_data.get('final_hand', {})
    actions = game_data.get('actions', [])
    
    # 为每个玩家建立操作记录
    player_operations = defaultdict(lambda: {
        'draws': [],
        'discards': [],
        'pengs': [],
        'gangs': [],
        'others': []
    })
    
    # 分析操作序列
    for action in actions:
        player_id = str(action['player_id'])
        action_type = action['type']
        tile = action.get('tile', '')
        
        if action_type == 'draw':
            player_operations[player_id]['draws'].append(tile)
        elif action_type == 'discard':
            player_operations[player_id]['discards'].append(tile)
        elif action_type == 'peng':
            player_operations[player_id]['pengs'].append(tile)
        elif action_type in ['gang', 'jiagang']:
            player_operations[player_id]['gangs'].append(tile)
        else:
            player_operations[player_id]['others'].append(action)
    
    # 推导结果
    deduced_hands = {}
    
    for player_id in ['0', '1', '2', '3']:
        print(f"\n👤 推导玩家{player_id}:")
        
        if player_id in known_initial:
            print(f"  ✅ 已知初始手牌: {known_initial[player_id]}")
            deduced_hands[player_id] = known_initial[player_id]
            continue
        
        # 获取最终状态
        final_data = final_hands.get(player_id, {})
        final_hand = final_data.get('hand', [])
        melds = final_data.get('melds', [])
        
        # 获取操作记录
        ops = player_operations[player_id]
        
        print(f"  📊 数据统计:")
        print(f"    最终手牌: {final_hand} ({len(final_hand)}张)")
        print(f"    摸牌: {len(ops['draws'])}次 - {ops['draws']}")
        print(f"    弃牌: {len(ops['discards'])}次 - {ops['discards']}")
        print(f"    碰牌: {len(ops['pengs'])}次 - {ops['pengs']}")
        print(f"    杠牌: {len(ops['gangs'])}次 - {ops['gangs']}")
        
        # 计算消耗的手牌
        meld_consumption = []
        for meld in melds:
            meld_type = meld['type']
            tiles = meld['tile']
            
            if meld_type == 'peng':
                # 碰牌消耗手牌中的2张
                meld_consumption.extend([tiles[0]] * 2)
            elif meld_type == 'gang':
                # 明杠消耗手牌中的3张
                meld_consumption.extend([tiles[0]] * 3)
            elif meld_type == 'jiagang':
                # 加杠消耗手牌中的1张
                meld_consumption.extend([tiles[0]] * 1)
        
        print(f"    碰杠消耗手牌: {meld_consumption}")
        
        # 推导初始手牌
        initial_counter = Counter()
        
        # 加上最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # 加上弃牌
        for tile in ops['discards']:
            initial_counter[tile] += 1
        
        # 加上碰杠消耗
        for tile in meld_consumption:
            initial_counter[tile] += 1
        
        # 减去摸牌
        for tile in ops['draws']:
            initial_counter[tile] -= 1
        
        # 处理负数情况
        deduced_initial = []
        issues = []
        
        for tile, count in initial_counter.items():
            if count > 0:
                deduced_initial.extend([tile] * count)
            elif count < 0:
                issues.append(f"牌 '{tile}' 计算为负数 {count}")
        
        deduced_initial.sort()
        
        print(f"  🎯 推导结果:")
        print(f"    推导初始手牌: {deduced_initial} ({len(deduced_initial)}张)")
        
        if issues:
            print(f"  ⚠️  问题: {issues}")
        
        if len(deduced_initial) != 13:
            print(f"  ❌ 警告: 推导手牌数量不是13张!")
        
        deduced_hands[player_id] = deduced_initial
    
    return deduced_hands

def create_complete_game_data(original_file: str, output_file: str):
    """创建完整的游戏数据文件"""
    
    with open(original_file, 'r', encoding='utf-8') as f:
        game_data = json.load(f)
    
    # 推导初始手牌
    deduced_hands = deduce_initial_hands(game_data)
    
    # 更新游戏数据
    if 'first_hand' not in game_data:
        game_data['first_hand'] = {}
    
    for player_id, hand in deduced_hands.items():
        game_data['first_hand'][player_id] = hand
    
    # 保存完整数据
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(game_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完整游戏数据已保存到: {output_file}")
    
    return game_data

if __name__ == "__main__":
    # 分析原始数据
    game_data = analyze_mahjong_game('game_data_template_gang_fixed.json')
    
    # 推导初始手牌
    deduced_hands = deduce_initial_hands(game_data)
    
    # 创建完整数据文件
    complete_data = create_complete_game_data(
        'game_data_template_gang_fixed.json', 
        'game_data_template_gang_all.json'
    )
    
    print("\n" + "=" * 60)
    print("📈 推导总结:")
    for player_id, hand in deduced_hands.items():
        status = "✅ 已知" if player_id == '0' else "🔍 推导"
        print(f"  玩家{player_id}: {status} - {hand} ({len(hand)}张)")