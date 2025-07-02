#!/usr/bin/env python3
"""
调试胜利状态设置问题
"""
import json
import requests

# 读取牌谱数据
with open('model/first_hand/sample_mahjong_game_final.json', 'r', encoding='utf-8') as f:
    replay_data = json.load(f)

final_hands = replay_data.get('final_hands', {})

print("🔍 牌谱中的胜利状态数据:")
for player_id, hand_data in final_hands.items():
    print(f"玩家{player_id}:")
    if 'self_win_tile' in hand_data:
        print(f"  自摸胡牌: {hand_data['self_win_tile']}")
    elif 'pao_tile' in hand_data:
        print(f"  点炮胡牌: {hand_data['pao_tile']}")
    else:
        print(f"  无胜利状态")
    print()

# 重置游戏
print("🔄 重置游戏...")
response = requests.post("http://localhost:8000/api/mahjong/reset")
print(f"重置结果: {response.json().get('success', False)}")

# 手动设置玩家0的胜利状态
print("\n🏆 手动设置玩家0胜利状态...")
params = {
    "player_id": 0,
    "win_type": "zimo",
    "win_tile_type": "tiao",
    "win_tile_value": 3
}

response = requests.post("http://localhost:8000/api/mahjong/player-win", params=params)
result = response.json()
print(f"设置结果: {result.get('success', False)}")
print(f"消息: {result.get('message', '无')}")

# 检查设置后的状态
print("\n🔍 检查设置后的胜利状态:")
response = requests.get("http://localhost:8000/api/mahjong/game-state")
game_state = response.json().get('game_state', {})
hand0 = game_state['player_hands']['0']
print(f"玩家0: is_winner={hand0.get('is_winner', '不存在')}")
print(f"玩家0: win_type={hand0.get('win_type', '不存在')}")  
print(f"玩家0: win_tile={hand0.get('win_tile', '不存在')}")

# 再次检查完整的游戏状态数据结构
print("\n📊 完整的玩家0数据:")
print(json.dumps(hand0, indent=2, ensure_ascii=False))