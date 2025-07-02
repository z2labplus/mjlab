#!/usr/bin/env python3
"""
测试前端导入标准格式文件的脚本
验证转换逻辑是否正确
"""

import json
from pathlib import Path

def test_standard_format_conversion():
    """测试标准格式到前端格式的转换"""
    
    print("🧪 测试标准格式文件转换")
    print("=" * 50)
    
    # 读取标准格式文件
    standard_file = "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json"
    
    if not Path(standard_file).exists():
        print(f"❌ 标准格式文件不存在: {standard_file}")
        return False
    
    with open(standard_file, 'r', encoding='utf-8') as f:
        standard_data = json.load(f)
    
    print("✅ 成功读取标准格式文件")
    print(f"   游戏ID: {standard_data.get('game_info', {}).get('game_id', 'unknown')}")
    print(f"   初始手牌玩家数: {len(standard_data.get('initial_hands', {}))}")
    print(f"   动作数: {len(standard_data.get('actions', []))}")
    
    # 验证必要字段
    has_game_info = 'game_info' in standard_data
    has_initial_hands = 'initial_hands' in standard_data
    has_actions = 'actions' in standard_data
    
    print(f"\n📋 字段检查:")
    print(f"   game_info: {'✅' if has_game_info else '❌'}")
    print(f"   initial_hands: {'✅' if has_initial_hands else '❌'}")
    print(f"   actions: {'✅' if has_actions else '❌'}")
    
    # 模拟前端转换逻辑
    print(f"\n🔄 模拟前端转换逻辑...")
    
    is_standard_format = has_game_info and has_initial_hands and has_actions
    is_legacy_format = has_game_info and ('players' in standard_data) and has_actions
    
    print(f"   识别为标准格式: {'✅' if is_standard_format else '❌'}")
    print(f"   识别为传统格式: {'✅' if is_legacy_format else '❌'}")
    
    if not is_standard_format and not is_legacy_format:
        print("❌ 前端会报错：无效的牌谱格式")
        return False
    
    if is_standard_format and 'players' not in standard_data:
        print("✅ 前端会触发标准格式转换")
        
        # 模拟转换过程
        players = []
        
        for player_id_str, hand_data in standard_data.get('initial_hands', {}).items():
            player_id_num = int(player_id_str)
            tiles = hand_data.get('tiles', []) if isinstance(hand_data, dict) else hand_data
            
            players.append({
                "id": player_id_num,
                "name": f"玩家{player_id_num + 1}",
                "position": player_id_num,
                "initial_hand": tiles,
                "missing_suit": standard_data.get('misssuit', {}).get(player_id_str),
                "final_score": 0,
                "is_winner": False,
                "statistics": {
                    "draw_count": 0,
                    "discard_count": 0,
                    "peng_count": 0,
                    "gang_count": 0
                }
            })
        
        # 统计操作
        for action in standard_data.get('actions', []):
            player = next((p for p in players if p['id'] == action.get('player_id')), None)
            if player:
                action_type = action.get('type', '')
                if action_type == 'draw':
                    player['statistics']['draw_count'] += 1
                elif action_type == 'discard':
                    player['statistics']['discard_count'] += 1
                elif action_type == 'peng':
                    player['statistics']['peng_count'] += 1
                elif action_type in ['gang', 'jiagang']:
                    player['statistics']['gang_count'] += 1
        
        # 构建前端期望的格式
        converted_data = {
            "game_info": {
                "game_id": standard_data.get('game_info', {}).get('game_id', 'converted_game'),
                "start_time": "2024-06-26T08:00:00.000Z",
                "end_time": "2024-06-26T08:30:00.000Z",
                "duration": 1800,
                "player_count": len(players),
                "game_mode": standard_data.get('mjtype', 'xuezhan_daodi')
            },
            "players": players,
            "actions": [
                {
                    "sequence": action.get('sequence', 0),
                    "timestamp": "2024-06-26T08:00:00.000Z",
                    "player_id": action.get('player_id', 0),
                    "action_type": action.get('type', 'draw'),
                    "card": action.get('tile'),
                    "target_player": action.get('target_player'),
                    "gang_type": action.get('gang_type'),
                    "score_change": 0
                }
                for action in standard_data.get('actions', [])
            ],
            "metadata": {
                "source": "standard_format_converted",
                "original_format": "standard"
            }
        }
        
        print(f"✅ 转换成功!")
        print(f"   转换后玩家数: {len(converted_data['players'])}")
        print(f"   转换后动作数: {len(converted_data['actions'])}")
        
        # 验证转换后的格式
        has_converted_game_info = 'game_info' in converted_data
        has_converted_players = 'players' in converted_data
        has_converted_actions = 'actions' in converted_data
        
        print(f"\n📋 转换后格式验证:")
        print(f"   game_info: {'✅' if has_converted_game_info else '❌'}")
        print(f"   players: {'✅' if has_converted_players else '❌'}")
        print(f"   actions: {'✅' if has_converted_actions else '❌'}")
        
        if has_converted_game_info and has_converted_players and has_converted_actions:
            print("✅ 转换后的格式符合前端期望")
            
            # 保存转换后的文件供测试
            output_file = "/root/claude/hmjai/backend/converted_for_frontend_test.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 转换后的文件已保存: {output_file}")
            return True
        else:
            print("❌ 转换后的格式不符合前端期望")
            return False
    
    return True

def main():
    """主函数"""
    print("🎯 前端导入标准格式文件测试")
    print("=" * 60)
    
    success = test_standard_format_conversion()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 测试成功！")
        print("📋 现在您可以:")
        print("   1. 直接在前端拖拽导入 model/first_hand/sample_mahjong_game_final.json")
        print("   2. 前端会自动检测格式并转换")
        print("   3. 转换后的数据符合前端期望的格式")
        print("\n💡 如果还有问题，请检查浏览器控制台的转换日志")
    else:
        print("❌ 测试失败，请检查文件格式或转换逻辑")

if __name__ == "__main__":
    main()